# TxDxAI - API Documentation

## 📋 Tabla de Contenidos

- [Información General](#información-general)
- [Arquitectura](#arquitectura)
- [Autenticación](#autenticación)
- [Backend API (Puerto 5000)](#backend-api-puerto-5000)
  - [Autenticación](#endpoints-de-autenticación)
  - [Empresas](#endpoints-de-empresas)
  - [Usuarios](#endpoints-de-usuarios)
  - [Tickets](#endpoints-de-tickets)
  - [Integraciones](#endpoints-de-integraciones)
  - [Sistemas](#endpoints-de-sistemas)
  - [Alertas](#endpoints-de-alertas)
  - [Vulnerabilidades](#endpoints-de-vulnerabilidades)
  - [Analíticas](#endpoints-de-analíticas)
  - [Administración de Agentes](#endpoints-de-administración-de-agentes)
  - [Autenticación de Agentes](#endpoints-de-autenticación-de-agentes)
  - [Voz](#endpoints-de-voz)
- [SOPHIA API (Puerto 8000)](#sophia-api-puerto-8000)
- [Modelos de Datos](#modelos-de-datos)
- [Códigos de Estado HTTP](#códigos-de-estado-http)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Variables de Entorno](#variables-de-entorno)

---

## Información General

**TxDxAI** es una plataforma multi-tenant de ciberseguridad y automatización de tickets diseñada para despliegue empresarial en Azure. El sistema permite a las empresas gestionar tickets de seguridad, integrar proveedores externos (Palo Alto, Splunk, Wazuh, Meraki) y automatizar flujos de trabajo de seguridad usando agentes de IA.

### Características Principales

- ✅ **Multi-tenancy**: Aislamiento completo de datos a nivel de empresa
- 🔐 **Autenticación JWT**: Sistema seguro de autenticación basado en tokens
- 👥 **Control de Acceso por Roles**: ADMIN y USER con permisos diferenciados
- 🔑 **Azure Key Vault**: Gestión segura de credenciales y secretos
- 🤖 **SOPHIA AI Agent**: Asistente IA para automatización de seguridad
- 🎤 **Integración de Voz**: Speech-to-Text y Text-to-Speech en español
- 📊 **Analíticas en Tiempo Real**: Métricas de seguridad e incidentes

---

## Arquitectura

### Stack Tecnológico

- **Backend**: Flask (Python) con arquitectura modular de Blueprints
- **Base de Datos**: PostgreSQL con SQLAlchemy ORM
- **Autenticación**: Flask-JWT-Extended
- **Gestión de Secretos**: Azure Key Vault
- **IA**: Azure OpenAI, Azure AI Search, Azure Speech Services
- **Frontend**: Vanilla HTML/CSS/JavaScript (básico para testing)

### Microservicios

1. **Backend Principal** (Puerto 5000): API REST para gestión de recursos
2. **SOPHIA Service** (Puerto 8000): Microservicio de IA con arquitectura modular

---

## Autenticación

El sistema utiliza **JWT (JSON Web Tokens)** para autenticación. Todos los endpoints protegidos requieren un token de acceso en el header:

```
Authorization: Bearer <access_token>
```

### Obtener Token

Los tokens se obtienen mediante los endpoints de autenticación (`/api/auth/register` o `/api/auth/login`).

### Roles

- **ADMIN**: Acceso completo a todos los recursos de su empresa
- **USER**: Acceso limitado a recursos específicos

---

## Backend API (Puerto 5000)

Base URL: `http://localhost:5000`

### Endpoints de Autenticación

#### POST /api/auth/register

Registra un nuevo usuario administrador y crea una nueva empresa.

**Request Body:**
```json
{
  "company_name": "TechCorp Inc.",
  "username": "admin",
  "email": "admin@techcorp.com",
  "password": "SecurePassword123"
}
```

**Response (201):**
```json
{
  "message": "Admin user registered successfully",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@techcorp.com",
    "role": "ADMIN",
    "company": {
      "id": 1,
      "name": "TechCorp Inc."
    }
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST /api/auth/login

Inicia sesión con credenciales existentes.

**Request Body:**
```json
{
  "username": "admin",
  "password": "SecurePassword123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@techcorp.com",
    "role": "ADMIN",
    "company": {
      "id": 1,
      "name": "TechCorp Inc."
    }
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Endpoints de Empresas

#### GET /api/companies

Obtiene la lista de empresas (solo la empresa del usuario actual).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "companies": [
    {
      "id": 1,
      "name": "TechCorp Inc.",
      "created_at": "2025-10-08T10:30:00Z"
    }
  ]
}
```

#### GET /api/companies/{company_id}

Obtiene detalles de una empresa específica.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "name": "TechCorp Inc.",
  "created_at": "2025-10-08T10:30:00Z"
}
```

#### PUT /api/companies/{company_id}

Actualiza información de la empresa (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "TechCorp International"
}
```

**Response (200):**
```json
{
  "message": "Company updated successfully",
  "company": {
    "id": 1,
    "name": "TechCorp International",
    "created_at": "2025-10-08T10:30:00Z"
  }
}
```

---

### Endpoints de Usuarios

#### GET /api/users

Obtiene todos los usuarios de la empresa.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@techcorp.com",
      "role": "ADMIN",
      "created_at": "2025-10-08T10:30:00Z"
    },
    {
      "id": 2,
      "username": "user1",
      "email": "user1@techcorp.com",
      "role": "USER",
      "created_at": "2025-10-08T11:00:00Z"
    }
  ]
}
```

#### GET /api/users/{user_id}

Obtiene detalles de un usuario específico.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@techcorp.com",
  "role": "ADMIN",
  "created_at": "2025-10-08T10:30:00Z"
}
```

#### POST /api/users

Crea un nuevo usuario (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@techcorp.com",
  "password": "SecurePass123",
  "role": "USER"
}
```

**Response (201):**
```json
{
  "message": "User created successfully",
  "user": {
    "id": 3,
    "username": "newuser",
    "email": "newuser@techcorp.com",
    "role": "USER",
    "created_at": "2025-10-08T12:00:00Z"
  }
}
```

#### PUT /api/users/{user_id}

Actualiza información de un usuario.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "email": "updated@techcorp.com",
  "role": "ADMIN"
}
```

**Response (200):**
```json
{
  "message": "User updated successfully",
  "user": {
    "id": 3,
    "username": "newuser",
    "email": "updated@techcorp.com",
    "role": "ADMIN",
    "updated_at": "2025-10-08T13:00:00Z"
  }
}
```

#### DELETE /api/users/{user_id}

Elimina un usuario (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

---

### Endpoints de Tickets

#### GET /api/tickets

Obtiene todos los tickets de la empresa.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (opcional): Filtra por estado (PENDING, EXECUTED, FAILED, DERIVED)

**Response (200):**
```json
{
  "tickets": [
    {
      "id": 1,
      "subject": "Bloquear IP maliciosa",
      "description": "Detectada actividad sospechosa desde 192.168.1.100",
      "status": "PENDING",
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-10-08T14:00:00Z"
    }
  ]
}
```

#### GET /api/tickets/{ticket_id}

Obtiene detalles de un ticket específico.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "subject": "Bloquear IP maliciosa",
  "description": "Detectada actividad sospechosa desde 192.168.1.100",
  "status": "PENDING",
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-10-08T14:00:00Z",
  "updated_at": "2025-10-08T14:30:00Z"
}
```

#### POST /api/tickets

Crea un nuevo ticket.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "subject": "Bloquear IP maliciosa",
  "description": "Detectada actividad sospechosa desde 192.168.1.100"
}
```

**Response (201):**
```json
{
  "message": "Ticket created successfully",
  "ticket": {
    "id": 1,
    "subject": "Bloquear IP maliciosa",
    "description": "Detectada actividad sospechosa desde 192.168.1.100",
    "status": "PENDING",
    "created_at": "2025-10-08T14:00:00Z"
  }
}
```

#### PUT /api/tickets/{ticket_id}

Actualiza un ticket existente.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "subject": "Bloquear IP maliciosa - Actualizado",
  "status": "EXECUTED"
}
```

**Response (200):**
```json
{
  "message": "Ticket updated successfully",
  "ticket": {
    "id": 1,
    "subject": "Bloquear IP maliciosa - Actualizado",
    "status": "EXECUTED",
    "updated_at": "2025-10-08T15:00:00Z"
  }
}
```

#### DELETE /api/tickets/{ticket_id}

Elimina un ticket (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Ticket deleted successfully"
}
```

#### POST /api/tickets/agent-create

Crea un ticket desde el agente SOPHIA (autenticación especial).

**Headers:**
```
Authorization: Bearer <agent_jwt_token>
```

**Request Body:**
```json
{
  "subject": "Acción de seguridad: Bloquear IP",
  "description": "SOPHIA recomienda bloquear la IP 192.168.1.100",
  "metadata": {
    "action": "block_ip",
    "ip": "192.168.1.100",
    "severity": "HIGH"
  }
}
```

**Response (201):**
```json
{
  "success": true,
  "ticket_id": 1,
  "ticket": {
    "id": 1,
    "subject": "Acción de seguridad: Bloquear IP",
    "status": "PENDING",
    "created_at": "2025-10-08T14:00:00Z"
  }
}
```

---

### Endpoints de Integraciones

#### GET /api/integrations

Obtiene todas las integraciones de seguridad de la empresa.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "integrations": [
    {
      "id": 1,
      "provider": "palo_alto",
      "keyvault_secret_id": "https://vault.azure.net/secrets/palo-alto-key",
      "extra_json": {},
      "created_at": "2025-10-08T10:00:00Z"
    }
  ]
}
```

#### GET /api/integrations/{integration_id}

Obtiene detalles de una integración específica.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "provider": "palo_alto",
  "keyvault_secret_id": "https://vault.azure.net/secrets/palo-alto-key",
  "extra_json": {},
  "created_at": "2025-10-08T10:00:00Z"
}
```

#### POST /api/integrations

Crea una nueva integración (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "provider": "palo_alto",
  "credentials": {
    "api_key": "YOUR_API_KEY",
    "endpoint": "https://firewall.company.com"
  },
  "extra_json": {
    "region": "us-east-1"
  }
}
```

**Proveedores soportados:**
- `palo_alto`: Palo Alto Networks
- `splunk`: Splunk SIEM
- `wazuh`: Wazuh Security Platform
- `meraki`: Cisco Meraki

**Response (201):**
```json
{
  "message": "Integration created successfully",
  "integration": {
    "id": 1,
    "provider": "palo_alto",
    "keyvault_secret_id": "https://vault.azure.net/secrets/palo-alto-key",
    "created_at": "2025-10-08T10:00:00Z"
  }
}
```

#### PUT /api/integrations/{integration_id}

Actualiza una integración existente (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "credentials": {
    "api_key": "NEW_API_KEY",
    "endpoint": "https://firewall.company.com"
  }
}
```

**Response (200):**
```json
{
  "message": "Integration updated successfully",
  "integration": {
    "id": 1,
    "provider": "palo_alto",
    "updated_at": "2025-10-08T11:00:00Z"
  }
}
```

#### DELETE /api/integrations/{integration_id}

Elimina una integración (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Integration deleted successfully"
}
```

#### GET /api/integrations/{integration_id}/credentials

Obtiene las credenciales de una integración desde Azure Key Vault (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "credentials": {
    "api_key": "YOUR_API_KEY",
    "endpoint": "https://firewall.company.com"
  }
}
```

---

### Endpoints de Sistemas

#### GET /api/systems/status

Obtiene resumen del estado de todos los sistemas.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "total_systems": 15,
  "online": 12,
  "offline": 2,
  "degraded": 1,
  "unknown": 0,
  "average_health_score": 87.5
}
```

#### GET /api/systems

Obtiene lista completa de sistemas.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "systems": [
    {
      "id": 1,
      "name": "Web Server 1",
      "status": "online",
      "health_score": 95,
      "last_check": "2025-10-08T15:00:00Z"
    }
  ]
}
```

#### GET /api/systems/{system_id}

Obtiene detalles de un sistema específico.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Web Server 1",
  "status": "online",
  "health_score": 95,
  "last_check": "2025-10-08T15:00:00Z",
  "metadata": {
    "cpu_usage": 45,
    "memory_usage": 60
  }
}
```

---

### Endpoints de Alertas

#### GET /api/alerts/active

Obtiene alertas activas de seguridad.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `since` (opcional): Timestamp ISO 8601 para filtrar alertas desde una fecha
- `limit` (opcional): Límite de resultados (default: 100)

**Response (200):**
```json
{
  "alerts": [
    {
      "id": 1,
      "title": "Actividad sospechosa detectada",
      "severity": "high",
      "status": "active",
      "created_at": "2025-10-08T14:30:00Z",
      "source": "Palo Alto Firewall"
    }
  ]
}
```

#### POST /api/alerts/{alert_id}/resolve

Marca una alerta como resuelta.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Alert resolved successfully",
  "alert": {
    "id": 1,
    "title": "Actividad sospechosa detectada",
    "status": "resolved",
    "resolved_at": "2025-10-08T15:00:00Z",
    "resolved_by": 1
  }
}
```

---

### Endpoints de Vulnerabilidades

#### GET /api/vulnerabilities

Obtiene vulnerabilidades detectadas.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `status` (opcional): Filtra por estado (open, patching, resolved)
- `severity` (opcional): Filtra por severidad (critical, high, medium, low)

**Response (200):**
```json
{
  "vulnerabilities": [
    {
      "id": 1,
      "cve_id": "CVE-2024-1234",
      "severity": "critical",
      "status": "open",
      "affected_system": "Web Server 1",
      "created_at": "2025-10-08T10:00:00Z"
    }
  ]
}
```

#### GET /api/vulnerabilities/{vuln_id}

Obtiene detalles de una vulnerabilidad específica.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "cve_id": "CVE-2024-1234",
  "severity": "critical",
  "status": "open",
  "affected_system": "Web Server 1",
  "description": "Vulnerabilidad de ejecución remota de código",
  "patch_available": true,
  "created_at": "2025-10-08T10:00:00Z"
}
```

#### POST /api/vulnerabilities/{vuln_id}/patch

Inicia el proceso de parcheo de una vulnerabilidad.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Patch process initiated",
  "vulnerability": {
    "id": 1,
    "cve_id": "CVE-2024-1234",
    "status": "patching",
    "patch_status": "initiated"
  }
}
```

---

### Endpoints de Analíticas

#### GET /api/analytics/incidents

Obtiene analíticas de incidentes.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `hours` (opcional): Período de análisis en horas (default: 24)

**Response (200):**
```json
{
  "period_hours": 24,
  "total_incidents": 15,
  "by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 6,
    "low": 2
  },
  "timestamp": "2025-10-08T15:00:00Z"
}
```

#### GET /api/analytics/response-time

Obtiene analíticas de tiempo de respuesta.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `days` (opcional): Período de análisis en días (default: 7)

**Response (200):**
```json
{
  "period_days": 7,
  "average_response_time_minutes": 45.5,
  "total_resolved_alerts": 120,
  "timestamp": "2025-10-08T15:00:00Z"
}
```

#### GET /api/analytics/vulnerability-distribution

Obtiene distribución de vulnerabilidades.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "severity_distribution": {
    "critical": 5,
    "high": 12,
    "medium": 25,
    "low": 8
  },
  "total_open_vulnerabilities": 50,
  "timestamp": "2025-10-08T15:00:00Z"
}
```

#### GET /api/analytics/summary

Obtiene resumen general de métricas.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "total_alerts": 150,
  "active_alerts": 12,
  "total_systems": 15,
  "systems_online": 12,
  "total_vulnerabilities": 50,
  "critical_vulnerabilities": 5,
  "average_response_time_minutes": 45.5,
  "timestamp": "2025-10-08T15:00:00Z"
}
```

---

### Endpoints de Administración de Agentes

#### POST /api/admin/agent-instances

Crea una nueva instancia del agente SOPHIA (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "agentType": "SOPHIA",
  "azureProjectId": "project-123",
  "azureAgentId": "agent-456",
  "azureVectorStoreId": "vector-789",
  "azureOpenaiEndpoint": "https://openai.azure.com",
  "azureOpenaiKey": "YOUR_OPENAI_KEY",
  "azureOpenaiDeployment": "gpt-4o",
  "azureSearchEndpoint": "https://search.azure.com",
  "azureSearchKey": "YOUR_SEARCH_KEY",
  "azureSpeechEndpoint": "https://speech.azure.com",
  "azureSpeechKey": "YOUR_SPEECH_KEY",
  "azureSpeechRegion": "eastus",
  "azureSpeechVoiceName": "es-ES-ElviraNeural",
  "region": "us-east-1"
}
```

**Response (201):**
```json
{
  "message": "Agent instance created successfully",
  "access_key": "generated-access-key-here",
  "agent_instance": {
    "id": "uuid-here",
    "company_id": 1,
    "agent_type": "SOPHIA",
    "status": "ACTIVE",
    "created_at": "2025-10-08T10:00:00Z"
  }
}
```

#### GET /api/admin/agent-instances

Obtiene todas las instancias de agentes de la empresa (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "agent_instances": [
    {
      "id": "uuid-here",
      "company_id": 1,
      "agent_type": "SOPHIA",
      "status": "ACTIVE",
      "azure_openai_endpoint": "https://openai.azure.com",
      "azure_openai_deployment": "gpt-4o",
      "created_at": "2025-10-08T10:00:00Z",
      "last_used_at": "2025-10-08T15:00:00Z"
    }
  ]
}
```

#### GET /api/admin/agent-instances/{instance_id}

Obtiene detalles de una instancia de agente (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "uuid-here",
  "company_id": 1,
  "agent_type": "SOPHIA",
  "status": "ACTIVE",
  "azure_openai_endpoint": "https://openai.azure.com",
  "azure_openai_deployment": "gpt-4o",
  "azure_search_endpoint": "https://search.azure.com",
  "azure_speech_endpoint": "https://speech.azure.com",
  "azure_speech_region": "eastus",
  "azure_speech_voice_name": "es-ES-ElviraNeural",
  "created_at": "2025-10-08T10:00:00Z"
}
```

#### PATCH /api/admin/agent-instances/{instance_id}

Actualiza una instancia de agente (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "azureOpenaiDeployment": "gpt-4o-mini",
  "azureSpeechVoiceName": "es-ES-AlvaroNeural"
}
```

**Response (200):**
```json
{
  "message": "Agent instance updated successfully",
  "agent_instance": {
    "id": "uuid-here",
    "azure_openai_deployment": "gpt-4o-mini",
    "azure_speech_voice_name": "es-ES-AlvaroNeural",
    "updated_at": "2025-10-08T16:00:00Z"
  }
}
```

#### POST /api/admin/agent-instances/{instance_id}/rotate-key

Rota la clave de acceso del agente (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Access key rotated successfully",
  "new_access_key": "new-generated-key-here"
}
```

#### DELETE /api/admin/agent-instances/{instance_id}

Desactiva una instancia de agente (solo ADMIN).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Agent instance disabled successfully"
}
```

---

### Endpoints de Autenticación de Agentes

#### POST /api/agents/auth/token

Autentica un agente y obtiene token de acceso (para aplicaciones cliente).

**Request Body:**
```json
{
  "companyId": 1,
  "agentType": "SOPHIA",
  "agentAccessKey": "your-access-key"
}
```

**Response (200):**
```json
{
  "access_token": "agent-jwt-token",
  "agent_instance_id": "uuid-here",
  "agent_instance": {
    "id": "uuid-here",
    "agent_type": "SOPHIA",
    "azure_openai_endpoint": "https://openai.azure.com",
    "azure_openai_deployment": "gpt-4o",
    "azure_search_endpoint": "https://search.azure.com"
  }
}
```

#### GET /api/agents/instance/{instance_id}

Obtiene detalles de una instancia de agente (endpoint legacy).

**Response (200):**
```json
{
  "id": "uuid-here",
  "company_id": 1,
  "agent_type": "SOPHIA",
  "azure_openai_endpoint": "https://openai.azure.com",
  "azure_openai_deployment": "gpt-4o"
}
```

---

### Endpoints de Voz

#### POST /api/voice/transcribe

Convierte audio a texto (Speech-to-Text) en español.

**Content-Type:** `multipart/form-data`

**Form Data:**
- `audio`: Archivo de audio (WAV, MP3, OGG, M4A, FLAC, WEBM)
- `companyId`: ID de la empresa
- `agentAccessKey`: Clave de acceso del agente

**Response (200):**
```json
{
  "text": "Hola SOPHIA, necesito bloquear la IP 192.168.1.100",
  "status": "success"
}
```

**Formatos de audio soportados:**
- WAV, MP3, OGG, M4A, FLAC
- WEBM (convertido automáticamente a WAV usando ffmpeg)

#### POST /api/voice/speak

Convierte texto a audio (Text-to-Speech) en español.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "text": "He recibido tu solicitud y procederé a bloquear la IP",
  "companyId": 1,
  "agentAccessKey": "your-access-key"
}
```

**Response (200):**
- Content-Type: `audio/mpeg`
- Archivo MP3 a 16kHz con voz en español

**Voces disponibles (configurables por empresa):**
- `es-ES-ElviraNeural` (mujer, por defecto)
- `es-ES-AlvaroNeural` (hombre)
- Otras voces de Azure Speech Services en español

---

## SOPHIA API (Puerto 8000)

Base URL: `http://localhost:8000`

### GET /health

Health check del servicio SOPHIA.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "SOPHIA",
  "version": "2.0.0",
  "architecture": "modular",
  "azure_ai_configured": true,
  "config": {
    "backend_url": "http://localhost:5000/api",
    "mode": "azure_ai"
  }
}
```

### POST /chat

Interactúa con el agente SOPHIA.

**Request Body:**
```json
{
  "companyId": 1,
  "userId": 1,
  "agentAccessKey": "your-access-key",
  "message": "¿Cuáles son las alertas críticas activas?",
  "threadId": "thread-uuid" 
}
```

**Response (200):**
```json
{
  "response": "Actualmente tienes 2 alertas críticas: ...",
  "threadId": "thread-uuid",
  "intent": "query",
  "metadata": {
    "sources": ["Palo Alto", "Splunk"]
  }
}
```

**Tipos de Intent:**
- `query`: Consulta de información
- `action`: Acción de seguridad (puede generar ticket en VictorIA)

### GET /threads/{thread_id}

Obtiene el historial de un hilo de conversación.

**Response (200):**
```json
{
  "thread_id": "thread-uuid",
  "company_id": 1,
  "messages": [
    {
      "role": "user",
      "content": "¿Cuáles son las alertas críticas?",
      "timestamp": "2025-10-08T14:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Tienes 2 alertas críticas...",
      "timestamp": "2025-10-08T14:00:05Z"
    }
  ],
  "created_at": "2025-10-08T14:00:00Z"
}
```

### DELETE /threads/{thread_id}

Elimina un hilo de conversación.

**Response (200):**
```json
{
  "message": "Thread deleted successfully"
}
```

### GET /config/test

Verifica la configuración de Azure del agente.

**Query Parameters:**
- `companyId`: ID de la empresa

**Response (200):**
```json
{
  "status": "configured",
  "azure_openai": true,
  "azure_search": true,
  "azure_speech": true,
  "mode": "azure_ai"
}
```

### GET /cache/stats

Obtiene estadísticas del caché de agentes.

**Response (200):**
```json
{
  "total_cached_agents": 5,
  "cache_keys": ["company-1", "company-2"]
}
```

### POST /cache/invalidate

Invalida el caché de un agente específico.

**Request Body:**
```json
{
  "companyId": 1
}
```

**Response (200):**
```json
{
  "message": "Cache invalidated for company 1"
}
```

---

## Modelos de Datos

### User
```json
{
  "id": 1,
  "company_id": 1,
  "username": "admin",
  "email": "admin@company.com",
  "role": "ADMIN",
  "created_at": "2025-10-08T10:00:00Z",
  "updated_at": "2025-10-08T10:00:00Z"
}
```

### Company
```json
{
  "id": 1,
  "name": "TechCorp Inc.",
  "created_at": "2025-10-08T10:00:00Z"
}
```

### Ticket
```json
{
  "id": 1,
  "company_id": 1,
  "created_by_user_id": 1,
  "subject": "Bloquear IP maliciosa",
  "description": "Detectada actividad sospechosa",
  "status": "PENDING",
  "created_at": "2025-10-08T14:00:00Z",
  "updated_at": "2025-10-08T14:00:00Z"
}
```

**Estados de Ticket:**
- `PENDING`: Pendiente de ejecución
- `EXECUTED`: Ejecutado correctamente
- `FAILED`: Fallo en la ejecución
- `DERIVED`: Derivado a otro sistema

### Integration
```json
{
  "id": 1,
  "company_id": 1,
  "provider": "palo_alto",
  "keyvault_secret_id": "https://vault.azure.net/secrets/key",
  "extra_json": {},
  "created_at": "2025-10-08T10:00:00Z"
}
```

### Alert
```json
{
  "id": 1,
  "company_id": 1,
  "title": "Actividad sospechosa",
  "severity": "high",
  "status": "active",
  "source": "Palo Alto",
  "created_at": "2025-10-08T14:00:00Z",
  "resolved_at": null,
  "resolved_by_user_id": null
}
```

**Severidades:**
- `critical`: Crítico
- `high`: Alto
- `medium`: Medio
- `low`: Bajo

### Vulnerability
```json
{
  "id": 1,
  "company_id": 1,
  "cve_id": "CVE-2024-1234",
  "severity": "critical",
  "status": "open",
  "affected_system": "Web Server 1",
  "patch_available": true,
  "created_at": "2025-10-08T10:00:00Z"
}
```

### AgentInstance
```json
{
  "id": "uuid-here",
  "company_id": 1,
  "agent_type": "SOPHIA",
  "status": "ACTIVE",
  "azure_openai_endpoint": "https://openai.azure.com",
  "azure_openai_deployment": "gpt-4o",
  "azure_search_endpoint": "https://search.azure.com",
  "azure_speech_endpoint": "https://speech.azure.com",
  "azure_speech_region": "eastus",
  "azure_speech_voice_name": "es-ES-ElviraNeural",
  "created_at": "2025-10-08T10:00:00Z",
  "last_used_at": "2025-10-08T15:00:00Z"
}
```

---

## Códigos de Estado HTTP

### Éxito
- **200 OK**: Solicitud exitosa
- **201 Created**: Recurso creado exitosamente
- **204 No Content**: Solicitud exitosa sin contenido de respuesta

### Errores del Cliente
- **400 Bad Request**: Datos de solicitud inválidos
- **401 Unauthorized**: Autenticación fallida o token inválido
- **403 Forbidden**: Permisos insuficientes
- **404 Not Found**: Recurso no encontrado
- **409 Conflict**: Conflicto con el estado actual (ej: usuario ya existe)
- **422 Unprocessable Entity**: Validación de datos fallida

### Errores del Servidor
- **500 Internal Server Error**: Error interno del servidor
- **503 Service Unavailable**: Servicio temporalmente no disponible

### Formato de Error
```json
{
  "error": "Descripción del error",
  "message": "Mensaje detallado",
  "status": 400
}
```

---

## Ejemplos de Uso

### cURL

#### Registro de Usuario
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp Inc.",
    "username": "admin",
    "email": "admin@techcorp.com",
    "password": "SecurePassword123"
  }'
```

#### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecurePassword123"
  }'
```

#### Crear Ticket (Autenticado)
```bash
curl -X POST http://localhost:5000/api/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "subject": "Bloquear IP maliciosa",
    "description": "Detectada actividad sospechosa desde 192.168.1.100"
  }'
```

#### Chat con SOPHIA
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "companyId": 1,
    "userId": 1,
    "agentAccessKey": "your-access-key",
    "message": "¿Cuáles son las alertas críticas activas?"
  }'
```

#### Transcribir Audio
```bash
curl -X POST http://localhost:5000/api/voice/transcribe \
  -F "audio=@recording.webm" \
  -F "companyId=1" \
  -F "agentAccessKey=your-access-key"
```

### JavaScript (Fetch API)

#### Login y Guardar Token
```javascript
async function login(username, password) {
  const response = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }
  
  throw new Error(data.error);
}
```

#### Obtener Tickets con Autenticación
```javascript
async function getTickets() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:5000/api/tickets', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

#### Chat con SOPHIA
```javascript
async function chatWithSophia(message, companyId, agentAccessKey) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      companyId,
      userId: 1,
      agentAccessKey,
      message
    })
  });
  
  return await response.json();
}
```

#### Grabar y Transcribir Voz
```javascript
async function transcribeAudio(audioBlob, companyId, agentAccessKey) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  formData.append('companyId', companyId);
  formData.append('agentAccessKey', agentAccessKey);
  
  const response = await fetch('http://localhost:5000/api/voice/transcribe', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}
```

### Python (Requests)

#### Registro y Login
```python
import requests

# Registro
response = requests.post(
    'http://localhost:5000/api/auth/register',
    json={
        'company_name': 'TechCorp Inc.',
        'username': 'admin',
        'email': 'admin@techcorp.com',
        'password': 'SecurePassword123'
    }
)
data = response.json()
access_token = data['access_token']

# Login
response = requests.post(
    'http://localhost:5000/api/auth/login',
    json={
        'username': 'admin',
        'password': 'SecurePassword123'
    }
)
data = response.json()
access_token = data['access_token']
```

#### Crear y Obtener Tickets
```python
# Headers con autenticación
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Crear ticket
response = requests.post(
    'http://localhost:5000/api/tickets',
    headers=headers,
    json={
        'subject': 'Bloquear IP maliciosa',
        'description': 'Detectada actividad sospechosa desde 192.168.1.100'
    }
)
ticket = response.json()

# Obtener todos los tickets
response = requests.get(
    'http://localhost:5000/api/tickets',
    headers=headers
)
tickets = response.json()
```

#### Interactuar con SOPHIA
```python
# Chat con SOPHIA
response = requests.post(
    'http://localhost:8000/chat',
    json={
        'companyId': 1,
        'userId': 1,
        'agentAccessKey': 'your-access-key',
        'message': '¿Cuáles son las alertas críticas activas?'
    }
)
sophia_response = response.json()
print(sophia_response['response'])
```

#### Transcribir Audio
```python
# Transcribir archivo de audio
with open('recording.webm', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {
        'companyId': '1',
        'agentAccessKey': 'your-access-key'
    }
    
    response = requests.post(
        'http://localhost:5000/api/voice/transcribe',
        files=files,
        data=data
    )
    
    result = response.json()
    print(f"Texto transcrito: {result['text']}")
```

---

## Variables de Entorno

### Backend Principal (Puerto 5000)

```bash
# Base de Datos
DATABASE_URL=postgresql://user:password@localhost:5432/txdxai

# JWT
SESSION_SECRET=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Azure Key Vault
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

### SOPHIA Service (Puerto 8000)

```bash
# Backend URL
BACKEND_URL=http://localhost:5000/api

# Azure OpenAI (opcional, se configura por empresa)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Azure AI Search (opcional)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key

# Azure Speech (opcional)
AZURE_SPEECH_ENDPOINT=https://your-speech.cognitiveservices.azure.com
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

---

## Configuración Rápida

### 1. Instalación

```bash
# Clonar repositorio
git clone https://github.com/your-org/txdxai.git
cd txdxai

# Instalar dependencias Python
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb txdxai

# Ejecutar migraciones
flask db upgrade
```

### 3. Ejecutar Servicios

```bash
# Backend principal (Puerto 5000)
python run.py

# SOPHIA service (Puerto 8000)
python sophia_service/app.py
```

### 4. Acceder a la Aplicación

- **Backend API**: http://localhost:5000
- **SOPHIA API**: http://localhost:8000
- **Frontend (básico)**: http://localhost:5000

---

## Seguridad

### Buenas Prácticas

1. **Tokens JWT**: Los access tokens expiran en 24 horas
2. **Credenciales**: Nunca almacenar credenciales en el código
3. **Azure Key Vault**: Todas las credenciales sensibles se almacenan en Key Vault
4. **HTTPS**: Usar HTTPS en producción
5. **Rate Limiting**: Implementar rate limiting en producción
6. **Validación**: Todos los inputs son validados

### Multi-Tenancy

- **Aislamiento de datos**: Cada empresa tiene sus datos completamente aislados
- **Queries filtrados**: Todas las consultas filtran automáticamente por `company_id`
- **Validación de acceso**: Se valida que el usuario solo acceda a recursos de su empresa

---

## Soporte

Para más información o reportar problemas:

- **Documentación Técnica**: Ver `replit.md`
- **Swagger/OpenAPI**: http://localhost:5000/apidocs (cuando esté configurado)
- **Issues**: GitHub Issues

---

## Licencia

Propiedad de TxDxAI. Todos los derechos reservados.
