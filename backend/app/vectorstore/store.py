from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    source: str
    metadata: dict[str, object]


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^0-9A-Za-zÀ-ỹ]+", text.lower()) if t]


class HashingEmbedder:
    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokenize(text):
            h = 2166136261
            for c in tok.encode("utf-8"):
                h ^= c
                h = (h * 16777619) % 2**32
            idx = int(h % self.dim)
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


def _cosine(a: list[float], b: list[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


class VectorStore:
    def __init__(self, embedder: Optional[HashingEmbedder] = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self._docs: list[Document] = []
        self._vectors: list[list[float]] = []

    @property
    def size(self) -> int:
        return len(self._docs)

    def add_documents(self, docs: Iterable[Document]) -> None:
        for d in docs:
            self._docs.append(d)
            self._vectors.append(self.embedder.embed(d.text))

    def search(self, query: str, top_k: int = 5, source: Optional[str] = None) -> list[tuple[Document, float]]:
        qv = self.embedder.embed(query)
        scored: list[tuple[int, float]] = []
        for i, (doc, dv) in enumerate(zip(self._docs, self._vectors)):
            if source is not None and doc.source != source:
                continue
            scored.append((i, _cosine(qv, dv)))
        scored.sort(key=lambda x: x[1], reverse=True)
        out: list[tuple[Document, float]] = []
        for i, s in scored[:top_k]:
            out.append((self._docs[i], s))
        return out

    def save(self, path: Path) -> None:
        payload = {
            "dim": self.embedder.dim,
            "docs": [asdict(d) for d in self._docs],
            "vectors": self._vectors,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "VectorStore":
        payload = json.loads(path.read_text(encoding="utf-8"))
        store = cls(embedder=HashingEmbedder(dim=int(payload["dim"])))
        store._docs = [Document(**d) for d in payload["docs"]]
        store._vectors = payload["vectors"]
        return store
