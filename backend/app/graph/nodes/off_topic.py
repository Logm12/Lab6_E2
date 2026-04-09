from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.config import settings
from app.graph.prompts import OFF_TOPIC_SYSTEM_PROMPT, OFF_TOPIC_USER_PROMPT_TEMPLATE
from app.graph.state import AgentState
from app.models import NextStep, RecommendResponse
from app.services.llm.client import llm_client
from app.utils import trace_step


_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class OffTopicOutput:
    assistant_message: str


class OffTopicAgent:
    def respond(self, *, user_message: str) -> OffTopicOutput:
        if settings.off_topic_mode == "llm" and settings.api_key:
            try:
                user_prompt = OFF_TOPIC_USER_PROMPT_TEMPLATE.format(user_message=user_message)
                msg = llm_client.chat_completion(
                    system_prompt=OFF_TOPIC_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=settings.off_topic_model,
                    temperature=0.2,
                ).strip()
                if msg:
                    return OffTopicOutput(assistant_message=msg)
            except Exception as e:
                _LOGGER.info("off_topic_llm_failed: %s", str(e))
        return OffTopicOutput(
            assistant_message="Mình đang hỗ trợ tư vấn chọn xe VinFast. Bạn cho mình biết ngân sách và cần mấy chỗ ngồi nhé."
        )


_AGENT = OffTopicAgent()


def off_topic_node(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    user_message = messages[-1] if messages else ""
    out = _AGENT.respond(user_message=user_message)

    client_state = dict(state.get("client_state") or {})
    client_state["session_id"] = str(state.get("session_id") or client_state.get("session_id") or "")
    client_state["turns_used"] = int(client_state.get("turns_used") or state.get("turns_used") or 0)

    meta = dict(state.get("meta") or {})
    meta["intent"] = "off_topic"

    resp = RecommendResponse(
        next_step=NextStep.ask,
        assistant_message=out.assistant_message,
        questions=[],
        recommendations=[],
        state=client_state,
        handoff_to_human=True,
        meta=meta,
    )
    meta2 = dict(resp.meta or {})
    trace_step(meta2, step="off_topic", data={"last_message": user_message})
    resp.meta = meta2
    return {"response": resp}
