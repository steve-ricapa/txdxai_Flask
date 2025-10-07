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
- **Architecture**: Company-level agent instances with secure access key authentication.
- **Agent Model**: `AgentInstance` stores Azure AI project configuration and access credentials.
- **Access Control**: 
  - ADMIN-only CRUD operations via `/admin/agent-instances` endpoints.
  - Client apps authenticate via `/agents/auth/token` using company ID and access key.
- **Security Pattern**:
  - Access keys generated using `secrets.token_urlsafe(32)` for strong entropy.
  - Keys hashed with bcrypt (cost factor 12) before storage; plain text never persisted.
  - Service JWT tokens issued with `agent:invoke` scope for authenticated clients.
- **Key Rotation**: Administrators can rotate access keys via `/admin/agent-instances/{id}/rotate-key`.
- **Azure Integration**: Stores Azure AI project ID, agent ID, and vector store ID for each instance.
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