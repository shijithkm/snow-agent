# Confluence MCP Server

A Model Context Protocol (MCP) server that provides HTTP endpoints for searching and retrieving Confluence content.

## Features

- 🔍 Search Confluence content using CQL (Confluence Query Language)
- 📄 Retrieve specific pages by ID
- 🔐 Secure authentication using Confluence API tokens
- 🚀 Fast and lightweight Node.js/Express server
- 📊 Relevance scoring for search results

## Prerequisites

- Node.js 18 or higher
- Confluence Cloud account (or Confluence Server/Data Center)
- Confluence API token

## Getting Your Confluence API Token

### For Confluence Cloud:

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Give it a name (e.g., "MCP Server")
4. Copy the token (you won't see it again!)

### Configuration:

- **Base URL**: Your Confluence URL (e.g., `https://your-company.atlassian.net`)
- **Email**: Your Confluence account email
- **API Token**: The token you just created
- **Space Key**: (Optional) Limit searches to a specific space

## Installation

1. **Install dependencies:**

```bash
cd mcp-server
npm install
```

2. **Create .env file:**

```bash
cp .env.example .env
```

3. **Edit .env with your Confluence credentials:**

```env
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
CONFLUENCE_SPACE_KEY=YOUR_SPACE
PORT=3001
```

## Running the Server

### Development mode (with auto-reload):

```bash
npm run dev
```

### Production mode:

```bash
npm run build
npm start
```

The server will start on http://localhost:3001 (or the PORT you specified).

## API Endpoints

### 1. Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "ok",
  "service": "Confluence MCP Server",
  "timestamp": "2026-01-18T12:00:00.000Z"
}
```

### 2. Search Confluence

```http
POST /search
Content-Type: application/json

{
  "query": "onboard new employee",
  "max_results": 5
}
```

**Response:**

```json
{
  "query": "onboard new employee",
  "count": 3,
  "results": [
    {
      "id": "123456",
      "title": "Employee Onboarding Guide",
      "content": "Full page content...",
      "excerpt": "This guide covers the steps for onboarding new employees...",
      "url": "https://your-domain.atlassian.net/wiki/spaces/HR/pages/123456",
      "space": "Human Resources",
      "relevance_score": 1.0
    }
  ]
}
```

### 3. Get Page by ID

```http
GET /page/123456
```

**Response:**

```json
{
  "id": "123456",
  "title": "Employee Onboarding Guide",
  "content": "Full page content...",
  "body": "Full page content...",
  "url": "https://your-domain.atlassian.net/wiki/spaces/HR/pages/123456",
  "space": "Human Resources"
}
```

## Integrating with Backend

Update your backend's `.env` file:

```env
CONFLUENCE_ENABLED=true
CONFLUENCE_MCP_URL=http://localhost:3001
```

Or set environment variables in terminal:

```powershell
# PowerShell
$env:CONFLUENCE_ENABLED="true"
$env:CONFLUENCE_MCP_URL="http://localhost:3001"
```

Then restart your backend:

```bash
uvicorn main:app --reload --port 8000
```

## Testing the Server

### Using curl:

```bash
# Health check
curl http://localhost:3001/health

# Search
curl -X POST http://localhost:3001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "onboarding", "max_results": 3}'

# Get page
curl http://localhost:3001/page/123456
```

### Using PowerShell:

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:3001/health"

# Search
$body = @{
    query = "onboarding"
    max_results = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3001/search" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## Troubleshooting

### Authentication Failed

- Verify your Confluence email and API token are correct
- Ensure your API token has not expired
- Check that your base URL is correct (no trailing slash)

### Connection Timeout

- Check that your Confluence instance is accessible
- Verify firewall/network settings
- Try increasing timeout in `confluence-client.ts`

### No Results Found

- Verify the space key is correct (if specified)
- Check that you have permission to view the content
- Try a simpler search query

### Port Already in Use

Change the PORT in `.env`:

```env
PORT=3002
```

And update backend's `CONFLUENCE_MCP_URL`:

```env
CONFLUENCE_MCP_URL=http://localhost:3002
```

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Backend   │  HTTP   │ MCP Server  │   API   │  Confluence │
│  (Python)   ├────────►│  (Node.js)  ├────────►│    Cloud    │
└─────────────┘         └─────────────┘         └─────────────┘
```

The MCP server acts as a middleware that:

1. Receives search requests from the backend
2. Translates them to Confluence API calls
3. Processes and formats the results
4. Returns structured JSON responses

## Security Notes

- **Never commit .env file** to version control
- Store API tokens securely
- Use environment variables in production
- Consider rate limiting for production use
- Use HTTPS in production environments

## License

MIT
