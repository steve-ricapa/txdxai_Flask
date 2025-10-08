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
- **Architecture**: True multi-tenant design where each company has dedicated Azure credentials.
- **Separate Microservice**: Runs on port 8000, communicates with main backend (port 5000).
- **Agent Model**: `AgentInstance` stores per-company Azure configuration:
  - `azure_openai_endpoint`: Company-specific OpenAI endpoint URL
  - `azure_openai_key_secret_id`: Key Vault reference to OpenAI API key
  - `azure_openai_deployment`: Model deployment (e.g., gpt-4o, gpt-4o-mini)
  - `azure_search_endpoint`: Company-specific Azure AI Search endpoint
  - `azure_search_key_secret_id`: Key Vault reference to search key
  - `azure_project_id`, `azure_agent_id`, `azure_vector_store_id`: Azure AI project references
- **Access Control**: 
  - ADMIN-only CRUD operations via `/admin/agent-instances` endpoints.
  - Client apps authenticate via `/agents/auth/token` using company ID and access key.
  - Backend retrieves Azure keys from Key Vault and returns with agent metadata.
- **Security Pattern**:
  - Access keys generated using `secrets.token_urlsafe(32)` for strong entropy.
  - Keys hashed with bcrypt (cost factor 12) before storage; plain text never persisted.
  - Azure credentials stored in Key Vault; only secret IDs stored in database.
  - Service JWT tokens issued with `agent:invoke` scope for authenticated clients.
- **Key Rotation**: Administrators can rotate access keys via `/admin/agent-instances/{id}/rotate-key`.
- **Dynamic Agent Initialization**:
  - Orchestrator maintains separate `project_client` and `rag_tool` per company.
  - Agent configurations cached in memory with key `company-{company_id}`.
  - Azure AI Agents created on-demand using company-specific credentials.
- **Mock Mode Fallback**: Companies without Azure credentials run in mock mode with simulated responses.
- **Configuration Testing**: `/config/test` endpoint validates Azure credential setup status.
- **Backward Compatibility**: `/api/agents/instance/<id>` endpoint for legacy backends.
- **Status Management**: Instances can be ACTIVE, DISABLED, or TO_PROVISION.
- **Audit Trail**: All agent authentication and management actions logged to `AuditLog`.

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
- **Approach**: Minimal test interface for endpoint validation.
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