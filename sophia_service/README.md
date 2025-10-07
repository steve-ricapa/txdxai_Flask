# SOPHIA AI Agent Service

RAG-based cybersecurity assistant using Microsoft Agent Framework (Azure AI Agents).

## Overview

SOPHIA is a multi-tenant AI agent that:
- Searches company-specific knowledge bases using RAG
- Queries security tools (Splunk, Palo Alto, Grafana) read-only
- Hands off infrastructure actions to VICTORIA via ticket creation
- Maintains conversation memory per user with threads

## Architecture

### Components
- **Orchestrator**: Microsoft Agent Framework integration
- **Tools**: RAG search, Splunk, Palo Alto, Grafana, ticket creation
- **Flask API**: /chat and /refresh endpoints
- **Multi-tenant**: Company-level isolation with agent instances

### Authentication
Uses agent access keys from TxDxAI backend agent provisioning system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

3. Run service:
```bash
python app.py
```

Service runs on port 5001 by default.

## API Endpoints

### POST /chat
Chat with SOPHIA agent.

**Request:**
```json
{
  "companyId": 2,
  "userId": 2,
  "message": "What are our firewall policies?",
  "threadId": "optional-thread-id",
  "agentAccessKey": "your-access-key"
}
```

**Response:**
```json
{
  "response": "SOPHIA's response",
  "threadId": "thread-xxx",
  "agentId": "agent-xxx",
  "toolCalls": []
}
```

### POST /refresh
Refresh knowledge base from sources.

**Request:**
```json
{
  "companyId": 2,
  "agentAccessKey": "your-access-key"
}
```

## Tools

1. **rag_search**: Search company knowledge base
2. **splunk_query**: Query Splunk logs (read-only)
3. **palo_alto_status**: Check firewall status
4. **grafana_fetch**: Fetch dashboard metrics
5. **create_ticket**: Hand off actions to VICTORIA

## Testing

Open `basic_frontend/index.html` in a browser to test the chat interface.

## Mock Mode

Without Azure AI configuration, SOPHIA runs in mock mode for development/testing.
