from fastapi import FastAPI
import threading
from datetime import datetime
import logging

# Configure basic logging for the backend
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("backend")
from graph.workflow import build_graph
from services.servicenow_mock import create_ticket, tickets
from services.grafana_mock import alerts
from models.ticket import TicketRequest

app = FastAPI()
graph = build_graph()

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
        if assigned:
            tickets[ticket_id]["assigned_to"] = assigned
            logger.info("Ticket %s assigned_to=%s", ticket_id, assigned)

        # If graph flagged closed True, treat it as immediate closure (rare).
        if closed:
            tickets[ticket_id]["status"] = "closed"
            logger.info("Ticket %s closed immediately by graph", ticket_id)

        # If assigned to Snow Agent for suppression, schedule delayed closure
        if assigned == "Snow Agent":
            # mark as in-progress now
            tickets[ticket_id]["status"] = "in_progress"
            logger.info("Ticket %s marked in_progress; scheduling closure in 60s", ticket_id)

            def close_later(tid: str, delay: int = 60):
                def _fn():
                    try:
                        tickets[tid]["status"] = "closed"
                        tickets[tid]["closed_at"] = datetime.utcnow().isoformat()
                        logger.info("Ticket %s auto-closed after delay", tid)
                    except Exception:
                        logger.exception("Failed to auto-close ticket %s", tid)
                t = threading.Timer(delay, _fn)
                t.daemon = True
                t.start()

            # schedule closure after 60 seconds
            close_later(ticket_id, 60)

    return result