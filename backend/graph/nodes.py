from services.grafana_mock import silence_alert
import os
import requests
import logging
from typing import Optional
from urllib.parse import urlparse
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient


from dotenv import load_dotenv
# Load environment variables from a .env file when present
load_dotenv()

logger = logging.getLogger("backend.graph.nodes")


client = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant"
)

# Initialize TavilyClient
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def classify_intent(state):
    # Check if ticket_type explicitly specifies RFI
    if state.ticket_type and state.ticket_type.lower() in ["rfi", "request_for_information"]:
        state.intent = "rfi"
        logger.info("Ticket %s classified as RFI based on ticket_type", getattr(state, "ticket_id", "?"))
        return state
    
    # Check if ticket_type explicitly specifies silence_alert
    if state.ticket_type and "silence" in state.ticket_type.lower():
        state.intent = "silence_alert"
        logger.info("Ticket %s classified as silence_alert based on ticket_type", getattr(state, "ticket_id", "?"))
        return state
    
    system = {
    "role": "system",
    "content": (
        "You are an intent-classification agent for a ServiceNow automation workflow. "
        "Your task is to output exactly one label based on the ticket description. "
        "Output 'silence_alert' if the user is requesting alert suppression in any form "
        "(silence, mute, suppress, disable, stop, acknowledge, or similar). "
        "Output 'rfi' if the user is asking for information, research, "
        "web search, documentation, explanation, how-to, or needs to find answers to questions. "
        "Output 'assign_l1' for all other requests (general support, incidents, or issues). "
        "Rules: "
        "1. Output ONLY one of these three labels: silence_alert, rfi, or assign_l1. "
        "2. Do NOT include explanations, punctuation, or additional text. "
        "3. Do NOT modify or rephrase the labels."
    )
}
    human = {"role": "user", "content": state.description}
    logger.info("human message for classification: %s", human["content"])
    try:
        resp = client.invoke([system, human])
        intent = resp.content.strip().lower()

        logger.info("ChatGroq classification for ticket %s: intent=%s", getattr(state, "ticket_id", "?"), intent)   

        if "silence" in intent or "silence_alert" in intent:
            state.intent = "silence_alert"
        elif "rfi" in intent:
            state.intent = "rfi"
        elif "assign_l1" in intent:
            state.intent = "assign_l1"
        else:
            # Fallback to heuristic if LLM response is unclear
            logger.warning("Unclear LLM response, using heuristic for ticket %s", getattr(state, "ticket_id", "?"))
            desc = state.description.lower()
            if any(keyword in desc for keyword in ["silence", "suppress", "mute", "disable", "stop alert", "acknowledge"]):
                state.intent = "silence_alert"
            elif any(keyword in desc for keyword in ["know more", "how to", "what is", "explain", "search", "find", "information", "help me understand", "tell me about"]):
                state.intent = "rfi"
            else:
                state.intent = "assign_l1"

    except Exception as e:
        logger.error("ChatGroq classification failed; using heuristic", exc_info=True)
        desc = state.description.lower()
        if any(keyword in desc for keyword in ["silence", "suppress", "mute", "disable", "stop alert", "acknowledge"]):
            state.intent = "silence_alert"
        elif any(keyword in desc for keyword in ["know more", "how to", "what is", "explain", "search", "find", "information", "help me understand", "tell me about"]):
            state.intent = "rfi"
        else:
            state.intent = "assign_l1"

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
    # Snow Agent handles suppression: mark assigned and close immediately
    state.assigned_to = "Snow Agent"
    state.closed = True
    state.result = f"Grafana alert {state.alert_id} silenced by Snow Agent: {result}"
    logger.info("Grafana handled for ticket %s: result=%s", getattr(state, "ticket_id", "?"), result)
    return state

def assign_l1(state):
    state.assigned_to = "L1 Team"
    state.result = "Ticket assigned to L1 support"
    return state

def rfi_agent(state):
    """
    Handles RFI (Request for Information) tickets by performing a web search
    using TavilyClient and generating a concise, policy-aligned response.
    """
    state.assigned_to = "RFI Agent"
    try:
        # Perform a web search using TavilyClient
        response = tavily_client.search(state.description, max_results=3)
        results = response.get("results", [])
        
        if results:
            # Collect search context
            search_context = ""
            for result in results:
                content = result.get("content", "")
                search_context += content + " "
            
            # Use LLM to generate a concise, policy-aligned summary
            summary_system = {
                "role": "system",
                "content": (
                    "You are a company knowledge assistant. Based on the search results provided, "
                    "generate a clear, concise answer that addresses the user's question. "
                    "Frame your response according to company policies and best practices. "
                    "Keep the response under 800 characters. "
                    "Be direct and actionable. Include relevant links if available."
                )
            }
            summary_human = {
                "role": "user",
                "content": f"Question: {state.description}\n\nSearch Results:\n{search_context[:2000]}"
            }
            
            try:
                summary_resp = client.invoke([summary_system, summary_human])
                summary = summary_resp.content.strip()
                
                # Add source references
                sources = "\n\nSources:\n"
                for idx, result in enumerate(results[:3], 1):
                    title = result.get("title", "Source")
                    url = result.get("url", "")
                    sources += f"{idx}. {title}: {url}\n"
                
                final_response = summary + sources
                
                # Ensure total length is under 1000 characters
                if len(final_response) > 1000:
                    # Truncate summary to fit within limit
                    max_summary_len = 1000 - len(sources) - 20
                    summary = summary[:max_summary_len] + "..."
                    final_response = summary + sources
                
                state.work_comments = final_response[:1000]
                state.result = f"RFI processed: Generated summary from {len(results)} sources"
                state.closed = True
                logger.info("RFI handled for ticket %s: summary generated from %d results", 
                           getattr(state, "ticket_id", "?"), len(results))
            except Exception as llm_error:
                logger.error("LLM summarization failed, using raw results", exc_info=True)
                # Fallback to basic formatting
                formatted_results = "Research Results:\n\n"
                for idx, result in enumerate(results[:2], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "")
                    content = result.get("content", "")[:200]
                    formatted_results += f"{idx}. {title}\n{content}...\nSource: {url}\n\n"
                
                state.work_comments = formatted_results[:1000]
                state.result = f"RFI processed: Found {len(results)} results"
                state.closed = True
        else:
            state.work_comments = "No relevant information found for your query. Please provide more details or contact the IT support team for assistance."
            state.result = "RFI processed: No results found"
            state.closed = True
            logger.info("RFI handled for ticket %s: no results found", getattr(state, "ticket_id", "?"))
    except Exception as e:
        logger.error("TavilyClient search failed for ticket %s", getattr(state, "ticket_id", "?"), exc_info=True)
        state.work_comments = f"Unable to process your research request at this time. Error: {str(e)[:100]}. Please contact IT support for assistance."
        state.result = "RFI processing failed"
        state.closed = True

    return state