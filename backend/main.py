from fastapi import FastAPI
import threading
from datetime import datetime
import logging
from typing import Dict, Any

# Configure basic logging for the backend
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("backend")
from graph.workflow import build_graph
from graph.chatbot_workflow import get_chatbot_graph
from graph.chatbot_state import ChatbotState, ChatMessage
from services.servicenow_mock import create_ticket, tickets
from services.grafana_mock import alerts
from models.ticket import TicketRequest

app = FastAPI()
graph = build_graph()

# Store chat sessions (in-memory for now)
chat_sessions: Dict[str, ChatbotState] = {}

@app.get("/alerts")
def get_alerts():
    return alerts

@app.get("/tickets")
def get_tickets():
    return tickets

@app.post("/process_ticket")
def process_ticket(req: TicketRequest):
    logger.info("Processing ticket request: ticket_type=%s alert_id=%s", req.ticket_type, req.alert_id)
    ticket_id = create_ticket(req.description, req.alert_id, req.ticket_type, req.start_time, req.end_time)
    logger.info("Created ticket %s", ticket_id)
    result = graph.invoke({
        "ticket_id": ticket_id,
        "description": req.description,
        "alert_id": req.alert_id,
        "ticket_type": req.ticket_type,
        "start_time": req.start_time,
        "end_time": req.end_time,
    })
    logger.info("Graph result for %s: %s", ticket_id, result)
    # Persist assignment back to the ticket store if graph set it
    if isinstance(result, dict):
        assigned = result.get("assigned_to")
        closed = result.get("closed")
        work_comments = result.get("work_comments")
        if assigned:
            tickets[ticket_id]["assigned_to"] = assigned
            logger.info("Ticket %s assigned_to=%s", ticket_id, assigned)
        if work_comments:
            tickets[ticket_id]["work_comments"] = work_comments
            logger.info("Ticket %s work_comments added", ticket_id)

        # If graph flagged closed True, close the ticket immediately
        if closed:
            tickets[ticket_id]["status"] = "closed"
            logger.info("Ticket %s closed immediately by graph", ticket_id)
        
        # If assigned to RFI Agent, mark as closed since research is complete
        elif assigned == "RFI Agent":
            tickets[ticket_id]["status"] = "closed"
            logger.info("Ticket %s marked closed (RFI complete)", ticket_id)

    return result


@app.post("/chat")
def chat(payload: Dict[str, Any]):
    """Handle chatbot conversation."""
    session_id = payload.get("session_id", "default")
    user_message = payload.get("message", "")
    action = payload.get("action", "continue")  # "start", "continue", or "reset"
    
    logger.info("Chat request: session=%s action=%s message=%s", session_id, action, user_message)
    
    # Get or create session
    if action == "start" or session_id not in chat_sessions:
        # Start new session with greeting
        chat_sessions[session_id] = ChatbotState()
        chatbot = get_chatbot_graph()
        result_dict = chatbot.invoke(chat_sessions[session_id].dict())
        result = ChatbotState(**result_dict)
        chat_sessions[session_id] = result
        
        return {
            "session_id": session_id,
            "messages": [{"role": m.role, "content": m.content} for m in result.messages],
            "ticket_created": result.ticket_created,
            "ticket_id": result.ticket_id
        }
    
    if action == "reset":
        # Reset session
        chat_sessions[session_id] = ChatbotState()
        chatbot = get_chatbot_graph()
        result_dict = chatbot.invoke(chat_sessions[session_id].dict())
        result = ChatbotState(**result_dict)
        chat_sessions[session_id] = result
        
        return {
            "session_id": session_id,
            "messages": [{"role": m.role, "content": m.content} for m in result.messages],
            "ticket_created": result.ticket_created,
            "ticket_id": result.ticket_id
        }
    
    # Continue conversation
    state = chat_sessions[session_id]
    
    # Add user message
    if user_message:
        state.messages.append(ChatMessage(role="user", content=user_message))
    
    # Determine which node to invoke based on state
    chatbot = get_chatbot_graph()
    
    # If we have missing fields from a previous ask, parse the user's response
    if state.missing_fields:
        from graph.chatbot_nodes import parse_user_response, check_required_fields, ask_for_missing_fields, create_ticket_from_chat
        
        # Parse the user's response
        state = parse_user_response(state)
        
        # Check if all fields are now present
        state = check_required_fields(state)
        
        if state.missing_fields:
            # Still missing fields, ask again
            state = ask_for_missing_fields(state)
        else:
            # All fields present, create ticket
            state = create_ticket_from_chat(state)
            
            # If ticket was created, invoke the main agent workflow
            if state.ticket_created and state.ticket_id:
                logger.info("Invoking agent workflow for ticket %s (intent=%s)", state.ticket_id, state.intent)
                try:
                    # Invoke the main graph with ticket details
                    graph_result = graph.invoke({
                        "ticket_id": state.ticket_id,
                        "description": state.description,
                        "alert_id": state.alert_id,
                        "ticket_type": state.intent,
                        "start_time": state.start_time,
                        "end_time": state.end_time,
                    })
                    logger.info("Agent workflow completed for %s: %s", state.ticket_id, graph_result)
                    
                    # Update ticket status based on workflow result
                    if isinstance(graph_result, dict):
                        if graph_result.get("work_comments"):
                            tickets[state.ticket_id]["work_comments"] = graph_result["work_comments"]
                            logger.info("Added research results to ticket %s", state.ticket_id)
                        if graph_result.get("closed"):
                            tickets[state.ticket_id]["status"] = "closed"
                            logger.info("Ticket %s closed by workflow", state.ticket_id)
                except Exception as e:
                    logger.error("Agent workflow failed for ticket %s", state.ticket_id, exc_info=True)
    else:
        # First time processing this message, extract info
        from graph.chatbot_nodes import extract_info, check_required_fields, ask_for_missing_fields, create_ticket_from_chat
        
        state = extract_info(state)
        state = check_required_fields(state)
        
        if state.missing_fields:
            state = ask_for_missing_fields(state)
        else:
            state = create_ticket_from_chat(state)
            
            # If ticket was created, invoke the main agent workflow
            if state.ticket_created and state.ticket_id:
                logger.info("Invoking agent workflow for ticket %s (intent=%s)", state.ticket_id, state.intent)
                try:
                    # Invoke the main graph with ticket details
                    graph_result = graph.invoke({
                        "ticket_id": state.ticket_id,
                        "description": state.description,
                        "alert_id": state.alert_id,
                        "ticket_type": state.intent,
                        "start_time": state.start_time,
                        "end_time": state.end_time,
                    })
                    logger.info("Agent workflow completed for %s: %s", state.ticket_id, graph_result)
                    
                    # Update ticket status based on workflow result
                    if isinstance(graph_result, dict):
                        if graph_result.get("work_comments"):
                            tickets[state.ticket_id]["work_comments"] = graph_result["work_comments"]
                            logger.info("Added research results to ticket %s", state.ticket_id)
                        if graph_result.get("closed"):
                            tickets[state.ticket_id]["status"] = "closed"
                            logger.info("Ticket %s closed by workflow", state.ticket_id)
                except Exception as e:
                    logger.error("Agent workflow failed for ticket %s", state.ticket_id, exc_info=True)
    
    # Update session
    chat_sessions[session_id] = state
    
    return {
        "session_id": session_id,
        "messages": [{"role": m.role, "content": m.content} for m in state.messages],
        "ticket_created": state.ticket_created,
        "ticket_id": state.ticket_id
    }