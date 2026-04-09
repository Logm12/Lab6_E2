from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.graph.prompts import REWRITE_SYSTEM_PROMPT, REWRITE_USER_PROMPT_TEMPLATE
from app.graph.state import AgentState
from app.retrieval.sources import default_retrieval_client
from app.services.rag.memory import EnhancedConversationMemory
from app.services.llm.client import llm_client
from app.utils import normalize_text, trace_step


_LOGGER = logging.getLogger(__name__)


def rewrite_node(state: AgentState) -> AgentState:
    messages = list(state.get("messages") or [])
    memory = EnhancedConversationMemory(max_messages=10)
    for m in messages:
        memory.add_message(role="user", content=str(m))
    last_message = messages[-1] if messages else ""
    history = memory.get_context(max_turns=10)
    original_query = normalize_text("\n".join([t for t in [history, last_message] if t]))
    profile = dict(state.get("profile") or {})

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
    memory = EnhancedConversationMemory(max_messages=10)
    for m in messages:
        memory.add_message(role="user", content=str(m))
    last_message = messages[-1] if messages else ""
    history = memory.get_context(max_turns=10)
    query = str(state.get("rewritten_query") or "").strip() or normalize_text("\n".join([t for t in [history, last_message] if t]))
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
