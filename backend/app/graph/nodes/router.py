from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal, Optional, cast

from app.core.config import settings
from app.graph.prompts import (
    PROFILE_SYSTEM_PROMPT,
    PROFILE_USER_PROMPT_TEMPLATE,
    ROUTER_SYSTEM_PROMPT,
    ROUTER_USER_PROMPT_TEMPLATE,
)
from app.graph.state import AgentState
from app.services.rag.memory import EnhancedConversationMemory
from app.services.llm.client import llm_client
from app.utils import parse_budget_vnd, parse_seats, safe_int, trace_step


_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RouterDecision:
    intent: Literal["off_topic", "elicitation", "retrieval"]
    confidence: float
    reason: str


class RouterAgent:
    def update_profile(self, state: AgentState) -> dict[str, Any]:
        profile = dict(state.get("profile") or {})
        messages = list(state.get("messages") or [])
        if not settings.api_key:
            merged = " ".join([str(m) for m in messages if str(m).strip()]).strip()
            if merged:
                if profile.get("budget_vnd") is None:
                    budget_vnd = parse_budget_vnd(merged)
                    if budget_vnd is not None:
                        profile["budget_vnd"] = budget_vnd
                if profile.get("seats") is None:
                    seats = parse_seats(merged)
                    if seats is not None:
                        profile["seats"] = seats
            return profile

        memory = EnhancedConversationMemory(max_messages=10)
        for m in messages:
            memory.add_message(role="user", content=str(m))
        last_message = messages[-1] if messages else ""
        history_text = memory.get_context(max_turns=10)

        try:
            user_prompt = PROFILE_USER_PROMPT_TEMPLATE.format(
                history_text=history_text,
                last_message=last_message,
                profile_json=json.dumps(profile, ensure_ascii=False),
            )
            parsed = llm_client.chat_completion_json(
                system_prompt=PROFILE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=settings.router_model,
            )
            budget_vnd = safe_int(parsed.get("budget_vnd"))
            seats = safe_int(parsed.get("seats"))
            if budget_vnd is not None:
                profile["budget_vnd"] = budget_vnd
            if seats is not None:
                profile["seats"] = seats
        except Exception as e:
            _LOGGER.info("profile_llm_failed: %s", str(e))
        # Fallback enrichment with regex even when LLM available but returns nulls
        merged = " ".join([str(m) for m in messages if str(m).strip()]).strip()
        if merged:
            if profile.get("budget_vnd") is None:
                budget_vnd = parse_budget_vnd(merged)
                if budget_vnd is not None:
                    profile["budget_vnd"] = budget_vnd
            if profile.get("seats") is None:
                seats = parse_seats(merged)
                if seats is not None:
                    profile["seats"] = seats
        return profile

    def decide(self, *, messages: list[str], profile: dict[str, Any], turns_used: int) -> RouterDecision:
        llm = self._decide_with_llm(messages=messages, profile=profile, turns_used=turns_used)
        if llm is not None:
            return llm
        missing = missing_fields(profile)
        if missing and turns_used < 3:
            return RouterDecision(intent="elicitation", confidence=0.0, reason="llm_unavailable_or_failed")
        return RouterDecision(intent="retrieval", confidence=0.0, reason="llm_unavailable_or_failed")

    def _decide_with_llm(
        self, *, messages: list[str], profile: dict[str, Any], turns_used: int
    ) -> Optional[RouterDecision]:
        if settings.router_mode != "llm":
            return None

        last_message = messages[-1] if messages else ""
        memory = EnhancedConversationMemory(max_messages=10)
        for m in messages:
            memory.add_message(role="user", content=str(m))
        history_text = memory.get_context(max_turns=10)
        user_prompt = ROUTER_USER_PROMPT_TEMPLATE.format(
            history_text=history_text,
            last_message=last_message,
            profile_json=json.dumps(profile, ensure_ascii=False),
            turns_used=str(turns_used),
        )
        try:
            parsed = llm_client.chat_completion_json(
                system_prompt=ROUTER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=settings.router_model,
            )
            print("parsed", parsed)
            intent = str(parsed.get("intent", "")).strip()
            confidence = float(parsed.get("confidence", 0.0))
            reason = str(parsed.get("reason", "")).strip()
            if intent not in {"off_topic", "elicitation", "retrieval"}:
                return None
            confidence = max(0.0, min(confidence, 1.0))
            return RouterDecision(
                intent=cast(Literal["off_topic", "elicitation", "retrieval"], intent),
                confidence=confidence,
                reason=reason,
            )
        except Exception as e:
            _LOGGER.info("router_llm_failed: %s", str(e))
            return None


_AGENT = RouterAgent()

def missing_fields(profile: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if profile.get("budget_vnd") is None:
        missing.append("budget_vnd")
    if profile.get("seats") is None:
        missing.append("seats")
    return missing


def route_next(state: AgentState) -> Literal["off_topic", "elicitation", "retrieval"]:
    intent = state.get("router_intent")
    if intent in {"off_topic", "elicitation", "retrieval"}:
        return cast(Literal["off_topic", "elicitation", "retrieval"], intent)
    return "retrieval"


def router_node(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    turns_used = int(state.get("turns_used") or 0)
    profile_dict = _AGENT.update_profile(state)
    state["profile"] = profile_dict
    decision = _AGENT.decide(messages=messages, profile=profile_dict, turns_used=turns_used)
    missing = missing_fields(profile_dict)

    meta = dict(state.get("meta") or {})
    meta.update(
        {
            "router": "langgraph",
            "router_intent": decision.intent,
            "router_confidence": decision.confidence,
            "router_reason": decision.reason,
        }
    )
    trace_step(
        meta,
        step="router",
        data={
            "turns_used": turns_used,
            "intent": decision.intent,
            "missing": list(missing),
            "profile": {"budget_vnd": profile_dict.get("budget_vnd"), "seats": profile_dict.get("seats")},
        },
    )
    return {"profile": profile_dict, "router_intent": decision.intent, "missing": missing, "meta": meta}
