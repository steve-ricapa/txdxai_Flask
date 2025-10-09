# 🔐 Agent Access Key Recovery - Multi-Device Support

## Problema Resuelto

Anteriormente, cuando creabas un agente SOPHIA obtenías un `agent_access_key` que solo estaba disponible en ese momento. Si cerrabas sesión o cambiabas de dispositivo, tenías que **recrear toda la instancia del agente**.

**Ahora esto está resuelto**: El sistema guarda tu access key de forma segura y encriptada, permitiéndote recuperarla en cualquier momento desde cualquier dispositivo.

## ¿Cómo Funciona?

### 1. Creación del Agente (Primera Vez)

```bash
POST /api/admin/agent-instances
Authorization: Bearer {tu_admin_token}

{
  "azure_openai_endpoint": "https://tu-endpoint.openai.azure.com",
  "azure_openai_key_secret_id": "openai-key-001",
  "azure_openai_deployment": "gpt-4o",
  "azure_search_endpoint": "https://tu-endpoint.search.windows.net",
  "azure_search_key_secret_id": "search-key-001",
  "azure_speech_endpoint": "https://eastus.api.cognitive.microsoft.com",
  "azure_speech_key_secret_id": "speech-key-001",
  "azure_speech_region": "eastus"
}
```

**Respuesta:**
```json
{
  "agent_access_key": "T6Cd0BrmPOrVYvRqsLYr6Eu7OjEWizzrtT6geIrF",
  "agent_instance": { ... },
  "message": "Agent instance created successfully"
}
```

✅ **Guarda el `agent_access_key`** (o no te preocupes, siempre lo puedes recuperar)

### 2. Recuperación desde Otro Dispositivo

```bash
GET /api/admin/agent-instances/{instance_id}/access-key
Authorization: Bearer {tu_admin_token}
```

**Respuesta:**
```json
{
  "agent_access_key": "T6Cd0BrmPOrVYvRqsLYr6Eu7OjEWizzrtT6geIrF",
  "agent_type": "SOPHIA",
  "instance_id": "0e5e7e33-4a09-4419-aac6-5f213a9f12b5"
}
```

✅ **Recibes el mismo access key que creaste originalmente**

## Seguridad

### Doble Protección

1. **Para autenticación del agente**: Hash bcrypt (costo 12)
   - Se usa para validar cuando el agente se conecta
   - Nunca se puede revertir al texto plano

2. **Para recuperación multi-dispositivo**: Encriptación Fernet (AES-256)
   - Permite desencriptar y recuperar la key original
   - Solo accesible por usuarios ADMIN de la misma compañía

### Configuración Requerida

La clave de encriptación debe estar configurada en las variables de entorno:

```bash
# Generar clave de encriptación (solo una vez)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Agregar a .env
AGENT_KEY_ENCRYPTION_KEY=n6W8tOkISJZ5gGCRy77tsKhYeiKDCn-qXFC8fLO9MAw=
```

⚠️ **IMPORTANTE**: Esta clave debe persistir entre reinicios. Sin ella, no podrás desencriptar las keys almacenadas.

### Producción (Azure)

En producción, almacena `AGENT_KEY_ENCRYPTION_KEY` en:
- Azure Key Vault (recomendado)
- Variable de entorno persistente en App Service

## Flujo Completo

### Escenario: Usuario con múltiples dispositivos

1. **Dispositivo 1 (Laptop)**: 
   - Login → Crear agente → Recibe `agent_access_key`
   - Usa SOPHIA normalmente

2. **Dispositivo 2 (PC de escritorio)**:
   - Login con el mismo usuario ADMIN
   - Llama `GET /api/admin/agent-instances/{id}/access-key`
   - Recibe el **mismo** `agent_access_key`
   - Puede usar SOPHIA sin problemas

3. **Frontend Streamlit separado**:
   - Login con usuario ADMIN
   - Recupera `agent_access_key`
   - Configura el cliente SOPHIA con esa key
   - ¡Funciona! Sin necesidad de recrear nada

## Endpoints Disponibles

### 1. Crear Agente
```
POST /api/admin/agent-instances
```
- Requiere: Token JWT de usuario ADMIN
- Retorna: `agent_access_key` + datos del agente

### 2. Recuperar Access Key
```
GET /api/admin/agent-instances/{id}/access-key
```
- Requiere: Token JWT de usuario ADMIN
- Retorna: `agent_access_key` desencriptado

### 3. Rotar Access Key
```
POST /api/admin/agent-instances/{id}/rotate-key
```
- Requiere: Token JWT de usuario ADMIN
- Genera nueva key, invalida la anterior
- Retorna: Nuevo `agent_access_key`

## Casos de Uso

### ✅ Sí - Usa el Endpoint de Recuperación

- Perdiste el access key original
- Necesitas configurar SOPHIA en un nuevo dispositivo
- Estás desarrollando un frontend separado (ej: Streamlit)
- Después de cerrar sesión y volver a entrar
- Necesitas el access key para configuración de producción

### ❌ No - Usa Rotación de Key

- Crees que la key fue comprometida
- Quieres revocar acceso actual
- Necesitas una key completamente nueva

## Integración con Postman

La colección de Postman incluye el endpoint de recuperación:

**Carpeta**: `4. Admin - Agent Instances`
**Request**: `Get Agent Access Key`

El script automáticamente guarda el access key en la variable de entorno:
```javascript
pm.environment.set("agent_access_key", jsonData.agent_access_key);
```

## Troubleshooting

### Error: "AGENT_KEY_ENCRYPTION_KEY environment variable is required"

**Causa**: La variable de entorno no está configurada

**Solución**:
```bash
# 1. Generar key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Agregar a .env
echo "AGENT_KEY_ENCRYPTION_KEY=tu_key_aqui" >> .env

# 3. Reiniciar servicios
bash start_services.sh
```

### Error: "Failed to decrypt agent access key"

**Causa**: La clave de encriptación cambió desde que se creó la instancia

**Solución**:
- Si tienes la key original de encriptación, restáurala
- Si no, usa el endpoint de rotación para generar una nueva key

## Arquitectura Técnica

### Módulo de Encriptación
```python
# txdxai/security/encryption.py

def encrypt_agent_key(plain_key: str) -> str:
    """Encripta usando Fernet (AES-256)"""
    
def decrypt_agent_key(encrypted_key: str) -> Optional[str]:
    """Desencripta y retorna key original"""
```

### Modelo de Base de Datos
```python
class AgentInstance(db.Model):
    # Hash para autenticación
    client_access_key_hash = db.Column(db.String(255))
    
    # Encriptado para recuperación
    client_access_key_encrypted = db.Column(db.Text, nullable=True)
```

### Flujo de Datos

**Creación:**
```
agent_access_key (plain)
    ├─> bcrypt.hash() -> client_access_key_hash (DB)
    └─> fernet.encrypt() -> client_access_key_encrypted (DB)
```

**Recuperación:**
```
GET /access-key
    └─> fernet.decrypt(client_access_key_encrypted) -> agent_access_key (plain)
```

## Conclusión

Esta funcionalidad elimina la fricción de tener que recrear instancias de agentes cada vez que cambias de dispositivo o pierdes la key original. El sistema es seguro (encriptación AES-256) y solo accesible por usuarios ADMIN de la misma compañía.

**Beneficios:**
- ✅ Configuración una sola vez
- ✅ Acceso desde múltiples dispositivos
- ✅ Seguridad con doble protección (hash + encriptación)
- ✅ Compatible con frontends externos (Streamlit, etc.)
