from __future__ import annotations

import pytest

from app.core.config import settings
from app.pipeline import RecommenderPipeline


def test_router_asks_when_missing_info() -> None:
    p = RecommenderPipeline()
    res = p.run(messages=["Em muốn mua xe gia đình"], state={}, top_k=3)
    assert res.next_step.value == "ask"
    assert res.questions


def test_router_recommends_when_enough_info() -> None:
    if not settings.api_key:
        pytest.skip("requires API key for LLM-based profile extraction")
    p = RecommenderPipeline()
    res = p.run(messages=["Ngân sách 1.2 tỷ, gia đình 5 người, hay đi xa"], state={}, top_k=3)
    assert res.next_step.value == "recommend"
    assert len(res.recommendations) == 3
    assert all(0.0 <= r.match_score <= 1.0 for r in res.recommendations)


def test_turn_cap_forces_recommend() -> None:
    p = RecommenderPipeline()
    res = p.run(messages=["Em muốn mua xe"], state={"turns_used": 3}, top_k=3)
    assert res.next_step.value == "recommend"


def test_off_topic_routes_to_response() -> None:
    p = RecommenderPipeline()
    res = p.run(messages=["Giải bài toán tích phân giúp mình"], state={}, top_k=3)
    assert res.next_step.value == "ask"
    assert res.assistant_message
