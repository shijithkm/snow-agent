from services.grafana_mock import silence_alert
import os
import requests
import logging
from typing import Optional
from urllib.parse import urlparse
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage


from dotenv import load_dotenv
# Load environment variables from a .env file when present
load_dotenv()

logger = logging.getLogger("backend.graph.nodes")


client = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant"
)



def classify_intent(state):
    system = {
    "role": "system",
    "content": (
        "You are an intent-classification agent for a ServiceNow automation workflow. "
        "Your task is to output exactly one label based on the ticket description. "
        "Output 'silence_alert' if the user is requesting alert suppression in any form "
        "(silence, mute, suppress, disable, stop, acknowledge, or similar). "
        "Output 'assign_l1' for all other requests. "
        "Rules: "
        "1. Output ONLY one of these two labels: silence_alert or assign_l1. "
        "2. Do NOT include explanations, punctuation, or additional text. "
        "3. Do NOT modify or rephrase the labels."
    )
}
    human = {"role": "user", "content": state.description}

    try:
        resp = client.invoke([system, human])
        intent = resp.content.lower()

        logger.info("ChatGroq classification for ticket %s: intent=%s", getattr(state, "ticket_id", "?"), intent)   

        if "silence" in intent:
            state.intent = "silence_alert"
        else:
            state.intent = "assign_l1"

    except Exception as e:
        logger.error("ChatGroq classification failed; using heuristic", exc_info=True)
        desc = state.description.lower()
        state.intent = "silence_alert" if "silence" in desc else "assign_l1"

    return state

def _heuristic_assign(state):
    # Minimal heuristic used as a safe fallback
    desc = (state.description or "").lower()
    if (state.ticket_type and ("suppress" in state.ticket_type.lower() or "silence" in state.ticket_type.lower())) or "silence" in desc or getattr(state, "alert_id", None):
        state.assigned_to = "Snow Agent"
        state.intent = "silence_alert"
    else:
        state.assigned_to = "L1 Team"
        state.intent = "assign_l1"
    logger.info("Heuristic assignment for ticket %s: %s", getattr(state, "ticket_id", "?"), state.assigned_to)
    return state

def handle_grafana(state):
    # Use provided suppression window if available
    start = getattr(state, "start_time", None)
    end = getattr(state, "end_time", None)
    logger.info("Handling grafana for ticket %s: alert=%s start=%s end=%s", getattr(state, "ticket_id", "?"), state.alert_id, start, end)
    result = silence_alert(state.alert_id, start, end)
    # Snow Agent handles suppression: mark assigned and schedule closure
    state.assigned_to = "Snow Agent"
    # Do not close immediately; main will schedule closure after a delay
    state.closed = False
    state.result = f"Grafana alert {state.alert_id} silenced by Snow Agent: {result}"
    logger.info("Grafana handled for ticket %s: result=%s", getattr(state, "ticket_id", "?"), result)
    return state

def assign_l1(state):
    state.assigned_to = "L1 Team"
    state.result = "Ticket assigned to L1 support"
    return state