import logging

tickets = {}

logger = logging.getLogger("backend.services.servicenow")


def create_ticket(description, alert_id=None, ticket_type=None, start_time=None, end_time=None, assigned_to=None):
    ticket_id = f"TKT-{len(tickets)+1}"
    
    # Set status based on ticket type
    if ticket_type == "silence_alert":
        status = "suppressed"
        # Actually suppress the alert in Grafana
        if alert_id:
            from services.grafana_mock import silence_alert
            silence_alert(alert_id, start_time, end_time)
    else:
        status = "open"
    
    tickets[ticket_id] = {
        "id": ticket_id,
        "description": description,
        "alert_id": alert_id,
        "ticket_type": ticket_type,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "assigned_to": assigned_to,
        "work_comments": None
    }
    logger.info("Created ticket %s: type=%s alert=%s start=%s end=%s status=%s assigned_to=%s", ticket_id, ticket_type, alert_id, start_time, end_time, status, assigned_to)
    return ticket_id