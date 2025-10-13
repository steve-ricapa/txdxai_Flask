from flask import request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from txdxai.admin import admin_bp
from txdxai.extensions import db
from txdxai.db.models import AgentInstance
from txdxai.common.errors import NotFoundError, ValidationError, ForbiddenError
from txdxai.common.utils import get_current_user, admin_required, log_audit
from txdxai.security.keys import generate_access_key, hash_access_key
from txdxai.security.encryption import encrypt_agent_key, decrypt_agent_key
from txdxai.integrations.keyvault import store_secret

@admin_bp.route('/agent-instances', methods=['POST'])
@jwt_required()
@admin_required
def create_agent_instance():
    user = get_current_user()
    data = request.get_json()
    
    company_id = data.get('companyId', user.company_id)
    agent_type = data.get('agentType', 'SOPHIA')
    
    azure_project_id = data.get('azureProjectId')
    azure_agent_id = data.get('azureAgentId')
    azure_vector_store_id = data.get('azureVectorStoreId')
    
    azure_openai_endpoint = data.get('azureOpenaiEndpoint')
    azure_openai_key = data.get('azureOpenaiKey')
    azure_openai_deployment = data.get('azureOpenaiDeployment')
    
    azure_search_endpoint = data.get('azureSearchEndpoint')
    azure_search_key = data.get('azureSearchKey')
    
    azure_speech_endpoint = data.get('azureSpeechEndpoint')
    azure_speech_key = data.get('azureSpeechKey')
    azure_speech_region = data.get('azureSpeechRegion')
    azure_speech_voice_name = data.get('azureSpeechVoiceName', 'es-ES-ElviraNeural')
    
    region = data.get('region')
    
    if company_id != user.company_id:
        raise ForbiddenError('Cannot create agent instance for other companies')
    
    access_key = generate_access_key(40)
    access_key_hash = hash_access_key(access_key)
    access_key_encrypted = encrypt_agent_key(access_key)
    
    azure_openai_key_secret_id = None
    if azure_openai_key:
        secret_name = f"agent-{agent_type.lower()}-{company_id}-openai-{datetime.utcnow().timestamp()}"
        azure_openai_key_secret_id = store_secret(secret_name, azure_openai_key)
    
    azure_search_key_secret_id = None
    if azure_search_key:
        secret_name = f"agent-{agent_type.lower()}-{company_id}-search-{datetime.utcnow().timestamp()}"
        azure_search_key_secret_id = store_secret(secret_name, azure_search_key)
    
    azure_speech_key_secret_id = None
    if azure_speech_key:
        secret_name = f"agent-{agent_type.lower()}-{company_id}-speech-{datetime.utcnow().timestamp()}"
        azure_speech_key_secret_id = store_secret(secret_name, azure_speech_key)
    
    settings = {
        'region': region
    }
    
    agent_instance = AgentInstance(
        company_id=company_id,
        agent_type=agent_type,
        azure_project_id=azure_project_id,
        azure_agent_id=azure_agent_id,
        azure_vector_store_id=azure_vector_store_id,
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_key_secret_id=azure_openai_key_secret_id,
        azure_openai_deployment=azure_openai_deployment,
        azure_search_endpoint=azure_search_endpoint,
        azure_search_key_secret_id=azure_search_key_secret_id,
        azure_speech_endpoint=azure_speech_endpoint,
        azure_speech_key_secret_id=azure_speech_key_secret_id,
        azure_speech_region=azure_speech_region,
        azure_speech_voice_name=azure_speech_voice_name,
        client_access_key_hash=access_key_hash,
        client_access_key_encrypted=access_key_encrypted,
        settings=settings,
        status='ACTIVE' if azure_openai_endpoint else 'TO_PROVISION'
    )
    
    db.session.add(agent_instance)
    db.session.commit()
    
    log_audit('CREATE', 'AGENT_INSTANCE', agent_instance.id, {
        'agent_type': agent_type,
        'company_id': company_id,
        'azure_openai_endpoint': azure_openai_endpoint,
        'azure_openai_deployment': azure_openai_deployment
    })
    
    return jsonify({
        'message': 'Agent instance created successfully',
        'agent_instance': agent_instance.to_dict(),
        'agent_access_key': access_key
    }), 201


@admin_bp.route('/agent-instances', methods=['GET'])
@jwt_required()
@admin_required
def get_agent_instances():
    user = get_current_user()
    
    instances = AgentInstance.query.filter_by(company_id=user.company_id).all()
    
    log_audit('VIEW', 'AGENT_INSTANCES', None, {'count': len(instances)})
    
    return jsonify({
        'agent_instances': [inst.to_dict() for inst in instances]
    }), 200


@admin_bp.route('/agent-instances/<instance_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_agent_instance(instance_id):
    user = get_current_user()
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    log_audit('VIEW', 'AGENT_INSTANCE', instance_id, {})
    
    return jsonify(instance.to_dict()), 200


@admin_bp.route('/agent-instances/<instance_id>/rotate-key', methods=['POST'])
@jwt_required()
@admin_required
def rotate_agent_key(instance_id):
    user = get_current_user()
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    new_access_key = generate_access_key(40)
    new_access_key_hash = hash_access_key(new_access_key)
    new_access_key_encrypted = encrypt_agent_key(new_access_key)
    
    instance.client_access_key_hash = new_access_key_hash
    instance.client_access_key_encrypted = new_access_key_encrypted
    db.session.commit()
    
    log_audit('ROTATE_KEY', 'AGENT_INSTANCE', instance_id, {})
    
    return jsonify({
        'message': 'Agent access key rotated successfully',
        'agent_access_key': new_access_key
    }), 200


@admin_bp.route('/agent-instances/<instance_id>', methods=['PATCH'])
@jwt_required()
@admin_required
def update_agent_instance(instance_id):
    """
    Update agent instance configuration (excluding status).
    Use PATCH /api/admin/agent-instances/{id}/status to update status.
    """
    user = get_current_user()
    data = request.get_json()
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    # Status updates must go through dedicated endpoint
    if 'status' in data:
        raise ValidationError('Status cannot be updated via this endpoint. Use PATCH /api/admin/agent-instances/{id}/status instead')
    
    if 'settings' in data:
        instance.settings = data['settings']
    
    if 'azureProjectId' in data:
        instance.azure_project_id = data['azureProjectId']
    
    if 'azureAgentId' in data:
        instance.azure_agent_id = data['azureAgentId']
    
    if 'azureVectorStoreId' in data:
        instance.azure_vector_store_id = data['azureVectorStoreId']
    
    db.session.commit()
    
    log_audit('UPDATE', 'AGENT_INSTANCE', instance_id, data)
    
    return jsonify({
        'message': 'Agent instance updated successfully',
        'agent_instance': instance.to_dict()
    }), 200


@admin_bp.route('/agent-instances/<instance_id>/access-key', methods=['GET'])
@jwt_required()
@admin_required
def get_agent_access_key(instance_id):
    """
    Retrieve the agent access key for a specific instance.
    This endpoint allows users to recover their agent key after logout or on different devices.
    """
    user = get_current_user()
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    if not instance.client_access_key_encrypted:
        raise ValidationError('No access key available for this instance. Please rotate the key.')
    
    access_key = decrypt_agent_key(instance.client_access_key_encrypted)
    
    if not access_key:
        raise ValidationError('Unable to decrypt access key. Please rotate the key.')
    
    log_audit('RETRIEVE_KEY', 'AGENT_INSTANCE', instance_id, {})
    
    return jsonify({
        'agent_access_key': access_key,
        'instance_id': instance.id,
        'agent_type': instance.agent_type
    }), 200


@admin_bp.route('/agent-instances/<instance_id>/status', methods=['PATCH'])
@jwt_required()
@admin_required
def update_agent_status(instance_id):
    """Update agent instance status (ACTIVE, TO_PROVISION, DISABLED)"""
    user = get_current_user()
    data = request.get_json()
    
    if not data or 'status' not in data:
        raise ValidationError('Status is required')
    
    new_status = data['status']
    valid_statuses = ['ACTIVE', 'TO_PROVISION', 'DISABLED']
    
    if new_status not in valid_statuses:
        raise ValidationError(f'Status must be one of: {", ".join(valid_statuses)}')
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    old_status = instance.status
    instance.status = new_status
    db.session.commit()
    
    log_audit('UPDATE_STATUS', 'AGENT_INSTANCE', instance_id, {
        'old_status': old_status,
        'new_status': new_status
    })
    
    return jsonify({
        'message': f'Agent status updated from {old_status} to {new_status}',
        'agent_instance': instance.to_dict()
    }), 200


@admin_bp.route('/agent-instances/<instance_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_agent_instance(instance_id):
    user = get_current_user()
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    instance.status = 'DISABLED'
    db.session.commit()
    
    log_audit('DELETE', 'AGENT_INSTANCE', instance_id, {})
    
    return jsonify({
        'message': 'Agent instance disabled successfully'
    }), 200
