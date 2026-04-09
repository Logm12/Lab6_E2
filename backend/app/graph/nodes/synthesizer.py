from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.graph.prompts import SYNTHESIZER_SYSTEM_PROMPT, SYNTHESIZER_USER_PROMPT_TEMPLATE
from app.graph.state import AgentState
from app.models import CarRecommendation, NextStep, RecommendResponse, UserProfile
from app.recommender.engine import RecommenderEngine, to_recommendation
from app.services.rag.memory import EnhancedConversationMemory
from app.services.llm.client import llm_client
from app.utils import build_history_context, debug_print, last_user_text, trace_step


_ENGINE = RecommenderEngine()
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SynthesizerOutput:
    assistant_message: str
    recommendations: list[dict[str, Any]]


class SynthesizerAgent:
    def rank(self, *, profile: UserProfile, retrieved: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
        ranked = _ENGINE.rank(profile, retrieved)
        recs = [to_recommendation(car, score, profile) for car, score in ranked[:top_k]]
        return [r.model_dump() for r in recs]

    def render(
        self,
        *,
        profile: dict[str, Any],
        recommendations: list[dict[str, Any]],
        history_text: str,
        last_message: str,
    ) -> str:
        if settings.synthesizer_mode == "llm" and settings.api_key:
            try:
                user_prompt = SYNTHESIZER_USER_PROMPT_TEMPLATE.format(
                    history_text=history_text,
                    last_message=last_message,
                    profile_json=json.dumps(profile, ensure_ascii=False),
                    recommendations_json=json.dumps(recommendations, ensure_ascii=False),
                )
                msg = llm_client.chat_completion(
                    system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=settings.synthesizer_model,
                    temperature=0.2,
                ).strip()
                if msg:
                    return msg
            except Exception as e:
                _LOGGER.info("synthesizer_llm_failed: %s", str(e))

        rec_objs = [CarRecommendation(**r) for r in recommendations]
        return _ENGINE.render_recommendations_message(rec_objs)

    def run(
        self,
        *,
        profile_dict: dict[str, Any],
        retrieved: dict[str, Any],
        top_k: int,
        history_text: str,
        last_message: str,
    ) -> SynthesizerOutput:
        profile = UserProfile(
            budget_vnd=profile_dict.get("budget_vnd"),
            seats=profile_dict.get("seats"),
        )
        recommendations = self.rank(profile=profile, retrieved=retrieved, top_k=top_k)
        assistant_message = self.render(
            profile=profile_dict,
            recommendations=recommendations,
            history_text=history_text,
            last_message=last_message,
        )
        return SynthesizerOutput(assistant_message=assistant_message, recommendations=recommendations)


_AGENT = SynthesizerAgent()


def synthesizer_node(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    ui_messages = state.get("ui_messages")
    if isinstance(ui_messages, list) and ui_messages:
        history_text = build_history_context(ui_messages, max_messages=10, max_turns=10)
        last_message = last_user_text(ui_messages) or (messages[-1] if messages else "")
    else:
        memory = EnhancedConversationMemory(max_messages=10)
        for m in messages:
            memory.add_message(role="user", content=str(m))
        last_message = messages[-1] if messages else ""
        history_text = memory.get_context(max_turns=10)

    profile_dict = dict(state.get("profile") or {})
    retrieved = dict(state.get("retrieved") or {})
    top_k = int(state.get("top_k") or 3)

    out = _AGENT.run(
        profile_dict=profile_dict,
        retrieved=retrieved,
        top_k=top_k,
        history_text=history_text,
        last_message=last_message,
    )
    debug_print("DEBUG_PIPELINE", "synthesizer.output", {"recs": len(out.recommendations), "top_k": top_k})
    print("synthesizer_node")

    client_state = dict(state.get("client_state") or {})
    client_state["session_id"] = str(state.get("session_id") or client_state.get("session_id") or "")
    client_state["turns_used"] = int(client_state.get("turns_used") or state.get("turns_used") or 0)
    client_state["profile"] = dict(profile_dict)
    client_state["last_recommendations"] = list(out.recommendations)

    recommendations = [CarRecommendation(**r) for r in out.recommendations]
    resp = RecommendResponse(
        next_step=NextStep.recommend,
        assistant_message=out.assistant_message,
        questions=[],
        recommendations=recommendations,
        state=client_state,
        handoff_to_human=True,
        meta=dict(state.get("meta") or {}),
    )
    meta = dict(resp.meta or {})
    trace_step(
        meta,
        step="synthesizer",
        data={"models": [r.model for r in recommendations], "top_k": top_k},
    )
    resp.meta = meta
    return {"response": resp}
