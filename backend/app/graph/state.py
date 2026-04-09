from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    messages: list[str]
    ui_messages: list[dict[str, Any]]
    client_state: dict[str, Any]
    session_id: str
    turns_used: int
    top_k: int
    profile: dict[str, Any]
    missing: list[str]
    router_intent: str
    questions: list[dict[str, Any]]
    rewritten_query: str
    retrieved: dict[str, Any]
    recommendations: list[dict[str, Any]]
    assistant_message: str
    next_step: str
    meta: dict[str, Any]
    chat_history: list[dict[str, Any]]
    last_user_message: str
    last_assistant_message: str
    response: Any
