import logging

tickets = {}

logger = logging.getLogger("backend.services.servicenow")


def create_ticket(description, alert_id=None, ticket_type=None, start_time=None, end_time=None):
    ticket_id = f"TKT-{len(tickets)+1}"
    tickets[ticket_id] = {
        "id": ticket_id,
        "description": description,
        "alert_id": alert_id,
        "ticket_type": ticket_type,
        "start_time": start_time,
        "end_time": end_time,
        "status": "open",
        "work_comments": None
    }
    logger.info("Created ticket %s: type=%s alert=%s start=%s end=%s", ticket_id, ticket_type, alert_id, start_time, end_time)
    return ticket_id