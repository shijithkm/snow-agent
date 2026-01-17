from langgraph.graph import StateGraph, END
from .state import SNOWState
from .nodes import classify_intent, handle_grafana, assign_l1

def build_graph():
    graph = StateGraph(SNOWState)

    graph.add_node("classify", classify_intent)
    graph.add_node("grafana", handle_grafana)
    graph.add_node("assign_l1", assign_l1)

    graph.set_entry_point("classify")

    graph.add_conditional_edges(
        "classify",
        lambda s: s.intent,
        {
            "silence_alert": "grafana",
            "assign_l1": "assign_l1"
        }
    )

    graph.add_edge("grafana", END)
    graph.add_edge("assign_l1", END)

    return graph.compile()