from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from datetime import datetime
import logging
from typing import Dict, Any, Optional, List

# Configure basic logging for the backend
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("backend")

from graph.workflow import build_graph
from graph.chatbot_workflow import get_chatbot_graph
from graph.chatbot_state import ChatbotState, ChatMessage
from graph.chatbot_nodes import (
    extract_info,
    check_required_fields,
    ask_for_missing_fields,
    create_ticket_from_chat,
    parse_user_response
)
from services.servicenow_mock import create_ticket, tickets
from services.grafana_mock import alerts
from services.rag_service import rag_service
from models.ticket import TicketRequest

app = FastAPI(title="Ops AI Agent", version="1.0.0")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# Store chat sessions (in-memory for now)
chat_sessions: Dict[str, ChatbotState] = {}


# Pydantic models for validation
class ChatRequest(BaseModel):
    session_id: str
    message: str = ""
    action: str = "continue"
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['start', 'continue', 'reset']:
            raise ValueError('action must be start, continue, or reset')
        return v


class ChatResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]
    ticket_created: bool
    ticket_id: Optional[str] = None


# Helper functions
def _update_ticket_from_result(ticket_id: str, result: dict) -> None:
    """Centralized ticket update logic."""
    if not isinstance(result, dict):
        return
    
    if assigned := result.get("assigned_to"):
        tickets[ticket_id]["assigned_to"] = assigned
        logger.info("Ticket %s assigned to %s", ticket_id, assigned)
    
    if work_comments := result.get("work_comments"):
        tickets[ticket_id]["work_comments"] = work_comments
        logger.info("Ticket %s work_comments added", ticket_id)
    
    # Close ticket if flagged by workflow or if RFI complete
    if result.get("closed") or assigned == "RFI Agent":
        tickets[ticket_id]["status"] = "closed"
        logger.info("Ticket %s closed", ticket_id)


def _invoke_agent_workflow(state: ChatbotState) -> None:
    """Helper to invoke main workflow and update ticket."""
    if not (state.ticket_created and state.ticket_id):
        return
    
    logger.info("Invoking agent workflow for ticket %s (intent=%s)", 
                state.ticket_id, state.intent)
    try:
        # Determine service_type for RITM tickets
        service_type = None
        if state.intent == "ritm":
            desc_lower = state.description.lower() if state.description else ""
            if any(keyword in desc_lower for keyword in ["suppress", "silence", "mute", "stop alert", "disable alert"]):
                service_type = "suppress_alerts"
        
        graph_result = graph.invoke({
            "ticket_id": state.ticket_id,
            "description": state.description,
            "alert_id": state.alert_id,
            "ticket_type": state.intent,
            "start_time": state.start_time,
            "end_time": state.end_time,
            "service_type": service_type,
            "application": state.application,
        })
        logger.info("Agent workflow completed for %s: %s", 
                   state.ticket_id, graph_result)
        
        _update_ticket_from_result(state.ticket_id, graph_result)
        
        # For RFI and RITM (non-suppress) tickets, show the answer to user and ask for confirmation
        # For RITM suppress_alerts, the Grafana agent handles it directly
        if state.intent in ["rfi", "ritm"]:
            # Skip answer confirmation for RITM suppress_alerts (Grafana handles it)
            if state.intent == "ritm" and service_type == "suppress_alerts":
                logger.info("RITM suppress_alerts handled by Grafana agent, skipping confirmation")
                return
            
            work_comments = graph_result.get("work_comments", "")
            assigned_to = graph_result.get("assigned_to", "")
            
            # Skip confirmation if ticket was assigned to L1 Team (no answer found)
            if assigned_to == "L1 Team":
                logger.info("Ticket %s assigned to L1 Team, skipping confirmation", state.ticket_id)
                if state.messages and "Ticket" in state.messages[-1].content and "created successfully" in state.messages[-1].content:
                    state.messages.pop()
                # Add L1 assignment message without confirmation prompt
                state.messages.append(ChatMessage(role="assistant", content=work_comments))
                state.needs_user_input = False
                state.awaiting_confirmation = False
                return
            
            if work_comments:
                # Remove the last ticket creation message
                if state.messages and "Ticket" in state.messages[-1].content and "created successfully" in state.messages[-1].content:
                    state.messages.pop()
                
                # Add the answer as assistant message with confirmation prompt
                answer_message = f"{work_comments}\n\n❓ **Did this answer your question?** (Reply 'yes' to close the ticket or 'no' if you need more information)"
                state.messages.append(ChatMessage(role="assistant", content=answer_message))
                state.needs_user_input = True
                state.awaiting_confirmation = True
                
    except Exception as e:
        logger.error("Agent workflow failed for ticket %s: %s", 
                    state.ticket_id, str(e), exc_info=True)


def _handle_missing_fields(state: ChatbotState) -> ChatbotState:
    """Process state when fields are missing."""
    state = parse_user_response(state)
    state = check_required_fields(state)
    
    if state.missing_fields:
        state = ask_for_missing_fields(state)
    else:
        state = create_ticket_from_chat(state)
        _invoke_agent_workflow(state)
    
    return state


def _handle_new_message(state: ChatbotState) -> ChatbotState:
    """Process new user message."""
    state = extract_info(state)
    state = check_required_fields(state)
    
    if state.missing_fields:
        state = ask_for_missing_fields(state)
    else:
        state = create_ticket_from_chat(state)
        _invoke_agent_workflow(state)
    
    return state


def _create_chat_response(state: ChatbotState) -> Dict[str, Any]:
    """Create standardized chat response."""
    return {
        "session_id": state.session_id if hasattr(state, 'session_id') else "default",
        "messages": [{"role": m.role, "content": m.content} for m in state.messages],
        "ticket_created": state.ticket_created,
        "ticket_id": state.ticket_id
    }


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(chat_sessions),
        "total_tickets": len(tickets)
    }


@app.get("/alerts")
async def get_alerts():
    """Get all Grafana alerts."""
    return alerts


@app.get("/tickets")
async def get_tickets():
    """Get all ServiceNow tickets."""
    return tickets


@app.post("/process_ticket")
async def process_ticket(req: TicketRequest):
    """Process a ticket through the agent workflow."""
    try:
        logger.info("Processing ticket request: ticket_type=%s alert_id=%s", 
                   req.ticket_type, req.alert_id)
        
        ticket_id = create_ticket(
            req.description, 
            req.alert_id, 
            req.ticket_type, 
            req.start_time, 
            req.end_time,
            service_type=req.service_type,
            application=req.application,
            source=req.source if req.source else "form"
        )
        logger.info("Created ticket %s", ticket_id)
        
        result = graph.invoke({
            "ticket_id": ticket_id,
            "description": req.description,
            "alert_id": req.alert_id,
            "ticket_type": req.ticket_type,
            "start_time": req.start_time,
            "end_time": req.end_time,
            "service_type": req.service_type,
            "application": req.application,
        })
        logger.info("Graph result for %s: %s", ticket_id, result)
        
        # Update ticket with workflow results
        _update_ticket_from_result(ticket_id, result)
        
        return result
    except ValueError as e:
        logger.error("Invalid ticket data: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Ticket processing failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    """Handle chatbot conversation with improved structure."""
    try:
        logger.info("Chat request: session=%s action=%s message=%s", 
                   payload.session_id, payload.action, payload.message)
        
        # Handle session initialization
        if payload.action == "start" or payload.session_id not in chat_sessions:
            chat_sessions[payload.session_id] = ChatbotState()
            chatbot = get_chatbot_graph()
            result_dict = chatbot.invoke(chat_sessions[payload.session_id].dict())
            result = ChatbotState(**result_dict)
            chat_sessions[payload.session_id] = result
            return _create_chat_response(result)
        
        # Handle session reset
        if payload.action == "reset":
            chat_sessions[payload.session_id] = ChatbotState()
            chatbot = get_chatbot_graph()
            result_dict = chatbot.invoke(chat_sessions[payload.session_id].dict())
            result = ChatbotState(**result_dict)
            chat_sessions[payload.session_id] = result
            return _create_chat_response(result)
        
        # Continue conversation
        state = chat_sessions[payload.session_id]
        
        # Add user message
        if payload.message:
            state.messages.append(ChatMessage(role="user", content=payload.message))
        
        # Check if last assistant message was "Is there anything else I can help you with?"
        # and user replied no - just acknowledge and don't create new ticket
        if (len(state.messages) >= 2 and 
            not state.awaiting_confirmation and 
            not state.ticket_created and
            "anything else" in state.messages[-2].content.lower() and
            payload.message and
            payload.message.lower().strip() in ["no", "nope", "no thanks", "no thank you", "nothing", "that's all"]):
            
            state.messages.append(ChatMessage(
                role="assistant",
                content="👍 Alright! Feel free to reach out if you need anything in the future. Have a great day!"
            ))
            state.needs_user_input = False
            chat_sessions[payload.session_id] = state
            return _create_chat_response(state)
        
        # Check if awaiting confirmation for RFI ticket
        if state.awaiting_confirmation and payload.message:
            response_lower = payload.message.lower().strip()
            if any(word in response_lower for word in ["yes", "yeah", "yep", "correct", "thanks", "thank you", "perfect"]):
                # User is satisfied, close the ticket
                if state.ticket_id and state.ticket_id in tickets:
                    tickets[state.ticket_id]["status"] = "closed"
                    logger.info("Ticket %s closed after user confirmation", state.ticket_id)
                
                state.messages.append(ChatMessage(
                    role="assistant", 
                    content=f"✅ Great! I'm glad I could help. Ticket {state.ticket_id} has been closed. Is there anything else I can assist you with?"
                ))
                state.awaiting_confirmation = False
                state.ticket_created = False
                state.ticket_id = None
                chat_sessions[payload.session_id] = state
                return _create_chat_response(state)
                
            elif any(word in response_lower for word in ["no", "nope", "not really", "need more", "more info"]):
                # User needs more information, assign to L1
                if state.ticket_id and state.ticket_id in tickets:
                    tickets[state.ticket_id]["assigned_to"] = "L1 Team"
                    tickets[state.ticket_id]["status"] = "open"
                    tickets[state.ticket_id]["work_comments"] += "\n\n**User requested additional information**\nTicket escalated to L1 Team for further assistance."
                    logger.info("Ticket %s assigned to L1 Team after user requested more info", state.ticket_id)
                
                state.messages.append(ChatMessage(
                    role="assistant",
                    content=f"📋 I understand. Ticket {state.ticket_id} has been assigned to our L1 Team for additional research. They will provide more detailed information shortly. Is there anything else I can help you with in the meantime?"
                ))
                state.awaiting_confirmation = False
                state.ticket_created = False
                state.ticket_id = None
                chat_sessions[payload.session_id] = state
                return _create_chat_response(state)
            else:
                # User is asking a NEW question instead of confirming - reset state for new request
                logger.info("User asked new question while awaiting confirmation, resetting state")
                # Close the previous ticket first
                if state.ticket_id and state.ticket_id in tickets:
                    tickets[state.ticket_id]["status"] = "closed"
                    logger.info("Auto-closing previous ticket %s", state.ticket_id)
                
                # Reset state for new question but keep conversation history
                state.awaiting_confirmation = False
                state.ticket_created = False
                state.ticket_id = None
                state.description = None
                state.intent = None
                state.alert_id = None
                state.application = None
                state.start_time = None
                state.end_time = None
                state.missing_fields = []
                state.target_agent = None
                state.details_requested = False
                # Continue to process the new question below
        
        # Process based on current state
        if state.missing_fields:
            state = _handle_missing_fields(state)
        else:
            state = _handle_new_message(state)
        
        # Update session
        chat_sessions[payload.session_id] = state
        
        return _create_chat_response(state)
    
    except ValueError as e:
        logger.error("Invalid chat request: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Chat processing failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# RAG Document Management Endpoints
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    uploaded_by: str = Form("admin")
):
    """Upload a document for RAG training."""
    try:
        # Validate file type
        allowed_extensions = [".pdf", ".md", ".txt", ".doc", ".docx"]
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Save document
        metadata = rag_service.save_document(content, file.filename, uploaded_by)
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """Get all uploaded documents."""
    try:
        documents = rag_service.get_all_documents()
        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document metadata."""
    try:
        doc = rag_service.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"success": True, "document": doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/{doc_id}/train")
async def train_document(doc_id: str):
    """Train a document into the vector database."""
    try:
        metadata = rag_service.train_document(doc_id)
        return {
            "success": True,
            "message": "Document trained successfully",
            "document": metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Document training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    try:
        success = rag_service.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/search")
async def search_documents(query: str = Form(...), k: int = Form(3)):
    """Search documents in vector database."""
    try:
        results = rag_service.search(query, k)
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Document search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
