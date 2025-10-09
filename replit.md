# TxDxAI - Multi-Tenant Cybersecurity & Ticket Automation Platform

## Overview
TxDxAI is a Flask-based multi-tenant cybersecurity and ticket automation system designed for enterprise deployment on Azure. The platform aims to streamline security operations by enabling companies to manage security tickets, integrate with external security providers (Palo Alto, Splunk, Wazuh, Meraki), and automate security workflows using AI agents. Each company operates in isolation with role-based access control (ADMIN and USER roles), ensuring data segregation and secure management of services.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Framework**: Flask with modular blueprint architecture.
- **Structure**: Blueprint-based modular design for authentication, users, companies, tickets, integrations, and providers.
- **API Documentation**: Flasgger/Swagger for OpenAPI specification generation.

### Authentication & Authorization
- **Method**: JWT-based authentication using Flask-JWT-Extended.
- **Role System**: Two-tier role model (ADMIN and USER) with company-level isolation.
- **Authorization Pattern**: Decorator-based access control (`@admin_required`, `@same_company_required`).

### Multi-Tenancy Design
- **Isolation Level**: Company-level data isolation enforced with foreign key constraints.
- **Data Model**: All primary entities include `company_id` for tenant separation.
- **Access Control**: Query-level filtering to ensure users only access their company's data.

### Data Persistence
- **Database**: PostgreSQL (Azure Database for PostgreSQL).
- **ORM**: SQLAlchemy with Flask-SQLAlchemy.
- **Migration Management**: Alembic via Flask-Migrate.
- **Connection Pool**: Configured with `pool_pre_ping=True` and `pool_recycle=300` to handle SSL disconnects gracefully.
- **Models**: `Company`, `User`, `Ticket`, `Integration`, `System`, `Alert`, `Vulnerability`, `AgentInstance`, `AgentSession`, `AgentMemoryRef`, `AuditLog`.

### Secret Management
- **Service**: Azure Key Vault for all sensitive credentials.
- **Pattern**: Integration records store Key Vault secret identifiers; actual credentials are never stored in the database.
- **Client**: Azure SDK with ClientSecretCredential.

### Security Provider Integrations
- **Architecture**: Pluggable provider system with a standardized execution interface.
- **Providers**: Palo Alto, Splunk, Wazuh, Meraki, Grafana.
- **Pattern**: Each provider implements `execute_<provider>_action(credentials, action, params)`.
- **Data Normalization**: `common/normalizer.py` standardizes multi-provider responses.

### SOPHIA AI Agent System
- **Purpose**: Multi-tenant AI agent provisioning for automation and security workflows.
- **Architecture**: Modular design with intent routing and VictorIA handoff capabilities.
- **Separate Microservice**: Runs on port 8000, communicates with main backend (port 5000).

#### Modular Architecture (v2.0)
- **sophia/agent_loader.py**: Dynamic per-tenant agent initialization with Azure AI integration
  - Initializes agents with company-specific Azure credentials
  - Maintains separate RAG tools per company
  - Supports both Azure AI mode and mock mode fallback
- **sophia/memory.py**: Session and conversation thread management
  - Creates and manages conversation threads per company/user
  - Stores message history with timestamps
  - Thread-based context retrieval
- **sophia/rag_tools.py**: RAG (Retrieval-Augmented Generation) with Azure AI Search
  - Integrates with Azure AI Search for knowledge retrieval
  - Mock search fallback when credentials unavailable
  - Context formatting for LLM consumption
- **sophia/intent_router.py**: Intent detection and routing
  - Detects query vs action intents from user messages
  - Identifies high-risk actions requiring VictorIA escalation
  - Extracts parameters from user requests (IPs, device names, severity)
- **sophia/handoff.py**: VictorIA integration for action escalation
  - Creates ticket stubs for manual review
  - Determines ticket severity based on action type
  - Provides user-friendly escalation messages
- **sophia/mock_integrations.py**: Security tool integrations
  - Mock responses from Palo Alto, Splunk, Grafana, Wazuh, Meraki
  - Simulates security tool data for testing
  - Security action execution with escalation flags

#### VictorIA Integration
- **victor/ticket_models.py**: Data models for tickets and action requests
- **victor/client_stub.py**: VictorIA client stub for ticket handoff
- **Handoff Pattern**: High-risk actions (block_ip, quarantine_device, etc.) automatically escalate to VictorIA
- **Ticket Creation**: Backend PostgreSQL assigns unique ticket IDs (autoincremental)
  - SOPHIA calls `/api/tickets/agent-create` with agent JWT token
  - Backend creates ticket and returns unique ID
  - VictorIA receives ticket with backend-assigned ID
  - No ID collisions: PostgreSQL guarantees uniqueness

#### Agent Model & Configuration
- **AgentInstance**: Stores per-company Azure configuration
  - `azure_openai_endpoint`: Company-specific OpenAI endpoint URL
  - `azure_openai_key_secret_id`: Key Vault reference to OpenAI API key
  - `azure_openai_deployment`: Model deployment (e.g., gpt-4o, gpt-4o-mini)
  - `azure_search_endpoint`: Company-specific Azure AI Search endpoint
  - `azure_search_key_secret_id`: Key Vault reference to search key
  - `azure_speech_endpoint`: Company-specific Azure Speech endpoint
  - `azure_speech_key_secret_id`: Key Vault reference to Speech API key
  - `azure_speech_region`: Azure region for Speech service (e.g., eastus, westeurope)
  - `azure_speech_voice_name`: Spanish voice for TTS (default: es-ES-ElviraNeural)
  - `azure_project_id`, `azure_agent_id`, `azure_vector_store_id`: Azure AI project references
- **Access Control**: 
  - ADMIN-only CRUD operations via `/admin/agent-instances` endpoints
  - Client apps authenticate via `/agents/auth/token` using company ID and access key
  - Backend retrieves Azure keys from Key Vault and returns with agent metadata
- **Security Pattern**:
  - Access keys generated using `secrets.token_urlsafe(32)` for strong entropy
  - Keys hashed with bcrypt (cost factor 12) before storage; plain text never persisted
  - **Multi-Device Support**: Access keys also stored encrypted (AES-256 Fernet) for recovery
    - `client_access_key_encrypted` field stores Fernet-encrypted key
    - Encryption key persisted in `AGENT_KEY_ENCRYPTION_KEY` environment variable
    - Enables key recovery on new devices without recreating agent instance
  - Azure credentials stored in Key Vault; only secret IDs stored in database
  - Service JWT tokens issued with `agent:invoke` scope for authenticated clients
- **Key Management**:
  - **Key Recovery**: `GET /api/admin/agent-instances/{id}/access-key` - Retrieve encrypted access key (ADMIN only)
  - **Key Rotation**: `POST /api/admin/agent-instances/{id}/rotate-key` - Generate new access key and invalidate old one
- **Dynamic Agent Initialization**:
  - Agent loader maintains separate configurations per company
  - Agent configurations cached in memory with key `company-{company_id}`
  - Azure AI Agents created on-demand using company-specific credentials
- **Mock Mode Fallback**: Companies without Azure credentials run in mock mode with simulated responses
- **Configuration Testing**: `/config/test` endpoint validates Azure credential setup status
- **Backward Compatibility**: `/api/agents/instance/<id>` endpoint for legacy backends
- **Status Management**: Instances can be ACTIVE, DISABLED, or TO_PROVISION
- **Audit Trail**: All agent authentication and management actions logged to `AuditLog`

#### API Endpoints
- `/health`: Health check with architecture info
- `/chat`: Main chat endpoint with intent routing
- `/threads/<id>`: Get or delete conversation threads
- `/config/test`: Test Azure configuration
- `/cache/stats`: Cache statistics
- `/cache/invalidate`: Invalidate company cache

### Voice/Speech Integration
- **Service**: Azure Cognitive Services Speech SDK for multilingual voice interaction.
- **Architecture**: Multi-tenant voice input/output with company-specific Azure Speech credentials.
- **Module**: `common/speech_service.py` provides STT (Speech-to-Text) and TTS (Text-to-Speech) functions.

#### Speech-to-Text (STT)
- **Function**: `transcribe_audio(audio_data, speech_config)` - Converts audio to Spanish text
- **Endpoint**: `POST /api/voice/transcribe`
  - Accepts audio file (WebM format from browser MediaRecorder)
  - Validates company credentials and retrieves Speech key from Key Vault
  - Returns JSON: `{"text": "transcribed_text", "status": "success"}`
- **Audio Format**: Browser-captured WebM, converted internally for Azure compatibility
- **Language**: Spanish (es-ES) for recognition

#### Text-to-Speech (TTS)
- **Function**: `synthesize_speech(text, speech_config, voice_name)` - Converts text to Spanish audio
- **Endpoint**: `POST /api/voice/speak`
  - Accepts JSON: `{"text": "response_text", "companyId": 1, "agentAccessKey": "key"}`
  - Validates company credentials and retrieves Speech key from Key Vault
  - Streams MP3 audio at 16kHz for optimal quality
- **Voice**: Configurable per company, default `es-ES-ElviraNeural` (Spanish female voice)
- **Audio Format**: MP3, streamed directly to client for playback

#### Security & Multi-Tenancy
- **Authentication**: Agent access key validation per company
- **Credential Retrieval**: Speech keys fetched from Azure Key Vault using secret IDs
- **Isolation**: Each company uses their own Azure Speech endpoint and credentials
- **Error Handling**: Structured responses with Spanish error messages for user clarity
- **Temporary Files**: Audio processing files cleaned up automatically after synthesis

### Error Handling
- **Custom Exception Hierarchy**: `TxDxAIError` base class with specialized exceptions.
- **HTTP Status Mapping**: Exceptions map to appropriate HTTP status codes.
- **Centralized Handler**: Global error handler converts exceptions to JSON responses.

### Audit & Compliance
- **Logging Strategy**: `AuditLog` table tracks all significant actions.
- **Pattern**: `log_audit()` utility function captures actor, action type, entity, and JSON payload.

### Cross-Origin Resource Sharing (CORS)
- **Configuration**: Flask-CORS with environment-configurable allowed origins.

### Frontend Strategy
- **Basic Admin Interface**: Vanilla HTML/CSS/JavaScript frontend in `/basic_frontend/` for SOPHIA configuration and testing.
  - **Registration/Login**: User registration with company creation, JWT authentication with localStorage persistence.
  - **Agent Management**: Create and configure Azure credentials for SOPHIA agent instances.
  - **Live Chat**: Interactive chat interface with SOPHIA using company ID and access key.
  - **Voice Controls**: 
    - 🎤 Record button - Captures audio using MediaRecorder API, sends to `/api/voice/transcribe`
    - 🔊 Play button - Synthesizes SOPHIA responses via `/api/voice/speak` and plays audio
    - Real-time status updates for recording, transcription, and playback
    - Spanish voice interaction for accessible user experience
  - **Served via Flask**: Frontend served through Flask static folder on port 5000.
  - **Frontend Access**: 
    - Health check / API root: `/` (returns JSON status)
    - Frontend UI: `/index.html`
    - JavaScript: `/script.js`
- **Production UI**: OpenAPI spec designed for import into VibeCode Workspace for web/mobile generation.

## Deployment

### Production Deployment (Replit VM)
- **Type**: VM Deployment (stateful, always-running)
- **Command**: `bash start_services.sh`
- **Services**:
  - Backend API: Gunicorn on port 5000 (2 workers)
  - SOPHIA Service: Gunicorn on port 8000 (2 workers)
- **Health Check**: `GET /` returns JSON `{"status": "healthy", "service": "TxDxAI", "version": "1.0.0"}`
- **Frontend**: Accessible at `/index.html`
- **Security**: 
  - DEBUG mode disabled in production (config default: False)
  - Gunicorn WSGI server (production-grade)
  - All services bind to `0.0.0.0` for external access

### Development
- **Backend**: `python run.py` or `flask run`
- **SOPHIA**: `python sophia_service/app.py`
- **Combined**: `bash start_services.sh`

## External Dependencies

### Cloud Services
- **Azure Key Vault**: Secret storage and credential management.
  - SDK: `azure-keyvault-secrets`, `azure-identity`.
- **Azure Database for PostgreSQL**: Primary data store.

### Python Packages
- **Flask Ecosystem**: `Flask`, `Flask-SQLAlchemy`, `Flask-JWT-Extended`, `Flask-Migrate`, `Flask-CORS`, `Flasgger`.
- **Security & Cryptography**: `Werkzeug`, `azure-identity`, `azure-keyvault-secrets`.
- **Database**: `psycopg2` or `psycopg2-binary`, `SQLAlchemy`.
- **Azure Cognitive Services**: `azure-cognitiveservices-speech` for voice/speech functionality.

### Environment Configuration
- **Required Variables**: `DATABASE_URL`, `SESSION_SECRET`/`JWT_SECRET_KEY`, `AZURE_KEY_VAULT_URL`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `CORS_ORIGINS`.

### Security Providers
- Palo Alto Networks, Splunk, Wazuh, Cisco Meraki (via provider-specific SDKs or REST API clients).