from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.utils import data_dir
from app.services.rag.vector_store import qdrant_store
from app.vectorstore.ingest import default_index_path, ingest_to_disk, ingest_to_qdrant
from app.vectorstore.store import Document, VectorStore


_LOGGER = logging.getLogger(__name__)


class RetrievalClient:
    def __init__(self, index_path: Optional[Path] = None) -> None:
        self.index_path = index_path or default_index_path()
        self._store: Optional[VectorStore] = None
        self._use_qdrant: Optional[bool] = None

    def _ensure_loaded(self) -> VectorStore:
        if self._store is not None:
            return self._store
        if not self.index_path.exists():
            ingest_to_disk(self.index_path)
        self._store = VectorStore.load(self.index_path)
        return self._store

    def _ensure_qdrant_ready(self) -> bool:
        if self._use_qdrant is not None:
            return self._use_qdrant
        if not qdrant_store.is_available():
            self._use_qdrant = False
            return False
        try:
            if qdrant_store.count() == 0:
                ingest_to_qdrant()
            self._use_qdrant = True
            return True
        except Exception:
            self._use_qdrant = False
            return False

    def search_vectordb(
        self, query: str, top_k: int = 5, source: Optional[str] = None
    ) -> list[tuple[Document, float]]:
        if self._ensure_qdrant_ready():
            try:
                return qdrant_store.search(query=query, top_k=top_k, source=source)
            except Exception as e:
                _LOGGER.info("qdrant_search_failed_fallback_to_disk: %s", str(e))
                self._use_qdrant = False
        store = self._ensure_loaded()
        return store.search(query, top_k=top_k, source=source)

    def retrieve_fanout(self, query: str, top_k: int = 5) -> dict[str, list[tuple[Document, float]]]:
        if self._ensure_qdrant_ready():
            try:
                return {
                    "specs": qdrant_store.search(query=query, top_k=top_k, source="specs"),
                    "youtube": qdrant_store.search(query=query, top_k=top_k, source="youtube"),
                    "facebook": qdrant_store.search(query=query, top_k=top_k, source="facebook"),
                    "web": qdrant_store.search(query=query, top_k=top_k, source="web"),
                }
            except Exception as e:
                _LOGGER.info("qdrant_retrieve_fanout_failed_fallback_to_disk: %s", str(e))
                self._use_qdrant = False
        store = self._ensure_loaded()
        return {
            "specs": store.search(query, top_k=top_k, source="specs"),
            "youtube": store.search(query, top_k=top_k, source="youtube"),
            "facebook": store.search(query, top_k=top_k, source="facebook"),
            "web": store.search(query, top_k=top_k, source="web"),
        }


def default_retrieval_client() -> RetrievalClient:
    return RetrievalClient(index_path=data_dir() / "vector_index.json")
