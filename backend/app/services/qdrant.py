import os
import uuid
from typing import Any, Dict, List, Optional
import numpy as np
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    from qdrant_client.http.models import Distance, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class QdrantService:
    """Manages Qdrant vector database connection, payload indexing, batch vector upserts, and search."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        settings = get_settings()
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.mock_mode = settings.MOCK_EXTERNAL_APIS
        self.client: Optional[Any] = None
        self._in_memory_store: Dict[str, List[Dict[str, Any]]] = {}

        self._initialize_client()

    def _initialize_client(self):
        if not QDRANT_AVAILABLE:
            logger.warning("qdrant-client not installed. Operating in fallback mock mode.")
            return

        try:
            logger.info(f"Connecting to Qdrant at {self.url}...")
            if self.api_key:
                client = QdrantClient(url=self.url, api_key=self.api_key, timeout=2)
            else:
                client = QdrantClient(url=self.url, timeout=2)

            # Test connection
            client.get_collections()
            self.client = client
        except Exception as err:
            logger.warning(
                f"Could not connect to Qdrant server at {self.url}: {err}. "
                f"Operating in in-memory vector store mode."
            )
            self.client = None

    def health_check(self) -> bool:
        """Returns True if Qdrant connection is healthy or running in fallback mode."""
        if self.mock_mode or self.client is None:
            return True
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Creates collection and configures vector parameters if it does not already exist."""
        if self.client is None:
            self._in_memory_store.setdefault(collection_name, [])
            return True

        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' with vector size {vector_size}...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                self.create_payload_indexes(collection_name)
            return True
        except Exception as err:
            logger.error(f"Failed to create Qdrant collection '{collection_name}': {err}")
            # Fallback to in-memory store
            self._in_memory_store.setdefault(collection_name, [])
            return True

    def create_payload_indexes(self, collection_name: str) -> None:
        """Creates payload field indexes for language, strategy, document_id, and chunk_id."""
        if self.client is None:
            return

        payload_fields = [
            ("document_id", qmodels.PayloadSchemaType.KEYWORD),
            ("language", qmodels.PayloadSchemaType.KEYWORD),
            ("strategy", qmodels.PayloadSchemaType.KEYWORD),
            ("chunk_id", qmodels.PayloadSchemaType.KEYWORD),
        ]

        for field_name, field_type in payload_fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception as err:
                logger.debug(f"Payload index creation note for '{field_name}': {err}")

    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Upserts a list of point dicts (id, vector, payload) to Qdrant."""
        if not points:
            return True

        if self.client is None:
            store = self._in_memory_store.setdefault(collection_name, [])
            store.extend(points)
            return True

        try:
            qdrant_points = []
            for p in points:
                raw_id = p.get("id") or p["payload"].get("chunk_id") or str(uuid.uuid4())
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
                qdrant_points.append(
                    qmodels.PointStruct(
                        id=point_id,
                        vector=p["vector"],
                        payload=p["payload"],
                    )
                )

            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points,
            )
            return True
        except Exception as err:
            logger.error(f"Failed to upsert points to Qdrant collection '{collection_name}': {err}")
            # Fallback to in-memory store
            store = self._in_memory_store.setdefault(collection_name, [])
            store.extend(points)
            return True

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 20,
        language_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Searches Qdrant for dense vector nearest neighbors with optional language payload filter."""
        if self.client is None:
            # Search in-memory store using cosine similarity
            store = self._in_memory_store.get(collection_name, [])
            results = []
            query_arr = np.array(query_vector, dtype=np.float32)
            query_norm = np.linalg.norm(query_arr) + 1e-9

            for item in store:
                if language_filter and item["payload"].get("language") != language_filter:
                    continue
                v_arr = np.array(item["vector"], dtype=np.float32)
                v_norm = np.linalg.norm(v_arr) + 1e-9
                sim = float(np.dot(query_arr, v_arr) / (query_norm * v_norm))
                results.append({"payload": item["payload"], "score": sim})

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]

        try:
            query_filter = None
            if language_filter:
                query_filter = qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="language",
                            match=qmodels.MatchValue(value=language_filter),
                        )
                    ]
                )

            search_res = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
            )

            return [
                {
                    "id": str(hit.id),
                    "score": float(hit.score),
                    "payload": hit.payload,
                }
                for hit in search_res
            ]
        except Exception as err:
            logger.error(f"Qdrant search error in '{collection_name}': {err}")
            # Fallback to in-memory store search if live client fails during search
            store = self._in_memory_store.get(collection_name, [])
            results = []
            query_arr = np.array(query_vector, dtype=np.float32)
            query_norm = np.linalg.norm(query_arr) + 1e-9
            for item in store:
                if language_filter and item["payload"].get("language") != language_filter:
                    continue
                v_arr = np.array(item["vector"], dtype=np.float32)
                v_norm = np.linalg.norm(v_arr) + 1e-9
                sim = float(np.dot(query_arr, v_arr) / (query_norm * v_norm))
                results.append({"payload": item["payload"], "score": sim})
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
