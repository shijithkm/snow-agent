from langgraph.graph import StateGraph, END
from .state import SNOWState
from .nodes import classify_intent, grafana_agent, l1_agent, rfi_agent
from .rag_node import rag_agent
from .info_node import info_agent

def build_graph():
    graph = StateGraph(SNOWState)

    graph.add_node("classify", classify_intent)
    graph.add_node("grafana", grafana_agent)
    graph.add_node("assign_l1", l1_agent)
    graph.add_node("info", info_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("rfi", rfi_agent)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        lambda s: s.intent,
        {
            "silence_alert": "grafana",
            "assign_l1": "assign_l1",
            "rfi": "info"  # RFI requests go to Info Agent first (Confluence)
        }
    )

    # Info agent decision: if found answer, end; otherwise go to RAG
    graph.add_conditional_edges(
        "info",
        lambda s: "end" if s.info_found else "rag",
        {
            "end": END,
            "rag": "rag"
        }
    )

    # RAG agent decision: if found answer, end; otherwise go to RFI
    graph.add_conditional_edges(
        "rag",
        lambda s: "end" if s.rag_found else "rfi",
        {
            "end": END,
            "rfi": "rfi"
        }
    )

    graph.add_edge("grafana", END)
    graph.add_edge("assign_l1", END)
    graph.add_edge("rfi", END)

    return graph.compile()