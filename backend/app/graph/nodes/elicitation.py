from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.graph.prompts import ELICITATION_SYSTEM_PROMPT, ELICITATION_USER_PROMPT_TEMPLATE
from app.graph.state import AgentState
from app.models import ElicitationQuestion, NextStep, RecommendResponse
from app.services.rag.memory import EnhancedConversationMemory
from app.services.llm.client import llm_client
from app.utils import trace_step


_LOGGER = logging.getLogger(__name__)


class ElicitationAgent:
    def run(self, state: AgentState) -> RecommendResponse:
        messages = list(state.get("messages") or [])
        turns_used = int(state.get("turns_used") or 0)
        profile = dict(state.get("profile") or {})

        memory = EnhancedConversationMemory(max_messages=10)
        for m in messages:
            memory.add_message(role="user", content=str(m))
        last_message = messages[-1] if messages else ""
        history_text = memory.get_context(max_turns=10)

        assistant_message = ""
        questions: list[ElicitationQuestion] = []
        if settings.api_key:
            try:
                user_prompt = ELICITATION_USER_PROMPT_TEMPLATE.format(
                    history_text=history_text,
                    last_message=last_message,
                    profile_json=json.dumps(profile, ensure_ascii=False),
                    turns_used=str(turns_used),
                )
                parsed = llm_client.chat_completion_json(
                    system_prompt=ELICITATION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    model=settings.elicitation_model,
                )
                assistant_message = str(parsed.get("assistant_message") or "").strip()
                questions_raw = parsed.get("questions") or []
                if isinstance(questions_raw, list):
                    for q in questions_raw[:2]:
                        if not isinstance(q, dict):
                            continue
                        q_id = str(q.get("id") or "").strip()
                        q_text = str(q.get("question") or "").strip()
                        if not q_text:
                            continue
                        q_choices = q.get("choices")
                        if isinstance(q_choices, list):
                            choices = [str(c).strip() for c in q_choices if str(c).strip()]
                        else:
                            choices = None
                        try:
                            questions.append(
                                ElicitationQuestion(id=q_id or "q", question=q_text, choices=choices or None)
                            )
                        except Exception:
                            pass
            except Exception as e:
                _LOGGER.info("elicitation_llm_failed: %s", str(e))

        if not questions:
            missing = list(state.get("missing") or [])
            if "budget_vnd" in missing:
                questions.append(
                    ElicitationQuestion(
                        id="budget_vnd",
                        question="Ngân sách dự kiến của bạn khoảng bao nhiêu (VNĐ / triệu / tỷ)?",
                        choices=None,
                    )
                )
            if "seats" in missing:
                questions.append(
                    ElicitationQuestion(
                        id="seats",
                        question="Bạn cần xe mấy chỗ (4/5/7)?",
                        choices=["4", "5", "7"],
                    )
                )
            if not questions:
                questions = [
                    ElicitationQuestion(
                        id="use_case",
                        question="Bạn dự định dùng xe chủ yếu để làm gì (đi phố, đi xa, gia đình, dịch vụ)?",
                        choices=["Đi phố", "Đi xa", "Gia đình", "Dịch vụ"],
                    ),
                ]
        if not assistant_message:
            parts = ["Mình cần thêm 1-2 thông tin để tư vấn sát hơn:"]
            for i, q in enumerate(questions[:2], start=1):
                parts.append(f"{i}) {q.question}")
            parts.append("Bạn cũng có thể bấm 'Gặp tư vấn viên' bất kỳ lúc nào.")
            assistant_message = "\n".join(parts)

        client_state = dict(state.get("client_state") or {})
        client_state["session_id"] = str(state.get("session_id") or client_state.get("session_id") or "")
        client_state["turns_used"] = turns_used + 1
        client_state["last_questions"] = [q.model_dump() for q in questions]
        client_state["profile"] = dict(profile)

        return RecommendResponse(
            next_step=NextStep.ask,
            assistant_message=assistant_message,
            questions=questions,
            recommendations=[],
            state=client_state,
            handoff_to_human=True,
            meta=dict(state.get("meta") or {}),
        )


_AGENT = ElicitationAgent()


def elicitation_node(state: AgentState) -> AgentState:
    resp = _AGENT.run(state)
    meta = dict(resp.meta or {})
    trace_step(
        meta,
        step="elicitation",
        data={
            "missing": list(state.get("missing") or []),
            "question_ids": [q.id for q in resp.questions],
        },
    )
    resp.meta = meta
    return {"response": resp}
