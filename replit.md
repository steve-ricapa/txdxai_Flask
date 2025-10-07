# TxDxAI - Multi-Tenant Cybersecurity & Ticket Automation Platform

## Overview

TxDxAI is a Flask-based multi-tenant cybersecurity and ticket automation system designed for enterprise deployment on Azure. The platform enables companies to manage security tickets, integrate with external security providers (Palo Alto, Splunk, Wazuh, Meraki), and automate security workflows through AI agents. Each company operates in isolation with role-based access control (ADMIN and USER roles), where admins manage users and integrations while standard users consume services.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Framework**: Flask with modular blueprint architecture
- **Rationale**: Migrated from Spring Boot to Flask for simplified deployment and Python-native AI/ML integration
- **Structure**: Blueprint-based modular design with separate modules for auth, users, companies, tickets, integrations, and providers
- **API Documentation**: Flasgger/Swagger integration for OpenAPI specification generation

### Authentication & Authorization
- **Method**: JWT-based authentication using Flask-JWT-Extended
- **Token Strategy**: Access tokens (1 hour expiry) and refresh tokens (30 days expiry)
- **Role System**: Two-tier role model (ADMIN and USER) with company-level isolation
- **Authorization Pattern**: Decorator-based access control (`@admin_required`, `@same_company_required`) with current user context injection
- **Rationale**: JWT provides stateless authentication suitable for microservices and mobile clients

### Multi-Tenancy Design
- **Isolation Level**: Company-level data isolation with foreign key constraints
- **Data Model**: All primary entities (users, tickets, integrations, agent_sessions) include `company_id` for tenant separation
- **Access Control**: Query-level filtering ensures users only access their company's data
- **Admin Registration**: Self-service admin registration creates both company and initial admin user atomically

### Data Persistence
- **Database**: PostgreSQL (Azure Database for PostgreSQL)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy integration
- **Migration Management**: Alembic via Flask-Migrate for schema version control
- **Models**: 
  - `Company`: Tenant root entity
  - `User`: Authentication and authorization with role-based access
  - `Ticket`: Work item tracking with status workflow (PENDING → EXECUTED/FAILED/DERIVED)
  - `Integration`: External provider configuration with Key Vault references
  - `AgentSession` & `AgentMemoryRef`: AI agent conversation and memory management
  - `AuditLog`: Comprehensive activity tracking

### Secret Management
- **Service**: Azure Key Vault for all sensitive credentials
- **Pattern**: Integration records store only Key Vault secret identifiers, never actual credentials
- **Client**: Azure SDK with ClientSecretCredential for service principal authentication
- **Operations**: Abstracted through `keyvault.py` module (store_secret, retrieve_secret, delete_secret)
- **Rationale**: Separating secrets from database prevents credential exposure and enables centralized rotation

### Security Provider Integrations
- **Architecture**: Pluggable provider system with standardized execution interface
- **Providers**: Palo Alto, Splunk, Wazuh, Meraki (stub implementations for future development)
- **Pattern**: Each provider implements `execute_<provider>_action(credentials, action, params)` interface
- **Credential Flow**: Retrieve from Key Vault → Execute provider action → Return results
- **Extensibility**: New providers added by implementing the standard execution pattern

### Error Handling
- **Custom Exception Hierarchy**: `TxDxAIError` base class with specialized errors (UnauthorizedError, ForbiddenError, NotFoundError, ConflictError, ValidationError)
- **HTTP Status Mapping**: Exceptions automatically map to appropriate HTTP status codes
- **Centralized Handler**: Global error handler converts exceptions to JSON responses
- **Rationale**: Consistent error responses across all endpoints with proper status codes

### Audit & Compliance
- **Logging Strategy**: `AuditLog` table tracks all significant actions (user registration, ticket creation, integration changes)
- **Pattern**: `log_audit()` utility function called after state-changing operations
- **Data Captured**: Actor user, action type, entity type/ID, and JSON payload
- **Rationale**: Provides compliance trail and debugging capability for security-critical operations

### Cross-Origin Resource Sharing (CORS)
- **Configuration**: Flask-CORS with environment-configurable allowed origins
- **Default**: Localhost for development, production origins set via CORS_ORIGINS env var
- **Rationale**: Enables frontend applications on different domains to consume the API

### Frontend Strategy
- **Approach**: Minimal test interface in `/basic_frontend` for endpoint validation
- **Production UI**: OpenAPI spec designed for import into VibeCode Workspace for web/mobile generation
- **Rationale**: Separates API development from UI, enabling multiple client implementations

## External Dependencies

### Cloud Services
- **Azure Key Vault**: Secret storage and credential management
  - Authentication: Service Principal (Client ID, Client Secret, Tenant ID)
  - SDK: `azure-keyvault-secrets`, `azure-identity`
- **Azure Database for PostgreSQL**: Primary data store
  - Connection: SQLAlchemy with PostgreSQL driver
  - Configuration: `DATABASE_URL` environment variable

### Python Packages
- **Flask Ecosystem**:
  - `Flask`: Core web framework
  - `Flask-SQLAlchemy`: ORM integration
  - `Flask-JWT-Extended`: JWT authentication
  - `Flask-Migrate`: Database migrations via Alembic
  - `Flask-CORS`: Cross-origin request handling
  - `Flasgger`: OpenAPI/Swagger documentation generation

- **Security & Cryptography**:
  - `Werkzeug`: Password hashing (generate_password_hash, check_password_hash)
  - `azure-identity`: Azure authentication
  - `azure-keyvault-secrets`: Key Vault SDK

- **Database**:
  - `psycopg2` or `psycopg2-binary`: PostgreSQL adapter
  - `SQLAlchemy`: Database ORM

### Environment Configuration
- **Required Variables**:
  - `DATABASE_URL`: PostgreSQL connection string
  - `SESSION_SECRET`/`JWT_SECRET_KEY`: Token signing keys
  - `AZURE_KEY_VAULT_URL`: Key Vault endpoint
  - `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`: Azure authentication
  - `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

### Future Integrations (Placeholder)
- **Security Providers**: Palo Alto Networks, Splunk, Wazuh, Cisco Meraki
  - Implementation: Provider-specific SDKs or REST API clients
  - Authentication: Credentials stored in Key Vault
- **AI/ML Services**: Agent framework for ticket automation (placeholder in `/agents`)

## Project Structure

```
txdxai/
├── app.py                     # Main Flask application factory
├── config.py                  # Configuration management
├── run.py                     # Application entry point
├── extensions/                # Flask extensions initialization
│   └── __init__.py           # db, jwt, migrate, cors
├── auth/                      # Authentication module
│   ├── __init__.py
│   └── routes.py             # /auth/register, /auth/login
├── companies/                 # Company management
│   ├── __init__.py
│   └── routes.py             # CRUD for companies
├── users/                     # User management
│   ├── __init__.py
│   └── routes.py             # CRUD for users
├── tickets/                   # Ticket management
│   ├── __init__.py
│   └── routes.py             # CRUD for tickets
├── integrations/              # Integration management
│   ├── __init__.py
│   ├── routes.py             # CRUD for integrations
│   └── keyvault.py           # Azure Key Vault client
├── providers/                 # Security provider modules
│   ├── __init__.py
│   ├── splunk.py             # Splunk provider stub
│   ├── palo_alto.py          # Palo Alto provider stub
│   ├── wazuh.py              # Wazuh provider stub
│   └── meraki.py             # Meraki provider stub
├── agents/                    # AI agent base module (placeholder)
│   └── __init__.py
├── db/                        # Database models
│   ├── __init__.py
│   └── models.py             # SQLAlchemy models
├── common/                    # Common utilities
│   ├── __init__.py
│   ├── errors.py             # Custom exceptions
│   └── utils.py              # Helper functions
└── openapi/                   # API documentation
    └── openapi.yaml          # OpenAPI 3.0 specification

basic_frontend/                # Test interface
└── index.html                # HTML/JS API tester
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new ADMIN user and company
- `POST /api/auth/login` - Login with username/password

### Companies
- `GET /api/companies` - Get user's company
- `GET /api/companies/{id}` - Get company by ID
- `PUT /api/companies/{id}` - Update company (ADMIN only)

### Users
- `GET /api/users` - Get all users in company
- `GET /api/users/{id}` - Get user by ID
- `POST /api/users` - Create user (ADMIN only)
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user (ADMIN only)

### Tickets
- `GET /api/tickets` - Get all tickets (with optional status filter)
- `GET /api/tickets/{id}` - Get ticket by ID
- `POST /api/tickets` - Create ticket
- `PUT /api/tickets/{id}` - Update ticket
- `DELETE /api/tickets/{id}` - Delete ticket

### Integrations
- `GET /api/integrations` - Get all integrations
- `GET /api/integrations/{id}` - Get integration by ID
- `POST /api/integrations` - Create integration (ADMIN only)
- `PUT /api/integrations/{id}` - Update integration (ADMIN only)
- `DELETE /api/integrations/{id}` - Delete integration (ADMIN only)
- `GET /api/integrations/{id}/credentials` - Get credentials from Key Vault (ADMIN only)

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Azure Key Vault (optional, for production)

### Running the Application
```bash
# Install dependencies (already done in Replit)
uv sync

# Run the application
python run.py
```

The API will be available at `http://localhost:5000`
- Swagger UI documentation: `http://localhost:5000/api/docs`
- Basic test frontend: `http://localhost:5000/`

### Testing with Basic Frontend
1. Open the application in your browser
2. Register a new ADMIN user with your company name
3. The access token will be automatically saved
4. Test creating tickets, integrations, and users
5. All API responses will be displayed in the response section

### Azure Key Vault Setup (Production)
To enable Azure Key Vault integration, set these environment variables:
- `AZURE_KEY_VAULT_URL`
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`

## Recent Changes (October 2025)
- ✅ Complete backend implementation with Flask REST API
- ✅ Multi-tenant architecture with company isolation
- ✅ JWT authentication with ADMIN/USER roles
- ✅ PostgreSQL database with SQLAlchemy models
- ✅ Azure Key Vault integration for secure credential storage
- ✅ CRUD operations for companies, users, tickets, and integrations
- ✅ Audit logging system for compliance
- ✅ OpenAPI 3.0 specification for all endpoints
- ✅ Swagger UI documentation at /api/docs
- ✅ Basic HTML/JS test frontend
- ✅ Provider modules (Splunk, Palo Alto, Wazuh, Meraki) as stubs