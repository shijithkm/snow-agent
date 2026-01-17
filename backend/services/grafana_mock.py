import logging

logger = logging.getLogger("backend.services.grafana")

alerts = [
    {"id": "A-1", "name": "CPU High", "status": "firing"},
    {"id": "A-2", "name": "Memory High", "status": "ok"},
    {"id": "A-3", "name": "Disk Full", "status": "firing"},
]


def silence_alert(alert_id, start_time=None, end_time=None):
    logger.info("Silence request for alert %s start=%s end=%s", alert_id, start_time, end_time)
    for a in alerts:
        if a["id"] == alert_id:
            a["status"] = "silenced"
            # record suppression window if provided
            if start_time:
                a["silenced_from"] = str(start_time)
            if end_time:
                a["silenced_until"] = str(end_time)
            logger.info("Alert %s silenced, window from=%s to=%s", alert_id, a.get("silenced_from"), a.get("silenced_until"))
            return {"status": "success", "silenced_from": a.get("silenced_from"), "silenced_until": a.get("silenced_until")}
    logger.warning("Alert %s not found to silence", alert_id)
    return {"status": "not_found"}