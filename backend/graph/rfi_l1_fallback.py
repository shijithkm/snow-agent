"""
RFI/RITM L1 Fallback Node - Assigns RFI/RITM tickets to L1 team when information not found
"""
import logging
from .state import OpsState

logger = logging.getLogger("backend.graph.rfi_l1_fallback")


def rfi_l1_fallback(state: OpsState) -> OpsState:
    """
    Fallback handler for RFI/RITM tickets when both Info Agent and RAG Agent
    cannot find sufficient information.
    
    Assigns ticket to L1 Team and keeps it OPEN for manual research.
    """
    ticket_id = state.ticket_id
    description = state.description
    ticket_type = state.ticket_type or "RFI"
    
    logger.info(f"{ticket_type.upper()} L1 Fallback for ticket {ticket_id}: No information found, assigning to L1 Team")
    
    state.assigned_to = "L1 Team"
    state.closed = False  # Keep ticket OPEN
    state.result = "Assigned to L1 Team for research"
    state.work_comments = (
        f"**Ticket assigned to L1 Team for research**\\n\\n"
        f"The automated system searched multiple sources but could not find sufficient information "
        f"to answer this request:\\n\\n"
        f"\"{description}\"\\n\\n"
        f"**Sources checked:**\\n"
        f"- Confluence documentation\\n"
        f"- Company knowledge base (RAG)\\n\\n"
        f"**Next steps:**\\n"
        f"The L1 Team will research this request and provide a response. "
        f"You will be notified once the information is available.\\n\\n"
        f"**Status:** OPEN (awaiting L1 Team research)"
    )
    
    logger.info(f"Ticket {ticket_id} assigned to L1 Team, status: OPEN")
    
    return state
