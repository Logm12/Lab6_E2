from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_health() -> None:
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_recommend_flow() -> None:
    if not settings.api_key:
        pytest.skip("requires API key for LLM-based profile extraction")
    client = TestClient(app)
    r1 = client.post(
        "/recommend",
        json={"messages": [{"role": "user", "content": "Mình muốn mua xe gia đình"}], "state": {}, "top_k": 3},
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["next_step"] in {"ask", "recommend"}
    state = body1["state"]

    r2 = client.post(
        "/recommend",
        json={
            "messages": [
                {"role": "user", "content": "Mình muốn mua xe gia đình"},
                {"role": "assistant", "content": body1["assistant_message"]},
                {"role": "user", "content": "Ngân sách 1.2 tỷ, cần 5 chỗ, hay đi xa"},
            ],
            "state": state,
            "top_k": 3,
        },
    )
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["next_step"] == "recommend"
    assert len(body2["recommendations"]) == 3
