import os
import logging
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from .chatbot_state import ChatbotState, ChatMessage

logger = logging.getLogger("backend.graph.chatbot")

# Lazy initialization of client
_client = None

def get_client():
    """Get or create the ChatGroq client."""
    global _client
    if _client is None:
        _client = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant"
        )
    return _client


def _extract_datetime_with_llm(user_message: str, missing_fields: list) -> dict:
    """Use LLM to extract datetime information from user message."""
    import json
    from datetime import datetime
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    fields_str = ", ".join(missing_fields)
    
    system_prompt = f"""You are a datetime extraction assistant. Current date is {current_date} and current time is {current_time}.

REQUIRED FIELDS TO EXTRACT: {fields_str}

Extract datetime information from the user's message and return them in ISO format (YYYY-MM-DD HH:MM).

Rules:
1. If user says "tomorrow", use date {tomorrow_date}
2. If user says "today" or "now", use date {current_date}
3. Convert AM/PM to 24-hour format (6 PM = 18:00, 7 PM = 19:00)
4. If time range is given (e.g., "6 to 7 PM"), extract both times
5. If only time is mentioned without date, assume tomorrow for future times

IMPORTANT: You MUST extract ALL fields in this list: {fields_str}

Return ONLY a JSON object with the required fields. Do not include fields not in the required list.

Examples:
- Required: start_time | User: "tomorrow 6 PM EST" -> {{"start_time": "{tomorrow_date} 18:00"}}
- Required: end_time | User: "tomorrow 7 PM EST" -> {{"end_time": "{tomorrow_date} 19:00"}}
- Required: end_time | User: "7 PM" -> {{"end_time": "{tomorrow_date} 19:00"}}
- Required: start_time, end_time | User: "tomorrow 6 to 7 PM EST" -> {{"start_time": "{tomorrow_date} 18:00", "end_time": "{tomorrow_date} 19:00"}}
"""
    
    try:
        client = get_client()
        response = client.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract datetime from: {user_message}"}
        ])
        
        # Parse LLM response
        response_text = response.content.strip()
        logger.info("LLM raw response for datetime extraction: %s", response_text)
        
        # Remove markdown code blocks if present
        if "```" in response_text:
            response_text = response_text.split("```")[1].replace("json", "").strip()
        
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            response_text = json_match.group(0)
        
        extracted_data = json.loads(response_text)
        logger.info("Parsed datetime data: %s", extracted_data)
        
        result = {}
        if "start_time" in extracted_data and extracted_data["start_time"] and "start_time" in missing_fields:
            try:
                result["start_time"] = datetime.strptime(extracted_data["start_time"], "%Y-%m-%d %H:%M")
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM start_time '%s': %s", extracted_data.get("start_time"), e)
        
        if "end_time" in extracted_data and extracted_data["end_time"] and "end_time" in missing_fields:
            try:
                result["end_time"] = datetime.strptime(extracted_data["end_time"], "%Y-%m-%d %H:%M")
            except (ValueError, TypeError) as e:
                logger.warning("Failed to parse LLM end_time '%s': %s", extracted_data.get("end_time"), e)
        
        return result
    except Exception as e:
        logger.error("LLM datetime extraction failed: %s", e, exc_info=True)
        return {}


def extract_info(state: ChatbotState) -> ChatbotState:
    """Extract ticket information from the conversation."""
    # Get the latest user message
    user_messages = [m.content for m in state.messages if m.role == "user"]
    if not user_messages:
        return state
    
    conversation = "\n".join(user_messages)
    
    # Use LLM to extract intent
    system = {
        "role": "system",
        "content": (
            "You are an intent classifier for a ServiceNow ticketing system. "
            "Classify the user's message into EXACTLY one of these intents.\n\n"
            "Output ONLY ONE WORD: 'rfi', 'ritm', or 'incident'\n\n"
            "CRITICAL CLASSIFICATION RULES:\n\n"
            "Choose 'rfi' when user is:\n"
            "- Asking WHAT IS something (policies, procedures, guidelines, definitions)\n"
            "- Asking HOW TO do something (steps, instructions, process)\n"
            "- Requesting INFORMATION or RESEARCH (looking up details, finding documentation)\n"
            "- Asking EXPLAIN or TELL ME ABOUT a topic\n"
            "- Questions starting with: what, how, why, where, when, explain, tell me\n"
            "Examples: 'what is the password policy', 'how to onboard employee', 'tell me about leave policy'\n\n"
            "Choose 'ritm' when user wants to:\n"
            "- REQUEST or SUPPRESS or SILENCE alerts (alert management)\n"
            "- REQUEST access to systems, applications, or resources\n"
            "- REQUEST software installation or hardware\n"
            "- REQUEST new accounts, permissions, or privileges\n"
            "- REQUEST services or items to be provisioned\n"
            "Examples: 'suppress alert', 'silence monitoring', 'need access to Jira', 'request laptop', 'create new user account'\n\n"
            "Choose 'incident' when user:\n"
            "- Reports a BROKEN or NOT WORKING system/service\n"
            "- Has an ERROR or PROBLEM that needs fixing\n"
            "- Reports service disruptions or outages\n"
            "Examples: 'my laptop is not working', 'application is down', 'getting error message'\n\n"
            "User message: {message}"
        )
    }
    
    try:
        client = get_client()
        prompt = system["content"].replace("{message}", conversation)
        resp = client.invoke([{"role": "system", "content": prompt}])
        intent = resp.content.strip().lower()
        
        logger.info("LLM classified intent as: '%s' for conversation: '%s'", intent, conversation)
        
        if "silence_alert" in intent:
            state.intent = "silence_alert"
            state.target_agent = "suppress_agent"
        elif "rfi" in intent:
            state.intent = "rfi"
            state.target_agent = "rfi_agent"
        elif "ritm" in intent:
            state.intent = "ritm"
            state.target_agent = "l1_agent"
        elif "incident" in intent:
            state.intent = "incident"
            state.target_agent = "l1_agent"
        else:
            # Default to incident for unclear cases
            state.intent = "incident"
            state.target_agent = "l1_agent"
    except Exception as e:
        logger.error("Failed to extract intent", exc_info=True)
        state.intent = "incident"
        state.target_agent = "l1_agent"
    
    # Only store description if the message is more than just the intent
    # Don't store generic phrases like "Information Request", "Alert Suppression", etc.
    last_msg = user_messages[-1].lower().strip()
    generic_phrases = ["information request", "rfi", "ritm", "incident", "requested item", "request for information"]
    
    is_generic = any(phrase in last_msg for phrase in generic_phrases)
    logger.info("Checking description - last_msg: '%s', is_generic: %s, current description: '%s'", last_msg, is_generic, state.description)
    
    if not state.description and not is_generic:
        # Message has actual content, use it as description
        state.description = user_messages[-1]
        logger.info("Set description to: '%s'", state.description)
    
    logger.info("Extracted intent: %s, target_agent: %s, description: %s", state.intent, state.target_agent, state.description)
    
    return state


def check_required_fields(state: ChatbotState) -> ChatbotState:
    """Check if all required fields are present for the identified intent."""
    state.missing_fields = []
    
    if state.intent == "rfi":
        # Only need description
        if not state.description:
            state.missing_fields.append("description")
    elif state.intent == "ritm":
        # RITM ticket needs description
        if not state.description:
            state.missing_fields.append("description")
        else:
            # Check if this is a suppress alerts request
            desc_lower = state.description.lower() if state.description else ""
            is_suppress_request = any(keyword in desc_lower for keyword in ["suppress", "silence", "mute", "stop alert", "disable alert"])
            
            if is_suppress_request:
                # This is a suppress alerts RITM - need alert_id, application, start_time, end_time
                if not state.alert_id:
                    state.missing_fields.append("alert_id")
                if not state.application:
                    state.missing_fields.append("application")
                if not state.start_time:
                    state.missing_fields.append("start_time")
                if not state.end_time:
                    state.missing_fields.append("end_time")
                logger.info("Suppress alerts RITM detected, missing fields: %s", state.missing_fields)
    elif state.intent == "incident":
        # Incident ticket needs description
        if not state.description:
            state.missing_fields.append("description")
        elif state.description:
            # Check if we should validate for vagueness
            if state.details_requested:
                # Already asked for details once, don't check again - accept whatever we have
                logger.info("Details already requested, accepting description: '%s'", state.description)
            else:
                # First time - check for vague description
                desc_lower = state.description.lower().strip()
                vague_patterns = [
                    "block ip", "reset password", "unlock account",
                    "create user", "delete user", "access issue", "need access",
                    "permission denied", "can't access", "unable to login",
                    "help", "issue", "problem", "error", "not working"
                ]
                
                # Check if description matches vague patterns or is too short
                is_vague = any(desc_lower == pattern or desc_lower.startswith(pattern + " ") or desc_lower == pattern + "s" 
                              for pattern in vague_patterns)
                is_too_short = len(desc_lower.split()) <= 4 and any(word in desc_lower for word in ["block", "reset", "unlock", "create", "delete", "access", "need", "issue", "problem"])
                
                if is_vague or is_too_short:
                    state.missing_fields.append("more_details")
                    state.details_requested = True  # Mark that we're requesting details
                    logger.info("Description is too vague, requesting more details: '%s'", state.description)
                else:
                    logger.info("Description is sufficient: '%s'", state.description)
    
    logger.info("Missing fields: %s", state.missing_fields)
    return state


def ask_for_missing_fields(state: ChatbotState) -> ChatbotState:
    """Generate a message asking for missing required fields."""
    if not state.missing_fields:
        return state
    
    # Get available alerts for alert_id prompts
    available_alerts_text = ""
    if "alert_id" in state.missing_fields:
        try:
            from services.grafana_mock import alerts
            alert_list = [f"• **{alert['id']}** - {alert['name']} (status: {alert['status']})" for alert in alerts]
            available_alerts_text = "\n\n📋 **Available alerts:**\n" + "\n".join(alert_list)
        except Exception as e:
            logger.warning("Failed to fetch alerts: %s", e)
    
    # For suppress alerts RITM, ask in specific order: alert_id, application, then time
    if state.intent == "ritm" and "alert_id" in state.missing_fields:
        # Ask for alert_id first
        prompt = f"Which alert would you like to silence?{available_alerts_text}"
        state.messages.append(ChatMessage(role="assistant", content=prompt))
        state.needs_user_input = True
        logger.info("Asking for alert_id first for suppress alerts RITM")
        return state
    
    if state.intent == "ritm" and "application" in state.missing_fields and "alert_id" not in state.missing_fields:
        # Ask for application second
        prompt = "Which application is this alert for? (e.g., 'Website 1' or 'Website 2')"
        state.messages.append(ChatMessage(role="assistant", content=prompt))
        state.needs_user_input = True
        logger.info("Asking for application for suppress alerts RITM")
        return state
    
    # Special case: if both start_time and end_time are missing, ask for them together
    if "start_time" in state.missing_fields and "end_time" in state.missing_fields:
        prompt = "When should the silence period be? (e.g., 'tomorrow 6 to 7 PM EST' or '2026-01-20 14:00 to 2026-01-20 15:00')"
        state.messages.append(ChatMessage(role="assistant", content=prompt))
        state.needs_user_input = True
        logger.info("Asking for both start_time and end_time together")
        return state
    
    field_prompts = {
        "alert_id": f"Which alert would you like to silence?{available_alerts_text}",
        "application": "Which application is this alert for? (e.g., 'Website 1' or 'Website 2')",
        "start_time": "When should the silence period start? (e.g., 'tomorrow 6 PM EST' or '2026-01-20 14:00')",
        "end_time": "When should the silence period end? (e.g., 'tomorrow 7 PM EST' or '2026-01-20 15:00')",
        "description": {
            "rfi": "What information are you looking for? Please describe what you need to research or find out.",
            "silence_alert": "Please provide additional details about this alert suppression.",
            "general": "What issue or request would you like help with? Please provide details."
        }.get(state.intent, "Could you please provide more details about your request?"),
        "more_details": None  # Will be handled specially below
    }
    
    # Check if we already asked for this field in the last message
    if len(state.messages) >= 2 and state.messages[-1].role == "assistant":
        last_assistant_msg = state.messages[-1].content.lower()
        # If we just asked for the same field, don't ask again immediately
        # Instead, provide helpful feedback
        first_missing = state.missing_fields[0]
        if any(keyword in last_assistant_msg for keyword in [first_missing.replace("_", " "), "which alert", "when should"]):
            clarification = f"I didn't quite catch that. {field_prompts.get(first_missing, f'Please provide the {first_missing}.')}"
            state.messages.append(ChatMessage(
                role="assistant", 
                content=clarification
            ))
            state.needs_user_input = True
            logger.info("Re-asking for missing field with clarification: %s", first_missing)
            return state
    
    # Ask for the first missing field
    first_missing = state.missing_fields[0]
    
    # Special handling for "more_details"
    if first_missing == "more_details":
        # Use LLM to generate a contextual prompt asking for more details
        try:
            client = get_client()
            system_prompt = {
                "role": "system",
                "content": (
                    "You are a helpful assistant. The user provided a vague request: '{description}'. "
                    "Generate a polite, specific question asking for more details needed to complete this request. "
                    "Keep it under 100 characters. Be direct and helpful."
                )
            }
            prompt_content = system_prompt["content"].replace("{description}", state.description or "")
            resp = client.invoke([{"role": "system", "content": prompt_content}])
            prompt = resp.content.strip()
            
            # Fallback to template if LLM fails
            if not prompt or len(prompt) > 200:
                desc_keywords = state.description.lower()
                if "block ip" in desc_keywords:
                    prompt = "Which IP address would you like to block? Please provide the IP address and reason."
                elif "reset password" in desc_keywords:
                    prompt = "For which user account should the password be reset?"
                elif "unlock account" in desc_keywords:
                    prompt = "Which user account needs to be unlocked?"
                elif "access" in desc_keywords or "permission" in desc_keywords:
                    prompt = "What resource or system do you need access to? Please provide details."
                else:
                    prompt = f"Could you provide more details about '{state.description}'? What specifically do you need?"
        except Exception as e:
            logger.warning("LLM prompt generation failed: %s", e)
            prompt = f"Could you provide more details about '{state.description}'? What specifically do you need?"
    else:
        prompt = field_prompts.get(first_missing, f"Please provide the {first_missing}.")
    
    state.messages.append(ChatMessage(role="assistant", content=prompt))
    state.needs_user_input = True
    
    logger.info("Asking for missing field: %s", first_missing)
    return state


def parse_user_response(state: ChatbotState) -> ChatbotState:
    """Parse user's response to extract missing field values."""
    if not state.messages or state.messages[-1].role != "user":
        return state
    
    last_message = state.messages[-1].content
    last_message_lower = last_message.lower()
    
    # Handle "more_details" - append to existing description
    if "more_details" in state.missing_fields:
        if last_message.strip():
            # Append the additional details to the existing description
            state.description = f"{state.description}. {last_message.strip()}"
            state.missing_fields.remove("more_details")
            logger.info("Added more details to description: %s", state.description)
    
    # Extract description if needed
    if "description" in state.missing_fields:
        # Any non-empty message can be the description
        if last_message.strip():
            state.description = last_message.strip()
            state.missing_fields.remove("description")
            logger.info("Extracted description: %s", state.description)
    
    # Try to extract alert_id
    if "alert_id" in state.missing_fields:
        # Look for alert ID patterns - be more flexible
        import re
        alert_match = re.search(r'(a-\d+|alert[-_\s]?\d+|alert[-_\s]?[a-z0-9]+|\d+)', last_message, re.IGNORECASE)
        if alert_match:
            extracted_id = alert_match.group(1)
            # Normalize to just the number
            if extracted_id.isdigit():
                state.alert_id = extracted_id
            else:
                state.alert_id = extracted_id.upper()
            state.missing_fields.remove("alert_id")
            logger.info("Extracted alert_id: %s", state.alert_id)
        # If user just provided a simple value, use it as is
        elif len(last_message.strip().split()) <= 5:
            # Clean up the input
            clean_input = last_message.strip()
            if clean_input and not any(word in last_message_lower for word in ['when', 'what', 'how', 'where', 'why']):
                state.alert_id = clean_input
                state.missing_fields.remove("alert_id")
                logger.info("Extracted alert_id from simple input: %s", state.alert_id)
    
    # Extract application
    if "application" in state.missing_fields:
        # Look for website patterns
        if "website" in last_message_lower:
            if "1" in last_message or "one" in last_message_lower:
                state.application = "website1"
                state.missing_fields.remove("application")
                logger.info("Extracted application: website1")
            elif "2" in last_message or "two" in last_message_lower:
                state.application = "website2"
                state.missing_fields.remove("application")
                logger.info("Extracted application: website2")
        # Direct match
        elif last_message.strip().lower() in ["website1", "website 1"]:
            state.application = "website1"
            state.missing_fields.remove("application")
            logger.info("Extracted application: website1")
        elif last_message.strip().lower() in ["website2", "website 2"]:
            state.application = "website2"
            state.missing_fields.remove("application")
            logger.info("Extracted application: website2")
    
    # Use LLM to extract datetime information
    if "start_time" in state.missing_fields or "end_time" in state.missing_fields:
        extracted_times = _extract_datetime_with_llm(last_message, state.missing_fields)
        
        if extracted_times.get("start_time") and "start_time" in state.missing_fields:
            state.start_time = extracted_times["start_time"]
            state.missing_fields.remove("start_time")
            logger.info("LLM extracted start_time: %s", state.start_time)
        
        if extracted_times.get("end_time") and "end_time" in state.missing_fields:
            state.end_time = extracted_times["end_time"]
            state.missing_fields.remove("end_time")
            logger.info("LLM extracted end_time: %s", state.end_time)
    
    return state


def create_ticket_from_chat(state: ChatbotState) -> ChatbotState:
    """Create a ticket using the extracted information."""
    from services.servicenow_mock import create_ticket
    
    try:
        # Map target_agent to display names
        agent_display_name = {
            "suppress_agent": "Ops Agent",
            "rfi_agent": "RFI Agent",
            "l1_agent": "L1 Team"
        }.get(state.target_agent, state.target_agent)
        
        # Determine service_type for RITM tickets
        service_type = None
        if state.intent == "ritm":
            desc_lower = state.description.lower() if state.description else ""
            if any(keyword in desc_lower for keyword in ["suppress", "silence", "mute", "stop alert", "disable alert"]):
                service_type = "suppress_alerts"
        
        ticket_id = create_ticket(
            description=state.description,
            alert_id=state.alert_id,
            ticket_type=state.intent,
            start_time=state.start_time,
            end_time=state.end_time,
            assigned_to=agent_display_name,
            service_type=service_type,
            application=state.application,
            source="chatbot"
        )
        
        state.ticket_id = ticket_id
        state.ticket_created = True
        
        # Create success message with status indication
        message = f"✅ Ticket {ticket_id} has been created successfully!\n\n"
        message += f"Type: {state.intent}\n"
        message += f"Assigned to: {agent_display_name}\n"
        
        # L1 tickets remain OPEN for manual processing
        if state.target_agent == "l1_agent":
            message += f"Status: OPEN (awaiting L1 Team action)\n"
        
        if state.alert_id:
            message += f"Alert ID: {state.alert_id}\n"
        if state.start_time:
            message += f"Start Time: {state.start_time.strftime('%Y-%m-%d %H:%M')}\n"
        if state.end_time:
            message += f"End Time: {state.end_time.strftime('%Y-%m-%d %H:%M')}\n"
        
        message += "\nYour request is being processed."
        
        state.messages.append(ChatMessage(role="assistant", content=message))
        state.needs_user_input = False
        
        logger.info("Created ticket %s from chat", ticket_id)
    except Exception as e:
        logger.error("Failed to create ticket from chat", exc_info=True)
        state.messages.append(ChatMessage(
            role="assistant",
            content=f"❌ Sorry, I encountered an error creating your ticket: {str(e)}"
        ))
        state.needs_user_input = False
    
    return state


def generate_greeting(state: ChatbotState) -> ChatbotState:
    """Generate initial greeting message."""
    if len(state.messages) == 0:
        greeting = (
            "👋 Hello! I'm your **ServiceNow Operations Agent**. How can I help you today?\n\n"
            "I can assist with:\n"
            "• 📚 **RFI (Request for Information)** – Search for information, ask 'how to' questions, or research topics\n"
            "• 🎫 **RITM (Requested Item)** – Request access, software, hardware, or services\n"
            "• 🚨 **INCIDENT** – Report system issues, errors, or service disruptions\n\n"
            "Please describe what you need help with."
        )
        state.messages.append(ChatMessage(role="assistant", content=greeting))
        state.needs_user_input = True
    
    return state
