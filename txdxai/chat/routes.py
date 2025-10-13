import requests
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from txdxai.chat import chat_bp
from txdxai.common.errors import ValidationError, TxDxAIError, UnauthorizedError
from txdxai.common.utils import log_audit
from txdxai.db.models import User, AgentInstance
from txdxai.extensions import db
from txdxai.security.keys import verify_access_key
import os

SOPHIA_SERVICE_URL = os.environ.get('SOPHIA_SERVICE_URL', 'http://localhost:8000')

@chat_bp.route('/chat', methods=['POST'])
@jwt_required()
def proxy_chat():
    """
    Proxy endpoint that forwards chat requests to SOPHIA microservice.
    
    Security:
    1. Validates user authentication (JWT)
    2. Validates agent access key against bcrypt hash
    3. Enforces ACTIVE status requirement
    4. Verifies company and user authorization
    5. Forwards request to SOPHIA service on port 8000
    
    Request body:
    {
        "companyId": 1,
        "userId": 1,
        "agentAccessKey": "...",
        "message": "user message",
        "threadId": "optional-thread-id"
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        raise ValidationError('User not found')
    
    data = request.get_json()
    
    required_fields = ['companyId', 'userId', 'agentAccessKey', 'message']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f'Missing required field: {field}')
    
    company_id = data.get('companyId')
    request_user_id = data.get('userId')
    agent_access_key = data.get('agentAccessKey')
    
    # Verify company authorization
    if user.company_id != company_id:
        raise UnauthorizedError('Access denied to this company')
    
    # Verify user identity
    if user.id != request_user_id:
        raise UnauthorizedError('User ID mismatch')
    
    # Get ACTIVE agent instances for this company
    instances = AgentInstance.query.filter_by(
        company_id=company_id,
        agent_type='SOPHIA',
        status='ACTIVE'
    ).all()
    
    if not instances:
        raise UnauthorizedError('No active agent instance found for this company')
    
    # Verify access key against bcrypt hash
    instance = None
    for candidate in instances:
        if verify_access_key(agent_access_key, candidate.client_access_key_hash):
            instance = candidate
            break
    
    if not instance:
        raise UnauthorizedError('Invalid agent access key')
    
    log_audit('CHAT_REQUEST', 'CHAT', None, {
        'company_id': company_id,
        'user_id': user_id,
        'agent_instance_id': instance.id,
        'message_preview': data.get('message')[:50] if len(data.get('message', '')) > 50 else data.get('message')
    })
    
    try:
        sophia_response = requests.post(
            f'{SOPHIA_SERVICE_URL}/chat',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if sophia_response.status_code == 200:
            return jsonify(sophia_response.json()), 200
        else:
            error_data = sophia_response.json() if sophia_response.headers.get('content-type') == 'application/json' else {'error': sophia_response.text}
            return jsonify(error_data), sophia_response.status_code
            
    except requests.exceptions.Timeout:
        raise TxDxAIError('SOPHIA service timeout', 504)
    except requests.exceptions.ConnectionError:
        raise TxDxAIError('Cannot connect to SOPHIA service', 503)
    except Exception as e:
        raise TxDxAIError(f'Error communicating with SOPHIA: {str(e)}', 500)
