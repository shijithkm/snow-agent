from langgraph.graph import StateGraph, END
from .state import OpsState
from .nodes import classify_intent, grafana_agent, l1_agent
from .rag_node import rag_agent
from .info_node import info_agent
from .rfi_l1_fallback import rfi_l1_fallback

def build_graph():
    graph = StateGraph(OpsState)

    graph.add_node("classify", classify_intent)
    graph.add_node("grafana", grafana_agent)
    graph.add_node("assign_l1", l1_agent)
    graph.add_node("info", info_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("rfi_l1_fallback", rfi_l1_fallback)

    graph.set_entry_point("classify")

    # Route based on intent and service_type
    def route_after_classify(state):
        # RITM with suppress_alerts service goes to Grafana
        if state.intent == "ritm" and state.service_type == "suppress_alerts":
            return "grafana"
        # Other RITM and RFI go to info agent
        elif state.intent in ["ritm", "rfi"]:
            return "info"
        elif state.intent == "incident":
            return "assign_l1"
        elif state.intent == "silence_alert":
            return "grafana"
        else:
            return "assign_l1"
    
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "grafana": "grafana",
            "info": "info",
            "assign_l1": "assign_l1"
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

    # RAG agent decision: if found answer, end; otherwise assign to L1
    graph.add_conditional_edges(
        "rag",
        lambda s: "end" if s.rag_found else "rfi_l1_fallback",
        {
            "end": END,
            "rfi_l1_fallback": "rfi_l1_fallback"
        }
    )

    graph.add_edge("grafana", END)
    graph.add_edge("assign_l1", END)
    graph.add_edge("rfi_l1_fallback", END)

    return graph.compile()