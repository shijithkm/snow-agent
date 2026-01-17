# Backend Documentation - Snow AI Agent

## Overview

The Snow AI Agent backend is a FastAPI-based service that automates ServiceNow ticket management using LangGraph workflows and AI-powered decision making. It handles alert suppression, information requests (RFI), and ticket routing through intelligent agent-based workflows.

## Architecture

```
backend/
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── graph/                     # LangGraph workflow definitions
│   ├── nodes.py              # Agent workflow nodes
│   ├── workflow.py           # Main workflow graph
│   ├── state.py              # State model for workflows
│   ├── chatbot_nodes.py      # Chatbot conversation logic
│   ├── chatbot_workflow.py   # Chatbot graph definition
│   └── chatbot_state.py      # Chatbot state model
├── services/                  # External service integrations
│   ├── grafana_mock.py       # Grafana alert management
│   └── servicenow_mock.py    # ServiceNow ticket management
└── models/                    # Data models
    └── ticket.py             # Ticket request/response models
```

## Core Components

### 1. Main Application (`main.py`)

**Purpose**: FastAPI application that exposes REST endpoints and orchestrates workflows.

**Key Features**:

- RESTful API endpoints for alerts, tickets, and chat
- In-memory session management for chat conversations
- Automatic ticket closure scheduling for suppression requests
- Workflow invocation and result processing

**Endpoints**:

#### `GET /alerts`

Returns all Grafana alerts with their current status.

**Response**:

```json
[
  {
    "id": "A-1",
    "name": "CPU High",
    "status": "firing|silenced|ok"
  }
]
```

#### `GET /tickets`

Returns all ServiceNow tickets.

**Response**:

```json
{
  "TKT-1": {
    "id": "TKT-1",
    "description": "suppress alert",
    "status": "open|in_progress|closed",
    "assigned_to": "Snow Agent|L1 Team|RFI Agent",
    "work_comments": "..."
  }
}
```

#### `POST /process_ticket`

Creates and processes a ticket through the agent workflow.

**Request Body**:

```json
{
  "description": "suppress alert A-1",
  "alert_id": "A-1",
  "ticket_type": "silence_alert|rfi|general",
  "start_time": "2026-01-17T10:00:00Z",
  "end_time": "2026-01-17T11:00:00Z"
}
```

#### `POST /chat`

Initiates or continues a chat conversation.

**Request Body**:

```json
{
  "session_id": "user-123",
  "message": "suppress alert A-1 for 1 hour"
}
```

**Response**:

```json
{
  "reply": "I'll suppress alert A-1 for 1 hour...",
  "ticket_created": false,
  "ticket_id": null
}
```

#### `GET /chat/{session_id}/history`

Retrieves chat conversation history.

---

### 2. Workflow Graph (`graph/workflow.py`)

**Purpose**: Defines the main agent routing workflow using LangGraph.

**Flow**:

```
START → classify_intent
         ├─ silence_alert → handle_grafana → END
         ├─ rfi → rfi_agent → END
         └─ assign_l1 → assign_l1 → END
```

**States**: Defined in `SNOWState` (see State Models below)

**Routing Logic**:

- **silence_alert**: Requests to suppress/silence/mute alerts → `handle_grafana`
- **rfi**: Information requests, research, documentation → `rfi_agent`
- **assign_l1**: General support tickets → `assign_l1`

---

### 3. Agent Nodes (`graph/nodes.py`)

#### `classify_intent(state)`

**Purpose**: Classifies user intent using LLM (ChatGroq with llama-3.1-8b-instant).

**Logic**:

1. Check explicit ticket_type field first
2. Use LLM classification with explicit prompt rules
3. Fallback to heuristic keyword matching if LLM unclear

**Prompt System Message**:

```
Output 'silence_alert' if user requests alert suppression in any form
(silence, mute, suppress, disable, stop, acknowledge, or similar)
Output 'rfi' if user asks for information/research
Output 'assign_l1' for all other requests
```

**Heuristic Keywords**:

- **silence_alert**: silence, suppress, mute, disable, stop alert, acknowledge
- **rfi**: know more, how to, what is, explain, search, find, information, help me understand, tell me about
- **assign_l1**: All other requests (default fallback)

**Returns**: Updated state with `intent` field set.

#### `handle_grafana(state)`

**Purpose**: Handles alert suppression requests by calling Grafana service.

**Logic**:

1. Extract alert_id, start_time, end_time from state
2. Call `silence_alert()` service
3. Set `assigned_to = "Snow Agent"`
4. Set `closed = True` (ticket closes immediately after suppression configured)
5. Set result message

**Returns**: Updated state with suppression confirmation.

#### `rfi_agent(state)`

**Purpose**: Handles information requests using web search and LLM summarization.

**Logic**:

1. Perform web search using TavilyClient (max 3 results)
2. Collect search context from results
3. Use LLM to generate concise, policy-aligned summary (<800 chars)
4. Add source references with URLs
5. Set `work_comments` with final response (<1000 chars)
6. Set `closed = True`
7. Handle errors gracefully with fallback formatting

**Dependencies**:

- TavilyClient for web search
- ChatGroq for summarization

**Returns**: Updated state with research results in `work_comments`.

#### `assign_l1(state)`

**Purpose**: Routes general support tickets to L1 team.

**Logic**:

1. Set `assigned_to = "L1 Team"`
2. Set result message

**Returns**: Updated state.

---

### 4. Chatbot Workflow (`graph/chatbot_workflow.py`)

**Purpose**: Conversational ticket creation workflow for natural language interactions.

**Flow**:

```
START → greeting → END
        ↓
user message → extract_info → check_required_fields
                                ├─ has_missing → ask_missing → END
                                └─ complete → create_ticket → END

user response → parse_user_response → check_required_fields (loop)
```

**Nodes**:

- `generate_greeting`: Provides available agent options
- `extract_info`: LLM-based extraction of ticket details
- `check_required_fields`: Validates required fields and detects vague descriptions
- `ask_for_missing_fields`: Generates contextual follow-up questions
- `parse_user_response`: Parses additional details from user response
- `create_ticket_from_chat`: Creates ticket and invokes main workflow

---

### 5. Chatbot Nodes (`graph/chatbot_nodes.py`)

#### `generate_greeting(state)`

**Returns**: Welcome message with agent options:

```
Welcome! I can help you with:
- Alert Suppression – Silence or mute Grafana alerts
- Information Requests (RFI) – Research and gather information
- General Support – Create tickets for IT support
```

#### `extract_info(state)`

**Purpose**: Extracts ticket information from user message using LLM.

**Extraction Fields**:

- `description`: Full ticket description
- `intent`: "silence_alert" | "rfi" | "general"
- `alert_id`: Alert identifier (e.g., "A-1")
- `start_time`: Suppression start time
- `end_time`: Suppression end time

**LLM Prompt**: Explicit rules for intent classification with examples.

#### `check_required_fields(state)`

**Purpose**: Validates required fields and detects vague descriptions.

**Required Fields by Intent**:

- **silence_alert**: `description`, `alert_id`
- **rfi**: `description`
- **general**: `description`

**Vague Description Detection**:

- Only checks if `details_requested == False` (prevents infinite loops)
- Patterns: "block ip", "reset password", "unlock account", "disable user", etc.
- Adds "more_details" to missing_fields if detected
- Sets `details_requested = True`

#### `ask_for_missing_fields(state)`

**Purpose**: Generates contextual follow-up questions for missing fields.

**Examples**:

- Missing `alert_id`: "Which alert would you like to suppress?"
- Missing `more_details`: "Which IP address would you like to block?" (LLM-generated)

#### `parse_user_response(state)`

**Purpose**: Parses additional details from user's follow-up response.

**Logic**:

1. Use LLM to extract missing fields from response
2. If "more_details" was requested, append to existing description
3. Remove filled fields from missing_fields list
4. Set `needs_user_input = False`

#### `create_ticket_from_chat(state)`

**Purpose**: Creates ticket and invokes main workflow.

**Logic**:

1. Determine ticket_type from intent
2. Call `create_ticket()` service
3. Invoke main workflow graph
4. Update state with ticket_id and results
5. Generate confirmation message

---

### 6. State Models

#### `SNOWState` (`graph/state.py`)

Main workflow state model.

```python
class SNOWState(BaseModel):
    ticket_id: Optional[str] = None
    description: Optional[str] = None
    intent: Optional[str] = None          # "silence_alert" | "rfi" | "assign_l1"
    alert_id: Optional[str] = None
    ticket_type: Optional[str] = None
    assigned_to: Optional[str] = None     # "Snow Agent" | "L1 Team" | "RFI Agent"
    closed: Optional[bool] = None         # Ticket closure status
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    work_comments: Optional[str] = None   # Research results or agent notes
```

#### `ChatbotState` (`graph/chatbot_state.py`)

Chatbot conversation state model.

```python
class ChatbotState(BaseModel):
    messages: List[ChatMessage] = []
    description: Optional[str] = None
    intent: Optional[str] = None
    alert_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    missing_fields: List[str] = []
    details_requested: bool = False       # Prevents infinite loop
    ticket_created: bool = False
    ticket_id: Optional[str] = None
    needs_user_input: bool = True
    target_agent: Optional[str] = None
```

---

### 7. Services

#### Grafana Service (`services/grafana_mock.py`)

**Purpose**: Manages Grafana alerts and suppression.

**Data Store**:

```python
alerts = [
    {"id": "A-1", "name": "CPU High", "status": "firing"},
    {"id": "A-2", "name": "Memory High", "status": "ok"},
    {"id": "A-3", "name": "Disk Full", "status": "firing"}
]
```

**Functions**:

##### `silence_alert(alert_id, start_time=None, end_time=None)`

Suppresses an alert for a specified time window.

**Parameters**:

- `alert_id`: Alert identifier
- `start_time`: Suppression start time (optional)
- `end_time`: Suppression end time (optional)

**Returns**:

```python
{
    "status": "success",
    "silenced_from": "2026-01-17T10:00:00Z",
    "silenced_until": "2026-01-17T11:00:00Z"
}
```

**Side Effects**:

- Sets alert status to "silenced"
- Records suppression window in alert metadata

#### ServiceNow Service (`services/servicenow_mock.py`)

**Purpose**: Manages ServiceNow tickets.

**Data Store**:

```python
tickets = {}  # In-memory ticket storage
```

**Functions**:

##### `create_ticket(description, alert_id=None, ticket_type=None, start_time=None, end_time=None, assigned_to=None)`

Creates a new ServiceNow ticket.

**Parameters**:

- `description`: Ticket description
- `alert_id`: Associated alert ID (optional)
- `ticket_type`: "silence_alert" | "rfi" | "general"
- `start_time`: Suppression start time (optional)
- `end_time`: Suppression end time (optional)
- `assigned_to`: Initial assignment (optional)

**Returns**: `ticket_id` (e.g., "TKT-1")

**Side Effects**:

- Adds ticket to in-memory store
- For silence_alert: automatically calls `silence_alert()` in Grafana
- Sets initial status to "suppressed" for silence_alert, "open" otherwise

---

## Configuration

### Environment Variables

```bash
GROQ_API_KEY=gsk_...                          # Groq API key for LLM
TAVILY_API_KEY=tvly-dev-...                   # Tavily API key for web search
```

### LLM Configuration

**Model**: `llama-3.1-8b-instant` via ChatGroq

**Usage**:

- Intent classification
- Field extraction from natural language
- Vague description detection
- Follow-up question generation
- Research result summarization

---

## Workflow Examples

### Example 1: Alert Suppression

**User Request**: "suppress alert A-1 for 1 hour"

**Flow**:

1. `classify_intent`: Detects "silence_alert" intent
2. `handle_grafana`:
   - Calls `silence_alert("A-1", start, end)`
   - Sets assigned_to = "Snow Agent"
   - Sets closed = True
3. Ticket status: "closed"
4. Grafana alert A-1 status: "silenced"

### Example 2: Information Request (RFI)

**User Request**: "what is kubernetes?"

**Flow**:

1. `classify_intent`: Detects "rfi" intent
2. `rfi_agent`:
   - TavilyClient searches web for "what is kubernetes?"
   - Retrieves top 3 results
   - LLM summarizes results
   - Formats with source URLs
3. work_comments set with summary
4. Ticket status: "closed"
5. User receives research summary

### Example 3: Vague Description Handling

**User Request**: "block ip address"

**Chat Flow**:

1. `extract_info`: Extracts description
2. `check_required_fields`: Detects vague pattern
3. `ask_for_missing_fields`: "Which IP address would you like to block?"
4. User responds: "192.168.1.100"
5. `parse_user_response`: Appends to description
6. `create_ticket_from_chat`: Creates ticket with full details

**Final Description**: "block ip address - 192.168.1.100"

---

## Error Handling

### LLM Failures

**Scenario**: ChatGroq API error during classification

**Handling**:

- Catches exception and logs error
- Falls back to keyword-based heuristic classification
- Continues workflow without interruption

### Search Failures

**Scenario**: TavilyClient search error

**Handling**:

- Catches exception and logs error
- Sets work_comments with error message
- Still closes ticket with status
- User receives friendly error message

### Missing Data

**Scenario**: Required field missing (e.g., alert_id for silence_alert)

**Handling**:

- Chatbot workflow asks follow-up questions
- Loops until all required fields collected
- Prevents ticket creation with incomplete data

---

## Logging

All modules use Python's `logging` module with INFO level.

**Log Format**:

```
%(asctime)s %(levelname)s %(name)s - %(message)s
```

**Key Log Points**:

- Ticket creation with all parameters
- Intent classification results
- Agent assignments
- Grafana suppression confirmation
- RFI search and summarization
- Error conditions with stack traces

**Loggers**:

- `backend`: Main application
- `backend.graph.nodes`: Agent nodes
- `backend.services.grafana`: Grafana service
- `backend.services.servicenow`: ServiceNow service

---

## Dependencies

### Core Dependencies

```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.0
langgraph>=0.0.20
langchain-groq>=0.1.0
tavily-python>=0.3.0
```

### Development Dependencies

```
python>=3.10
pytest>=7.4.0
```

---

## API Integration Points

### External APIs

1. **Groq API**: LLM inference for intent classification and text generation
2. **Tavily API**: Web search for RFI agent research

### Internal Services

1. **Grafana Mock**: Alert management (replaceable with real Grafana API)
2. **ServiceNow Mock**: Ticket management (replaceable with real ServiceNow API)

---

## Future Enhancements

1. **Persistent Storage**: Replace in-memory stores with database (PostgreSQL/MongoDB)
2. **Real Integrations**: Replace mock services with actual Grafana and ServiceNow APIs
3. **Authentication**: Add JWT-based authentication for API endpoints
4. **WebSocket Support**: Real-time chat updates via WebSocket
5. **Multi-tenant**: Support multiple organizations with data isolation
6. **Advanced Workflows**: Add more agent types (security, compliance, etc.)
7. **Metrics**: Prometheus metrics for monitoring workflow performance
8. **Rate Limiting**: Protect LLM/search APIs with rate limiting
9. **Caching**: Cache LLM responses and search results for common queries
10. **Audit Trail**: Comprehensive logging of all ticket actions

---

## Deployment

### Docker

```bash
cd backend
docker build -t snow-ai-agent-backend .
docker run -p 8000:8000 \
  -e GROQ_API_KEY=gsk_... \
  -e TAVILY_API_KEY=tvly-dev-... \
  snow-ai-agent-backend
```

### Local Development

```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...
export TAVILY_API_KEY=tvly-dev-...
python -c "from main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

---

## Docker Deployment

### Configuration

The backend is containerized using Docker for production deployment.

**Dockerfile** (`backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port and run with reload enabled
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Docker Compose Configuration**:

```yaml
backend:
  build: ./backend
  container_name: snow-ai-backend
  ports:
    - "8000:8000"
  environment:
    - GROQ_API_KEY=gsk_...
    - TAVILY_API_KEY=tvly-dev-...
  networks:
    - app-network
```

### Build and Run

```bash
# Build backend container
docker-compose build backend

# Start backend
docker-compose up -d backend

# View logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Stop backend
docker-compose stop backend
```

### Environment Variables

Set API keys in `docker-compose.yml`:

```yaml
environment:
  - GROQ_API_KEY=your_groq_api_key_here
  - TAVILY_API_KEY=your_tavily_api_key_here
```

### Network Configuration

- **Internal Access**: `http://backend:8000` (from frontend container)
- **External Access**: `http://localhost:8000` (from host machine)
- **Docker Network**: Bridge network (`app-network`)

### API Documentation

Access Swagger UI at `http://localhost:8000/docs` when backend is running.

### Monitoring

```bash
# Check backend health
curl http://localhost:8000/alerts

# View real-time logs
docker-compose logs -f backend

# Check container status
docker ps | grep backend

# View container resource usage
docker stats snow-ai-backend
```

### Troubleshooting Docker

**Container won't start**:

- Check logs: `docker-compose logs backend`
- Verify API keys are set in docker-compose.yml
- Ensure port 8000 is not in use: `netstat -ano | findstr :8000`

**"Connection refused" from frontend**:

- Verify backend container is running: `docker ps`
- Check network: `docker network inspect snow-ai-agent_app-network`
- Ensure both containers are on same network

**Code changes not reflecting**:

- Rebuild container: `docker-compose up -d --build backend`
- Check `--reload` flag in CMD (enables hot reload)

---

## Testing

### Manual Testing

```bash
# Test alert suppression
curl -X POST http://localhost:8000/process_ticket \
  -H "Content-Type: application/json" \
  -d '{"description": "suppress alert", "alert_id": "A-1", "ticket_type": "silence_alert"}'

# Test RFI
curl -X POST http://localhost:8000/process_ticket \
  -H "Content-Type: application/json" \
  -d '{"description": "what is kubernetes?", "ticket_type": "rfi"}'

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "message": "suppress alert A-1 for 1 hour"}'
```

### Expected Results

- Tickets created with sequential IDs (TKT-1, TKT-2, ...)
- Silence_alert tickets closed immediately
- RFI tickets closed with research results in work_comments
- Chat sessions maintained across multiple messages

---

## Troubleshooting

### Issue: "ChatGroq classification failed"

**Cause**: Invalid or missing GROQ_API_KEY

**Solution**: Verify API key is set correctly in environment variables

### Issue: "TavilyClient search failed"

**Cause**: Invalid or missing TAVILY_API_KEY

**Solution**: Verify API key is set correctly in environment variables

### Issue: "Ticket stays in_progress"

**Cause**: Ticket closure logic not working

**Solution**: Check `handle_grafana` sets `closed = True` and main.py processes closed flag

### Issue: "Infinite loop asking for details"

**Cause**: `details_requested` flag not being set/checked

**Solution**: Verify `check_required_fields` checks `details_requested` flag before adding "more_details"

---

## Contact & Support

For questions or issues, please refer to the main project README or contact the development team.
