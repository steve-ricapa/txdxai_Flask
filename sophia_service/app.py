from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import sys
import os
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config, config_cache
from sophia.agent_loader import agent_loader
from sophia.memory import memory_manager
from sophia.intent_router import intent_router
from sophia.handoff import create_ticket_stub
from sophia.mock_integrations import (
    get_palo_alto_alerts,
    get_splunk_logs,
    get_grafana_metrics,
    get_wazuh_alerts,
    get_meraki_network_status,
    execute_security_action
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS.split(','))


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SOPHIA',
        'version': '2.0.0',
        'architecture': 'modular',
        'azure_ai_configured': config.validate(),
        'config': config.get_info()
    }), 200


def validate_agent_access(company_id: int, agent_access_key: str) -> Optional[Dict[str, Any]]:
    """Validate agent access key with backend"""
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
                'agent_instance_id': data.get('agent_instance_id'),
                'agent_instance': data.get('agent_instance', {})
            }
        return None
    except Exception as e:
        logger.error(f"Auth validation error: {e}")
        return None


def get_agent_instance(agent_instance_id: str) -> Optional[Dict[str, Any]]:
    """Get agent instance details from backend (fallback)"""
    try:
        response = requests.get(
            f"{config.BACKEND_URL}/agents/instance/{agent_instance_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error fetching agent instance: {e}")
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


def process_user_message(message: str, company_id: int, user_id: int) -> Dict:
    """
    Process user message with intent detection and routing
    
    Returns:
        Dict with response and metadata
    """
    intent_type, action_request = intent_router.detect_intent(message)
    
    logger.info(f"Detected intent: {intent_type} for company {company_id}")
    
    if intent_type == "action":
        if intent_router.should_escalate_to_victoria(action_request):
            ticket_result = create_ticket_stub(
                action_request=action_request,
                company_id=company_id,
                user_id=user_id,
                context={"intent_type": intent_type}
            )
            
            return {
                'response': ticket_result['escalation_message'],
                'intent': 'action_escalated',
                'ticket_id': ticket_result['victoria_response'].get('ticket_id'),
                'tool_calls': ['create_victoria_ticket']
            }
        else:
            result = execute_security_action(
                action_request.action_type,
                action_request.parameters
            )
            
            return {
                'response': f"✅ Action executed successfully:\n\n{result.get('message')}",
                'intent': 'action_executed',
                'action_result': result,
                'tool_calls': [action_request.action_type]
            }
    
    elif intent_type == "query":
        rag_tool = agent_loader.get_rag_tool(company_id)
        
        if rag_tool:
            context = rag_tool.get_context(message, max_tokens=1500)
            
            security_tools = {
                'palo_alto': get_palo_alto_alerts() if 'alert' in message.lower() or 'palo' in message.lower() else None,
                'splunk': get_splunk_logs(message, limit=5) if 'log' in message.lower() or 'splunk' in message.lower() else None,
                'grafana': get_grafana_metrics() if 'metric' in message.lower() or 'grafana' in message.lower() else None,
                'wazuh': get_wazuh_alerts() if 'wazuh' in message.lower() else None,
                'meraki': get_meraki_network_status() if 'meraki' in message.lower() or 'network' in message.lower() else None
            }
            
            tools_used = [k for k, v in security_tools.items() if v is not None]
            tools_data = {k: v for k, v in security_tools.items() if v is not None}
            
            response_parts = [f"**Response to your query:**\n"]
            
            if context:
                response_parts.append(context)
            
            if tools_data:
                response_parts.append("\n**Security Tool Data:**\n")
                for tool_name, tool_data in tools_data.items():
                    response_parts.append(f"\n**{tool_name.replace('_', ' ').title()}:**")
                    if isinstance(tool_data, list) and tool_data:
                        response_parts.append(f"Found {len(tool_data)} items")
                    elif isinstance(tool_data, dict):
                        response_parts.append(f"Status: {tool_data.get('status', 'available')}")
            
            if not context and not tools_data:
                response_parts.append("I found information related to your query. How can I help you further?")
            
            return {
                'response': '\n'.join(response_parts),
                'intent': 'query',
                'tool_calls': ['rag_search'] + tools_used,
                'tools_data': tools_data
            }
        else:
            return {
                'response': "I can help answer your security questions. Please provide more details.",
                'intent': 'query',
                'tool_calls': [],
                'mode': 'mock'
            }
    
    else:
        return {
            'response': "I'm not sure how to help with that. Can you rephrase your question or request?",
            'intent': 'unknown',
            'tool_calls': []
        }


@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint for SOPHIA with modular architecture
    
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
    agent_instance = auth_data.get('agent_instance', {})
    
    if not agent_instance:
        agent_instance = get_agent_instance(auth_data['agent_instance_id'])
        if not agent_instance:
            return jsonify({
                'error': 'Agent instance metadata unavailable'
            }), 502
    
    azure_config = {
        'azure_project_id': agent_instance.get('azure_project_id'),
        'azure_agent_id': agent_instance.get('azure_agent_id'),
        'azure_vector_store_id': agent_instance.get('azure_vector_store_id'),
        'azure_openai_endpoint': agent_instance.get('azure_openai_endpoint'),
        'azure_openai_key': agent_instance.get('azure_openai_key'),
        'azure_openai_deployment': agent_instance.get('azure_openai_deployment'),
        'azure_search_endpoint': agent_instance.get('azure_search_endpoint'),
        'azure_search_key': agent_instance.get('azure_search_key')
    }
    
    agent_id = agent_loader.initialize_agent(company_id, azure_config)
    
    if not thread_id:
        thread_id = memory_manager.create_thread(company_id, user_id)
    
    memory_manager.add_message(thread_id, 'user', message)
    
    result = process_user_message(message, company_id, user_id)
    
    memory_manager.add_message(thread_id, 'assistant', result['response'])
    
    log_audit('CHAT', 'SOPHIA_MESSAGE', thread_id, {
        'company_id': company_id,
        'user_id': user_id,
        'intent': result.get('intent'),
        'message_length': len(message)
    }, auth_token)
    
    return jsonify({
        'response': result['response'],
        'threadId': thread_id,
        'agentId': agent_id,
        'intent': result.get('intent'),
        'toolCalls': result.get('tool_calls', []),
        'ticketId': result.get('ticket_id'),
        'mode': 'mock' if agent_loader.is_mock_mode(company_id) else 'azure'
    }), 200


@app.route('/threads/<thread_id>', methods=['GET'])
def get_thread(thread_id):
    """Get conversation history for a thread"""
    context = memory_manager.get_context(thread_id)
    
    if not context:
        return jsonify({'error': 'Thread not found'}), 404
    
    return jsonify({
        'threadId': thread_id,
        'companyId': context.company_id,
        'userId': context.user_id,
        'messages': context.messages,
        'createdAt': context.created_at.isoformat(),
        'lastUpdated': context.last_updated.isoformat()
    }), 200


@app.route('/threads/<thread_id>', methods=['DELETE'])
def clear_thread(thread_id):
    """Clear a conversation thread"""
    memory_manager.clear_thread(thread_id)
    
    return jsonify({
        'message': 'Thread cleared successfully',
        'threadId': thread_id
    }), 200


@app.route('/config/test', methods=['POST'])
def test_config():
    """Test Azure credentials and configuration"""
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
    
    agent_instance = auth_data.get('agent_instance', {})
    
    has_openai = bool(agent_instance.get('azure_openai_endpoint') and agent_instance.get('azure_openai_key'))
    has_search = bool(agent_instance.get('azure_search_endpoint') and agent_instance.get('azure_search_key'))
    
    config_status = {
        'company_id': company_id,
        'agent_instance_id': auth_data.get('agent_instance_id'),
        'azure_openai_configured': has_openai,
        'azure_search_configured': has_search,
        'deployment_model': agent_instance.get('azure_openai_deployment', 'not_set'),
        'status': 'ready' if has_openai else 'mock_mode',
        'modular_architecture': True,
        'capabilities': {
            'intent_routing': True,
            'victoria_handoff': True,
            'rag_search': has_search,
            'security_tools': True
        }
    }
    
    if has_openai:
        config_status['message'] = 'All Azure credentials configured - full functionality available'
    else:
        config_status['message'] = 'Running in mock mode - configure Azure credentials for full functionality'
    
    return jsonify(config_status), 200


@app.route('/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    return jsonify(config_cache.get_stats()), 200


@app.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalidate cache for a company"""
    data = request.get_json()
    company_id = data.get('companyId')
    
    if company_id:
        config_cache.invalidate(company_id)
        agent_loader.clear_agent(company_id)
        return jsonify({'message': f'Cache invalidated for company {company_id}'}), 200
    else:
        config_cache.invalidate_all()
        return jsonify({'message': 'All cache invalidated'}), 200


@app.route('/', methods=['GET'])
def index():
    """Service info endpoint"""
    return jsonify({
        'service': 'SOPHIA AI Agent Service',
        'version': '2.0.0',
        'architecture': 'modular',
        'description': 'Multi-tenant cybersecurity assistant with intent routing and VictorIA handoff',
        'endpoints': {
            '/health': 'Health check',
            '/chat': 'Chat with SOPHIA (POST)',
            '/threads/<id>': 'Get or delete thread (GET/DELETE)',
            '/config/test': 'Test Azure configuration (POST)',
            '/cache/stats': 'Cache statistics (GET)',
            '/cache/invalidate': 'Invalidate cache (POST)'
        },
        'capabilities': {
            'intent_routing': 'Automatically detects query vs action intents',
            'victoria_handoff': 'Escalates high-risk actions to VictorIA',
            'rag_search': 'Azure AI Search integration',
            'security_tools': ['Palo Alto', 'Splunk', 'Grafana', 'Wazuh', 'Meraki'],
            'multi_tenant': 'Per-company Azure credentials and isolation'
        }
    }), 200


if __name__ == '__main__':
    logger.info(f"🤖 Starting SOPHIA AI Agent Service v2.0 on {config.SOPHIA_HOST}:{config.SOPHIA_PORT}")
    logger.info(f"📡 Backend: {config.BACKEND_URL}")
    logger.info(f"🏗️  Architecture: Modular with intent routing and VictorIA handoff")
    
    if config.validate():
        logger.info("✅ Azure AI configured at service level")
    else:
        logger.info("⚠️  Service-level Azure AI not configured - using per-company credentials")
    
    app.run(
        host=config.SOPHIA_HOST,
        port=config.SOPHIA_PORT,
        debug=config.DEBUG
    )
