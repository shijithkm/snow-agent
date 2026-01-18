from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatbotState(BaseModel):
    # Conversation history
    messages: List[ChatMessage] = []
    
    # Extracted ticket information
    description: Optional[str] = None
    intent: Optional[str] = None  # "silence_alert" or "rfi" or "assign_l1"
    alert_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Missing fields tracking
    missing_fields: List[str] = []
    details_requested: bool = False  # Track if we already asked for more details
    
    # Workflow state
    ticket_created: bool = False
    ticket_id: Optional[str] = None
    needs_user_input: bool = True
    
    # Agent assignment
    target_agent: Optional[str] = None  # "suppress_agent", "l1_agent", "rfi_agent"
