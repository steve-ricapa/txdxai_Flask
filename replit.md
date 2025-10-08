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
- **Ticket Creation**: Automatic ticket generation with severity, context, and metadata

#### Agent Model & Configuration
- **AgentInstance**: Stores per-company Azure configuration
  - `azure_openai_endpoint`: Company-specific OpenAI endpoint URL
  - `azure_openai_key_secret_id`: Key Vault reference to OpenAI API key
  - `azure_openai_deployment`: Model deployment (e.g., gpt-4o, gpt-4o-mini)
  - `azure_search_endpoint`: Company-specific Azure AI Search endpoint
  - `azure_search_key_secret_id`: Key Vault reference to search key
  - `azure_project_id`, `azure_agent_id`, `azure_vector_store_id`: Azure AI project references
- **Access Control**: 
  - ADMIN-only CRUD operations via `/admin/agent-instances` endpoints
  - Client apps authenticate via `/agents/auth/token` using company ID and access key
  - Backend retrieves Azure keys from Key Vault and returns with agent metadata
- **Security Pattern**:
  - Access keys generated using `secrets.token_urlsafe(32)` for strong entropy
  - Keys hashed with bcrypt (cost factor 12) before storage; plain text never persisted
  - Azure credentials stored in Key Vault; only secret IDs stored in database
  - Service JWT tokens issued with `agent:invoke` scope for authenticated clients
- **Key Rotation**: Administrators can rotate access keys via `/admin/agent-instances/{id}/rotate-key`
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
  - **Served via Flask**: Frontend served through Flask static folder on port 5000.
- **Production UI**: OpenAPI spec designed for import into VibeCode Workspace for web/mobile generation.

## External Dependencies

### Cloud Services
- **Azure Key Vault**: Secret storage and credential management.
  - SDK: `azure-keyvault-secrets`, `azure-identity`.
- **Azure Database for PostgreSQL**: Primary data store.

### Python Packages
- **Flask Ecosystem**: `Flask`, `Flask-SQLAlchemy`, `Flask-JWT-Extended`, `Flask-Migrate`, `Flask-CORS`, `Flasgger`.
- **Security & Cryptography**: `Werkzeug`, `azure-identity`, `azure-keyvault-secrets`.
- **Database**: `psycopg2` or `psycopg2-binary`, `SQLAlchemy`.

### Environment Configuration
- **Required Variables**: `DATABASE_URL`, `SESSION_SECRET`/`JWT_SECRET_KEY`, `AZURE_KEY_VAULT_URL`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `CORS_ORIGINS`.

### Security Providers
- Palo Alto Networks, Splunk, Wazuh, Cisco Meraki (via provider-specific SDKs or REST API clients).