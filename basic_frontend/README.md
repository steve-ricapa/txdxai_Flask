# SOPHIA Admin Panel - Frontend

Simple HTML/CSS/JavaScript frontend for administering and testing SOPHIA AI agent instances.

## Features

- **Login**: Authenticate as an admin user
- **Agent Instance Management**: Create and view agent instances
- **Azure Credentials**: Configure Azure OpenAI and Search credentials
- **Test Configuration**: Validate Azure setup
- **Chat Interface**: Test SOPHIA AI responses

## How to Use

### 1. Access the Frontend

The frontend is automatically served by the Flask backend at:
```
http://localhost:5000/
```

### 2. Login

Use your admin credentials:
- **Username**: Your admin username
- **Password**: Your admin password

*Note: If you don't have an account yet, use the `/api/auth/register` endpoint to create one*

### 3. Create Agent Instance

1. Click **"+ Create New Instance"**
2. Fill in the Azure credentials:
   - **Azure OpenAI Endpoint**: Your Azure OpenAI resource URL (e.g., `https://your-resource.openai.azure.com`)
   - **Azure OpenAI Key**: Your Azure OpenAI API key
   - **Azure OpenAI Deployment**: Model deployment name (e.g., `gpt-4o`, `gpt-4o-mini`)
   - **Azure Project ID** (optional): Azure AI project ID
   - **Azure Search Endpoint** (optional): Your Azure Search URL
   - **Azure Search Key** (optional): Your Azure Search API key
3. Click **"Create Instance"**
4. **Save the Agent Access Key** displayed in the response - you'll need it for testing

### 4. Update Credentials

To update existing instance credentials:
1. Enter the **Agent Instance ID**
2. Fill in the new credentials
3. Click **"Update Credentials"**

### 5. Test Configuration

1. Enter your **Company ID**
2. Enter the **Agent Access Key** (from instance creation)
3. Click **"Test Configuration"**
4. Check the status response:
   - **ready**: Azure credentials are configured correctly
   - **mock_mode**: No Azure credentials, running in mock mode

### 6. Chat with SOPHIA

1. Enter your **Company ID**
2. Enter the **Agent Access Key**
3. Type your message
4. Click **"Send to SOPHIA"**

The thread ID will be automatically saved for continued conversations.

## Architecture

- **Frontend**: Plain HTML/CSS/JavaScript (no frameworks)
- **Backend API**: Flask REST API on port 5000
- **SOPHIA Service**: Separate microservice on port 8000
- **Storage**: JWT tokens saved in localStorage

## API Endpoints Used

### Backend (port 5000)
- `POST /api/auth/login` - User authentication
- `POST /api/admin/agent-instances` - Create agent instance
- `GET /api/admin/agent-instances` - List agent instances
- `PUT /api/admin/agent-instances/{id}` - Update credentials

### SOPHIA Service (port 8000)
- `POST /config/test` - Test Azure configuration
- `POST /chat` - Chat with SOPHIA

## Files

- `index.html` - Main UI
- `script.js` - JavaScript logic and API calls
- `README.md` - This file

## Notes

- JWT tokens are stored in localStorage for persistence
- Password fields show warnings in browser console (normal behavior)
- The frontend auto-detects the SOPHIA service URL based on environment
- All API requests include JWT authentication headers
