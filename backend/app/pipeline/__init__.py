from __future__ import annotations

from typing import Any, Optional

from app.graph.workflow import recommender_graph
from app.models import RecommendResponse
from app.utils import debug_print, extract_user_texts, last_user_text, new_session_id


class RecommenderPipeline:
    def _coerce_ui_messages(self, raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        out: list[dict[str, Any]] = []
        for m in raw:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "")
            if role not in {"user", "assistant"}:
                continue
            text = self._extract_text_from_ui_message(m)
            if not text:
                continue
            out.append({"role": role, "content": text})
        return out

    def _dedupe_consecutive(self, ui_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        prev_role: Optional[str] = None
        prev_text: Optional[str] = None
        for m in ui_messages:
            role = str(m.get("role") or "")
            if role not in {"user", "assistant"}:
                continue
            text = self._extract_text_from_ui_message(m)
            if not text:
                continue
            if prev_role == role and prev_text == text:
                continue
            out.append({"role": role, "content": text})
            prev_role = role
            prev_text = text
        return out

    def _merge_history(self, *, incoming: list[dict[str, Any]], prior: Any, max_messages: int = 40) -> list[dict[str, Any]]:
        incoming_norm = self._coerce_ui_messages(incoming)
        if len(incoming_norm) > 1:
            return self._dedupe_consecutive(incoming_norm)[-int(max_messages) :]
        prior_norm = self._coerce_ui_messages(prior)
        merged = prior_norm + incoming_norm
        return self._dedupe_consecutive(merged)[-int(max_messages) :]

    def _extract_text_from_ui_message(self, msg: dict[str, Any]) -> str:
        parts = msg.get("parts")
        if isinstance(parts, list):
            out: list[str] = []
            for p in parts:
                if not isinstance(p, dict):
                    continue
                if p.get("type") == "text":
                    out.append(str(p.get("text") or ""))
            joined = "".join(out).strip()
            if joined:
                return joined
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        return ""

    def run(
        self,
        messages: list[str],
        state: dict[str, Any],
        top_k: int = 3,
        ui_messages: Optional[list[dict[str, Any]]] = None,
    ) -> RecommendResponse:
        session_id = str(state.get("session_id") or new_session_id())
        turns_used = int(state.get("turns_used") or 0)
        print("run")
        debug_print("DEBUG_PIPELINE", "pipeline.run", {"session_id": session_id, "turns_used": turns_used, "top_k": top_k, "messages": messages})
        initial_state: dict[str, Any] = {
            "messages": messages,
            "ui_messages": list(ui_messages or []),
            "client_state": dict(state),
            "session_id": session_id,
            "turns_used": turns_used,
            "top_k": top_k,
        }
        final_state = recommender_graph.invoke(initial_state)
        resp = final_state.get("response")
        print(resp)
        debug_print("DEBUG_PIPELINE", "pipeline.run.response", {"type": type(resp).__name__})
        if isinstance(resp, RecommendResponse):
            return resp
        raise RuntimeError("LangGraph did not produce RecommendResponse")

    def chat(
        self,
        *,
        ui_messages: list[dict[str, Any]],
        session_id: Optional[str] = None,
        state: Optional[dict[str, Any]] = None,
        top_k: int = 3,
    ) -> RecommendResponse:
        merged_state: dict[str, Any] = dict(state or {})
        sid = str(session_id or merged_state.get("session_id") or new_session_id())
        merged_state["session_id"] = sid

        full_ui_messages = self._merge_history(incoming=ui_messages, prior=merged_state.get("chat_history"))
        assistant_turns = 0
        for m in full_ui_messages:
            if not isinstance(m, dict):
                continue
            if m.get("role") == "assistant":
                assistant_turns += 1
        user_texts = extract_user_texts(full_ui_messages)
        if not user_texts:
            raise ValueError("messages is required")

        turns_used = merged_state.get("turns_used")
        if turns_used is None:
            turns_used = assistant_turns
        merged_state["turns_used"] = int(turns_used)
        debug_print(
            "DEBUG_PIPELINE",
            "pipeline.chat",
            {
                "ui_messages_len": len(full_ui_messages),
                "assistant_turns": assistant_turns,
                "user_texts_len": len(user_texts),
                "turns_used": merged_state["turns_used"],
                "session_id": merged_state["session_id"],
            },
        )
        resp = self.run(messages=user_texts, state=merged_state, top_k=top_k, ui_messages=full_ui_messages)
        new_state = dict(resp.state or {})
        chat_history = self._dedupe_consecutive(full_ui_messages)
        assistant_text = str(resp.assistant_message or "").strip()
        if assistant_text:
            if not chat_history or chat_history[-1].get("role") != "assistant" or chat_history[-1].get("content") != assistant_text:
                chat_history = chat_history + [{"role": "assistant", "content": assistant_text}]
        new_state["chat_history"] = chat_history
        new_state["last_user_message"] = last_user_text(chat_history)
        new_state["last_assistant_message"] = assistant_text
        resp.state = new_state
        return resp


__all__ = ["RecommenderPipeline"]
