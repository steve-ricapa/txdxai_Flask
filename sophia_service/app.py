from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import json
import sys
import os
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from orchestrator import orchestrator

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS.split(','))

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SOPHIA',
        'version': '1.0.0',
        'azure_ai_configured': config.validate()
    }), 200


def validate_agent_access(company_id: int, agent_access_key: str) -> Optional[Dict[str, Any]]:
    """
    Validate agent access key with backend
    
    Args:
        company_id: Company ID
        agent_access_key: Agent access key
        
    Returns:
        Agent instance data or None if invalid
    """
    try:
        response = requests.post(
            f"{config.BACKEND_URL}/agents/auth/token",
            json={
                'companyId': company_id,
                'agentType': 'SOPHIA',
                'agentAccessKey': agent_access_key
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'access_token': data.get('access_token'),
                'agent_instance_id': data.get('agent_instance_id')
            }
        return None
    except Exception as e:
        print(f"Auth validation error: {e}")
        return None


def get_agent_instance(agent_instance_id: str, auth_token: str) -> Optional[Dict[str, Any]]:
    """
    Get agent instance details from backend
    
    Args:
        agent_instance_id: Agent instance ID
        auth_token: JWT token
        
    Returns:
        Agent instance data or None
    """
    try:
        response = requests.get(
            f"{config.BACKEND_URL}/admin/agent-instances/{agent_instance_id}",
            headers={'Authorization': f'Bearer {auth_token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching agent instance: {e}")
        return None


def log_audit(action: str, entity_type: str, entity_id: str, payload: Dict, auth_token: str):
    """Log action to backend audit system"""
    try:
        requests.post(
            f"{config.BACKEND_URL}/audit",
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'action': action,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'payload': payload
            },
            timeout=5
        )
    except:
        pass


@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint for SOPHIA
    
    Request body:
    {
        "companyId": int,
        "userId": int,
        "message": str,
        "threadId": str (optional),
        "agentAccessKey": str
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    company_id = data.get('companyId')
    user_id = data.get('userId')
    message = data.get('message')
    thread_id = data.get('threadId')
    agent_access_key = data.get('agentAccessKey')
    
    if not all([company_id, user_id, message, agent_access_key]):
        return jsonify({
            'error': 'companyId, userId, message, and agentAccessKey are required'
        }), 400
    
    auth_data = validate_agent_access(company_id, agent_access_key)
    if not auth_data:
        return jsonify({'error': 'Invalid agent access credentials'}), 401
    
    auth_token = auth_data['access_token']
    agent_instance_id = auth_data['agent_instance_id']
    
    agent_instance = get_agent_instance(agent_instance_id, auth_token)
    if not agent_instance:
        return jsonify({'error': 'Agent instance not found'}), 404
    
    azure_project_id = agent_instance.get('azure_project_id')
    azure_agent_id = agent_instance.get('azure_agent_id')
    vector_store_id = agent_instance.get('azure_vector_store_id')
    
    agent_id = orchestrator.initialize_agent(
        company_id,
        azure_project_id or f"project-{company_id}",
        azure_agent_id,
        vector_store_id
    )
    
    if not thread_id:
        thread_id = orchestrator.create_thread()
    
    result = orchestrator.chat(
        agent_id=agent_id,
        thread_id=thread_id,
        message=message,
        company_id=company_id,
        user_id=user_id,
        vector_store_id=vector_store_id,
        auth_token=auth_token
    )
    
    log_audit('CHAT', 'SOPHIA_MESSAGE', thread_id, {
        'company_id': company_id,
        'user_id': user_id,
        'message_length': len(message)
    }, auth_token)
    
    return jsonify({
        'response': result.get('response'),
        'threadId': result.get('thread_id'),
        'agentId': agent_id,
        'toolCalls': result.get('tool_calls', [])
    }), 200


@app.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh knowledge base endpoint
    
    Request body:
    {
        "companyId": int,
        "agentAccessKey": str
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    company_id = data.get('companyId')
    agent_access_key = data.get('agentAccessKey')
    
    if not all([company_id, agent_access_key]):
        return jsonify({
            'error': 'companyId and agentAccessKey are required'
        }), 400
    
    auth_data = validate_agent_access(company_id, agent_access_key)
    if not auth_data:
        return jsonify({'error': 'Invalid agent access credentials'}), 401
    
    auth_token = auth_data['access_token']
    agent_instance_id = auth_data['agent_instance_id']
    
    agent_instance = get_agent_instance(agent_instance_id, auth_token)
    if not agent_instance:
        return jsonify({'error': 'Agent instance not found'}), 404
    
    vector_store_id = agent_instance.get('azure_vector_store_id', 'default')
    
    result = orchestrator.refresh_knowledge(company_id, vector_store_id)
    
    log_audit('REFRESH', 'SOPHIA_KNOWLEDGE', vector_store_id, {
        'company_id': company_id
    }, auth_token)
    
    return jsonify(result), 200


@app.route('/', methods=['GET'])
def index():
    """Service info endpoint"""
    return jsonify({
        'service': 'SOPHIA AI Agent Service',
        'version': '1.0.0',
        'description': 'RAG-based cybersecurity assistant with tool calling',
        'endpoints': {
            '/health': 'Health check',
            '/chat': 'Chat with SOPHIA (POST)',
            '/refresh': 'Refresh knowledge base (POST)'
        },
        'tools': [
            'rag_search - Search knowledge base',
            'splunk_query - Query Splunk logs',
            'palo_alto_status - Check firewall status',
            'grafana_fetch - Fetch metrics',
            'create_ticket - Hand off to VICTORIA'
        ]
    }), 200


if __name__ == '__main__':
    print(f"🤖 Starting SOPHIA AI Agent Service on {config.SOPHIA_HOST}:{config.SOPHIA_PORT}")
    print(f"📡 Backend: {config.BACKEND_URL}")
    
    if config.validate():
        print("✅ Azure AI configured")
    else:
        print("⚠️  Running in mock mode - configure Azure AI for full functionality")
    
    app.run(
        host=config.SOPHIA_HOST,
        port=config.SOPHIA_PORT,
        debug=True
    )
