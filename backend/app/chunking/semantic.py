import math
from typing import Any, Dict, List, Optional
import numpy as np
from backend.app.chunking.base import BaseChunker, create_chunk
from backend.app.chunking.sentence import split_sentences
from backend.app.config import get_settings


def compute_tfidf_vectors(sentences: List[str]) -> List[np.ndarray]:
    """Computes TF-IDF character/word n-gram vectors for fast semantic similarity computation."""
    vocab: Dict[str, int] = {}
    term_doc_freq: Dict[str, int] = {}

    tokenized_sentences = []
    for s in sentences:
        words = s.lower().split()
        unique_words = set(words)
        tokenized_sentences.append(words)
        for w in words:
            vocab.setdefault(w, len(vocab))
        for w in unique_words:
            term_doc_freq[w] = term_doc_freq.get(w, 0) + 1

    num_docs = len(sentences)
    vectors = []

    for words in tokenized_sentences:
        vec = np.zeros(len(vocab), dtype=np.float32)
        if not words:
            vectors.append(vec)
            continue
        # Count term frequencies
        tf: Dict[int, int] = {}
        for w in words:
            idx = vocab[w]
            tf[idx] = tf.get(idx, 0) + 1

        for idx_term, count in tf.items():
            word = list(vocab.keys())[list(vocab.values()).index(idx_term)]
            idf = math.log((1.0 + num_docs) / (1.0 + term_doc_freq.get(word, 1))) + 1.0
            vec[idx_term] = (count / len(words)) * idf

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        vectors.append(vec)

    return vectors


class SemanticChunker(BaseChunker):
    """Detects semantic breakpoints by calculating similarity between adjacent sentences."""

    def __init__(self, breakpoint_threshold: Optional[float] = None):
        super().__init__(strategy_name="semantic")
        settings = get_settings()
        self.breakpoint_threshold = (
            breakpoint_threshold
            if breakpoint_threshold is not None
            else settings.SEMANTIC_BREAKPOINT_THRESHOLD
        )

    def chunk(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        doc_id = document["document_id"]
        language = document.get("language", "en")
        query = document.get("query", "")
        answer = document.get("answer", "")
        passages = document.get("passages", [])

        chunks: List[Dict[str, Any]] = []
        global_pos = 0

        for p in passages:
            p_idx = p.get("passage_index", 0)
            p_text = p.get("text", "")
            is_selected = p.get("is_selected", False)

            sentences = split_sentences(p_text)
            if not sentences:
                continue

            if len(sentences) == 1:
                chunk_payload = create_chunk(
                    document_id=doc_id,
                    text=sentences[0],
                    language=language,
                    strategy=self.strategy_name,
                    position=global_pos,
                    source_query=query,
                    source_answer=answer,
                    passage_index=p_idx,
                    is_selected=is_selected,
                    additional_metadata={"sentence_count": 1, "breakpoint_threshold": self.breakpoint_threshold},
                )
                chunks.append(chunk_payload)
                global_pos += 1
                continue

            # Compute sentence vectors
            vectors = compute_tfidf_vectors(sentences)

            current_group: List[str] = [sentences[0]]
            similarities: List[float] = []

            for i in range(len(sentences) - 1):
                vec1 = vectors[i]
                vec2 = vectors[i + 1]
                sim = float(np.dot(vec1, vec2))
                similarities.append(sim)

                # Breakpoint detected: similarity drops below threshold
                if sim < self.breakpoint_threshold:
                    chunk_text = " ".join(current_group)
                    chunk_payload = create_chunk(
                        document_id=doc_id,
                        text=chunk_text,
                        language=language,
                        strategy=self.strategy_name,
                        position=global_pos,
                        source_query=query,
                        source_answer=answer,
                        passage_index=p_idx,
                        is_selected=is_selected,
                        additional_metadata={
                            "sentence_count": len(current_group),
                            "breakpoint_similarity": round(sim, 4),
                            "breakpoint_threshold": self.breakpoint_threshold,
                        },
                    )
                    chunks.append(chunk_payload)
                    global_pos += 1
                    current_group = [sentences[i + 1]]
                else:
                    current_group.append(sentences[i + 1])

            # Emit final group
            if current_group:
                chunk_text = " ".join(current_group)
                chunk_payload = create_chunk(
                    document_id=doc_id,
                    text=chunk_text,
                    language=language,
                    strategy=self.strategy_name,
                    position=global_pos,
                    source_query=query,
                    source_answer=answer,
                    passage_index=p_idx,
                    is_selected=is_selected,
                    additional_metadata={
                        "sentence_count": len(current_group),
                        "breakpoint_threshold": self.breakpoint_threshold,
                    },
                )
                chunks.append(chunk_payload)
                global_pos += 1

        return chunks
