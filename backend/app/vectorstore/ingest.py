from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from typing import Iterable

from app.core.config import settings
from app.utils import data_dir, normalize_text
from app.services.rag.vector_store import QdrantConfig, QdrantVectorStore, qdrant_store
from app.vectorstore.store import Document, VectorStore


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    out: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _hash_id(value: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, value).hex


def _read_vinfast_youtube_csv(path: Path) -> list[Document]:
    if not path.exists():
        return []
    docs: list[Document] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return []
        for row_idx, row in enumerate(reader, start=1):
            if not row:
                continue
            model = (row[0] if len(row) > 0 else "").strip()
            title = (row[1] if len(row) > 1 else "").strip()
            video_id = (row[2] if len(row) > 2 else "").strip()
            transcript = (row[3] if len(row) > 3 else "").strip()
            if not transcript:
                continue

            base = normalize_text(" | ".join([t for t in [f"Model: {model}", f"Title: {title}"] if t.strip()]))
            doc_id = f"youtube:{video_id or _hash_id(f'{row_idx}:{title}:{model}')}"
            text = normalize_text("\n".join([base, transcript]))
            docs.append(
                Document(
                    id=doc_id,
                    text=text,
                    source="youtube",
                    metadata={
                        "kind": "transcript",
                        "model": model,
                        "video_id": video_id,
                        "video_title": title,
                        "row_index": row_idx,
                    },
                )
            )
    return docs


def _read_vinfast_agent_clean_csv(path: Path) -> list[Document]:
    if not path.exists():
        return []
    docs: list[Document] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=1):
            url = str(row.get("url") or "").strip()
            text_raw = str(row.get("text") or "").strip()
            if not text_raw:
                continue
            group = str(row.get("group") or "").strip()
            time = str(row.get("time") or "").strip()
            reason = str(row.get("reason") or "").strip()
            category = str(row.get("category") or "").strip()
            car_model = str(row.get("car_model") or "").strip()

            prefix_bits = [b for b in [f"Model: {car_model}", f"Category: {category}"] if b.strip()]
            prefix = normalize_text(" | ".join(prefix_bits))
            stable = url or f"row:{row_idx}:{car_model}:{category}"
            doc_id = f"facebook:{_hash_id(stable)}"
            text = normalize_text("\n".join([prefix, text_raw])) if prefix else normalize_text(text_raw)
            docs.append(
                Document(
                    id=doc_id,
                    text=text,
                    source="facebook",
                    metadata={
                        "kind": "post",
                        "url": url,
                        "group": group,
                        "time": time,
                        "reason": reason,
                        "category": category,
                        "model": car_model,
                        "row_index": row_idx,
                    },
                )
            )
    return docs


def build_corpus_documents(base_dir: Path | None = None) -> list[Document]:
    base = base_dir or data_dir()
    cars_path = base / "cars.json"
    cars = json.loads(cars_path.read_text(encoding="utf-8")) if cars_path.exists() else []

    docs: list[Document] = []
    for car in cars:
        model = str(car["model"])
        text = normalize_text(
            " | ".join(
                [
                    model,
                    f"Body: {car.get('body_type','')}",
                    f"Seats: {car.get('seats','')}",
                    f"Range_km: {car.get('range_km','')}",
                    f"Price_min_vnd: {car.get('price_min_vnd','')}",
                    f"Price_max_vnd: {car.get('price_max_vnd','')}",
                    str(car.get("highlights", "")),
                ]
            )
        )
        docs.append(
            Document(
                id=f"spec:{model}",
                text=text,
                source="specs",
                metadata={"model": model, "kind": "spec"},
            )
        )

    for item in _read_jsonl(base / "reviews_youtube.jsonl"):
        meta_obj = item.get("metadata", {})
        meta: dict[str, object] = meta_obj if isinstance(meta_obj, dict) else {}
        docs.append(
            Document(
                id=str(item["id"]),
                text=normalize_text(str(item["text"])),
                source="youtube",
                metadata=meta,
            )
        )
    for item in _read_jsonl(base / "reviews_facebook.jsonl"):
        meta_obj = item.get("metadata", {})
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        docs.append(
            Document(
                id=str(item["id"]),
                text=normalize_text(str(item["text"])),
                source="facebook",
                metadata=meta,
            )
        )
    docs.extend(_read_vinfast_youtube_csv(base / "vinfast_data.csv"))
    docs.extend(_read_vinfast_agent_clean_csv(base / "vinfast_agent_clean.csv"))
    for item in _read_jsonl(base / "realtime_prices.jsonl"):
        meta_obj = item.get("metadata", {})
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        docs.append(
            Document(
                id=str(item["id"]),
                text=normalize_text(str(item["text"])),
                source="web",
                metadata=meta,
            )
        )
    return docs


def build_vectorstore(docs: Iterable[Document]) -> VectorStore:
    store = VectorStore()
    store.add_documents(docs)
    return store


def default_index_path() -> Path:
    return data_dir() / "vector_index.json"


def ingest_to_disk(index_path: Path | None = None) -> Path:
    docs = build_corpus_documents()
    store = build_vectorstore(docs)
    out_path = index_path or default_index_path()
    store.save(out_path)
    return out_path


def ingest_to_qdrant() -> str:
    docs = build_corpus_documents()
    if not qdrant_store.is_available():
        raise RuntimeError("Qdrant is not available. Set QDRANT_URL and start Qdrant.")
    qdrant_store.upsert_documents(docs)
    return str(qdrant_store.collection_name)


def ingest_vinfast_csvs_to_qdrant(
    *,
    youtube_collection: str | None = None,
    facebook_collection: str | None = None,
    base_dir: Path | None = None,
) -> tuple[str, str]:
    base = base_dir or data_dir()
    youtube_docs = _read_vinfast_youtube_csv(base / "vinfast_data.csv")
    facebook_docs = _read_vinfast_agent_clean_csv(base / "vinfast_agent_clean.csv")

    if not qdrant_store.is_available():
        raise RuntimeError("Qdrant is not available. Set QDRANT_URL and start Qdrant.")

    yt_collection = youtube_collection or f"{qdrant_store.collection_name}_youtube"
    fb_collection = facebook_collection or f"{qdrant_store.collection_name}_facebook"

    yt_store = QdrantVectorStore(
        QdrantConfig(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection=yt_collection,
            timeout_s=max(0.2, float(settings.qdrant_timeout_s)),
        )
    )
    fb_store = QdrantVectorStore(
        QdrantConfig(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection=fb_collection,
            timeout_s=max(0.2, float(settings.qdrant_timeout_s)),
        )
    )

    yt_store.delete_collection()
    fb_store.delete_collection()

    yt_store.upsert_documents(youtube_docs)
    fb_store.upsert_documents(facebook_docs)

    return (yt_store.collection_name, fb_store.collection_name)
