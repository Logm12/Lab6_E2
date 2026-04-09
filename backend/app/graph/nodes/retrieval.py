from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.graph.prompts import REWRITE_SYSTEM_PROMPT, REWRITE_USER_PROMPT_TEMPLATE
from app.graph.state import AgentState
from app.retrieval.sources import default_retrieval_client
from app.services.rag.memory import EnhancedConversationMemory
from app.services.llm.client import llm_client
from app.utils import build_history_context, last_user_text, normalize_text, trace_step, user_history_text


_LOGGER = logging.getLogger(__name__)


def rewrite_node(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    ui_messages = state.get("ui_messages")
    if isinstance(ui_messages, list) and ui_messages:
        history = build_history_context(ui_messages, max_messages=10, max_turns=10)
        last_message = last_user_text(ui_messages) or (messages[-1] if messages else "")
    else:
        memory = EnhancedConversationMemory(max_messages=10)
        for m in messages:
            memory.add_message(role="user", content=str(m))
        last_message = messages[-1] if messages else ""
        history = memory.get_context(max_turns=10)
    if isinstance(ui_messages, list) and ui_messages:
        user_hist = user_history_text(ui_messages, max_turns=10)
        original_query = normalize_text("\n".join([t for t in [user_hist, last_message] if t]))
    else:
        original_query = normalize_text("\n".join([t for t in [history, last_message] if t]))
    profile = dict(state.get("profile") or {})

    print("rewrite_node")
    rewritten = ""
    if settings.api_key:
        try:
            user_prompt = REWRITE_USER_PROMPT_TEMPLATE.format(
                history_text=history,
                last_message=last_message,
                profile_json=json.dumps(profile, ensure_ascii=False),
            )
            parsed = llm_client.chat_completion_json(
                system_prompt=REWRITE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=settings.router_model,
                temperature=0.0,
            )
            rewritten = str(parsed.get("query") or "").strip()
        except Exception:
            rewritten = ""

    final_query = normalize_text(rewritten) if rewritten else original_query
    meta = dict(state.get("meta") or {})
    meta.update(
        {
            "rewrite_query_original": original_query,
            "rewrite_query": final_query,
            "rewrite_used_llm": bool(rewritten),
        }
    )
    trace_step(
        meta,
        step="rewrite",
        data={
            "used_llm": bool(rewritten),
            "query": final_query,
        },
    )
    return {"rewritten_query": final_query, "meta": meta}


def retrieval_node(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    ui_messages = state.get("ui_messages")
    if isinstance(ui_messages, list) and ui_messages:
        history = build_history_context(ui_messages, max_messages=10, max_turns=10)
        last_message = last_user_text(ui_messages) or (messages[-1] if messages else "")
    else:
        memory = EnhancedConversationMemory(max_messages=10)
        for m in messages:
            memory.add_message(role="user", content=str(m))
        last_message = messages[-1] if messages else ""
        history = memory.get_context(max_turns=10)
    rewritten_query = str(state.get("rewritten_query") or "").strip()
    if rewritten_query:
        query = rewritten_query
    elif isinstance(ui_messages, list) and ui_messages:
        user_hist = user_history_text(ui_messages, max_turns=10)
        query = normalize_text("\n".join([t for t in [user_hist, last_message] if t]))
    else:
        query = normalize_text("\n".join([t for t in [history, last_message] if t]))
    retrieval = default_retrieval_client()
    retrieved = retrieval.retrieve_fanout(query=query, top_k=6)
    meta = dict(state.get("meta") or {})
    trace_step(
        meta,
        step="retrieval",
        data={"query": query, "sizes": {k: len(v) for k, v in retrieved.items()}},
    )
    return {
        "retrieved": retrieved,
        "meta": {**meta, "retrieval_sizes": {k: len(v) for k, v in retrieved.items()}, "retrieval_query": query},
    }
