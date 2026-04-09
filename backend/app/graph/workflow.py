from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    elicitation_node,
    off_topic_node,
    rewrite_node,
    retrieval_node,
    route_next,
    router_node,
    synthesizer_node,
)
from app.graph.state import AgentState


def create_graph() -> Any:
    workflow: Any = StateGraph(AgentState)
    workflow.add_node("router", router_node)
    workflow.add_node("off_topic", off_topic_node)
    workflow.add_node("elicitation", elicitation_node)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("router")
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "off_topic": "off_topic",
            "elicitation": "elicitation",
            "retrieval": "rewrite",
        },
    )
    workflow.add_edge("off_topic", END)
    workflow.add_edge("elicitation", END)
    workflow.add_edge("rewrite", "retrieval")
    workflow.add_edge("retrieval", "synthesizer")
    workflow.add_edge("synthesizer", END)
    return workflow.compile()


recommender_graph = create_graph()
