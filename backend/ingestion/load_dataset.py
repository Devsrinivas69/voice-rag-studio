import io
import os
import urllib.request
from typing import Any, Dict, Generator, Optional
import pyarrow.parquet as pq
from backend.app.config import get_settings
from backend.app.monitoring.metrics import logger

LANG_PREFIX_MAP = {
    "kn": "kan",
    "hi": "hin",
    "ta": "tam",
    "te": "tel",
    "ml": "mal",
    "mr": "mar",
    "bn": "ben",
    "gu": "guj",
    "as": "asm",
    "or": "ori",
    "pa": "pan",
    "en": "kan",  # Fallback to kan for English fields
}


class MSMarcoLoader:
    """Safely streams records from ai4bharat/MSMARCO-XI language partitions efficiently."""

    def __init__(
        self,
        dataset_name: Optional[str] = None,
        language: Optional[str] = None,
        split: Optional[str] = None,
        sample_size: Optional[int] = None,
        full_ingest: Optional[bool] = None,
    ):
        settings = get_settings()
        self.dataset_name = dataset_name or settings.DATASET_NAME
        self.language = (language or settings.DATASET_LANGUAGE).lower()
        self.split = split or settings.DATASET_SPLIT
        self.sample_size = sample_size if sample_size is not None else settings.DATASET_SAMPLE_SIZE
        self.full_ingest = full_ingest if full_ingest is not None else settings.FULL_INGEST

        if self.full_ingest:
            logger.warning(
                "WARNING: FULL_INGEST=true is enabled! Ingesting the full partition "
                "may require additional processing time."
            )

    def _get_parquet_url(self) -> str:
        prefix = LANG_PREFIX_MAP.get(self.language, "kan")
        split_suffix = "val" if "val" in self.split.lower() else "train"
        folder = "validation" if "val" in self.split.lower() else "train"
        filename = f"{prefix}{split_suffix}.parquet"
        return f"https://huggingface.co/datasets/{self.dataset_name}/resolve/main/{folder}/{filename}"

    def stream_records(self) -> Generator[Dict[str, Any], None, None]:
        """Streams dataset items matching target language up to sample_size limit."""
        url = self._get_parquet_url()
        logger.info(
            f"Loading dataset partition for '{self.dataset_name}' "
            f"[language={self.language}, split={self.split}, url={url}]"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HHGOA-Voice-RAG/1.0"})
            with urllib.request.urlopen(req) as response:
                content = response.read()

            pf = pq.ParquetFile(io.BytesIO(content))
        except Exception as err:
            logger.error(f"Failed to read parquet file from {url}: {err}")
            raise err

        logger.info(f"Parquet loaded. Total row groups: {pf.num_row_groups}")

        yielded_count = 0

        for rg_idx in range(pf.num_row_groups):
            table = pf.read_row_group(rg_idx)
            records = table.to_pylist()

            for item in records:
                yield item
                yielded_count += 1

                if not self.full_ingest and yielded_count >= self.sample_size:
                    logger.info(
                        f"Reached DATASET_SAMPLE_SIZE limit of {self.sample_size} records."
                    )
                    return
