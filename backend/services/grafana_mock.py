import logging

logger = logging.getLogger("backend.services.grafana")

alerts = [
    {"id": "1", "name": "Real User Monitoring Alert", "status": "ok"},
    {"id": "2", "name": "API Monitoring Alerts", "status": "ok"},
    {"id": "3", "name": "User Flow Monitoring Alerts", "status": "ok"},
    {"id": "4", "name": "Infrastructure Alerts", "status": "ok"},
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