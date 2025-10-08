from flask import request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta, datetime
from txdxai.agents import agents_bp
from txdxai.extensions import db
from txdxai.db.models import AgentInstance
from txdxai.common.errors import UnauthorizedError, ValidationError
from txdxai.security.keys import verify_access_key
from txdxai.common.utils import log_audit
from txdxai.integrations.keyvault import retrieve_secret

@agents_bp.route('/auth/token', methods=['POST'])
def authenticate_agent():
    """
    Public endpoint for client apps to authenticate and get a service JWT.
    Requires: companyId, agentType, and agentAccessKey
    """
    data = request.get_json()
    
    company_id = data.get('companyId')
    agent_type = data.get('agentType', 'SOPHIA')
    agent_access_key = data.get('agentAccessKey')
    
    if not company_id or not agent_access_key:
        raise ValidationError('companyId and agentAccessKey are required')
    
    instances = AgentInstance.query.filter_by(
        company_id=company_id,
        agent_type=agent_type,
        status='ACTIVE'
    ).all()
    
    if not instances:
        raise UnauthorizedError('Invalid credentials')
    
    instance = None
    for candidate in instances:
        if verify_access_key(agent_access_key, candidate.client_access_key_hash):
            instance = candidate
            break
    
    if not instance:
        raise UnauthorizedError('Invalid credentials')
    
    instance.last_used_at = datetime.utcnow()
    db.session.commit()
    
    additional_claims = {
        'scopes': ['agent:invoke'],
        'company_id': company_id,
        'agent_instance_id': instance.id,
        'agent_type': agent_type
    }
    
    service_token = create_access_token(
        identity=f"agent-{instance.id}",
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1)
    )
    
    log_audit('AUTH', 'AGENT_TOKEN', instance.id, {
        'company_id': company_id,
        'agent_type': agent_type
    })
    
    azure_openai_key = None
    if instance.azure_openai_key_secret_id:
        try:
            azure_openai_key = retrieve_secret(instance.azure_openai_key_secret_id)
        except:
            pass
    
    azure_search_key = None
    if instance.azure_search_key_secret_id:
        try:
            azure_search_key = retrieve_secret(instance.azure_search_key_secret_id)
        except:
            pass
    
    return jsonify({
        'access_token': service_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'agent_instance_id': instance.id,
        'agent_instance': {
            'id': instance.id,
            'company_id': instance.company_id,
            'agent_type': instance.agent_type,
            'azure_project_id': instance.azure_project_id,
            'azure_agent_id': instance.azure_agent_id,
            'azure_vector_store_id': instance.azure_vector_store_id,
            'azure_openai_endpoint': instance.azure_openai_endpoint,
            'azure_openai_key': azure_openai_key,
            'azure_openai_deployment': instance.azure_openai_deployment,
            'azure_search_endpoint': instance.azure_search_endpoint,
            'azure_search_key': azure_search_key,
            'status': instance.status,
            'settings': instance.settings
        }
    }), 200


@agents_bp.route('/instance/<instance_id>', methods=['GET'])
def get_agent_instance_metadata(instance_id):
    """
    Public endpoint for agent services to fetch instance metadata.
    No authentication required as this is protected by instance_id knowledge.
    """
    instance = AgentInstance.query.get(instance_id)
    
    if not instance:
        raise UnauthorizedError('Invalid instance')
    
    azure_openai_key = None
    if instance.azure_openai_key_secret_id:
        try:
            azure_openai_key = retrieve_secret(instance.azure_openai_key_secret_id)
        except:
            pass
    
    azure_search_key = None
    if instance.azure_search_key_secret_id:
        try:
            azure_search_key = retrieve_secret(instance.azure_search_key_secret_id)
        except:
            pass
    
    return jsonify({
        'id': instance.id,
        'company_id': instance.company_id,
        'agent_type': instance.agent_type,
        'azure_project_id': instance.azure_project_id,
        'azure_agent_id': instance.azure_agent_id,
        'azure_vector_store_id': instance.azure_vector_store_id,
        'azure_openai_endpoint': instance.azure_openai_endpoint,
        'azure_openai_key': azure_openai_key,
        'azure_openai_deployment': instance.azure_openai_deployment,
        'azure_search_endpoint': instance.azure_search_endpoint,
        'azure_search_key': azure_search_key,
        'status': instance.status,
        'settings': instance.settings
    }), 200
