from __future__ import annotations

from app.vectorstore.ingest import build_corpus_documents, build_vectorstore


def test_search_returns_results() -> None:
    docs = build_corpus_documents()
    store = build_vectorstore(docs)
    results = store.search("xe gia đình 7 chỗ đi xa", top_k=3)
    assert results
    top_doc, top_score = results[0]
    assert isinstance(top_doc.text, str)
    assert 0.0 <= top_score <= 1.0
