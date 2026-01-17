from langgraph.graph import StateGraph, END
from .chatbot_state import ChatbotState
from .chatbot_nodes import (
    extract_info,
    check_required_fields,
    ask_for_missing_fields,
    parse_user_response,
    create_ticket_from_chat,
    generate_greeting
)


def build_chatbot_graph():
    """Build the chatbot conversation workflow using LangGraph."""
    graph = StateGraph(ChatbotState)
    
    # Add nodes
    graph.add_node("greeting", generate_greeting)
    graph.add_node("extract", extract_info)
    graph.add_node("parse_response", parse_user_response)
    graph.add_node("check_fields", check_required_fields)
    graph.add_node("ask_missing", ask_for_missing_fields)
    graph.add_node("create_ticket", create_ticket_from_chat)
    
    # Set entry point
    graph.set_entry_point("greeting")
    
    # Add edges
    graph.add_edge("greeting", END)
    
    # After extracting info, check fields
    graph.add_edge("extract", "check_fields")
    
    # After parsing user response, check fields again
    graph.add_edge("parse_response", "check_fields")
    
    # Conditional edges based on missing fields
    graph.add_conditional_edges(
        "check_fields",
        lambda s: "has_missing" if s.missing_fields else "complete",
        {
            "has_missing": "ask_missing",
            "complete": "create_ticket"
        }
    )
    
    # After asking for missing fields, end (wait for user input)
    graph.add_edge("ask_missing", END)
    
    # After creating ticket, end
    graph.add_edge("create_ticket", END)
    
    return graph.compile()


# Singleton instance
chatbot_graph = None


def get_chatbot_graph():
    """Get or create the chatbot graph instance."""
    global chatbot_graph
    if chatbot_graph is None:
        chatbot_graph = build_chatbot_graph()
    return chatbot_graph
