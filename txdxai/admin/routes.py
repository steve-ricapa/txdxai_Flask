from flask import request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from txdxai.admin import admin_bp
from txdxai.extensions import db
from txdxai.db.models import AgentInstance
from txdxai.common.errors import NotFoundError, ValidationError, ForbiddenError
from txdxai.common.utils import get_current_user, admin_required, log_audit
from txdxai.security.keys import generate_access_key, hash_access_key
from txdxai.integrations.keyvault import store_secret

@admin_bp.route('/agent-instances', methods=['POST'])
@jwt_required()
@admin_required
def create_agent_instance():
    user = get_current_user()
    data = request.get_json()
    
    company_id = data.get('companyId', user.company_id)
    agent_type = data.get('agentType', 'SOPHIA')
    region = data.get('region')
    model = data.get('model')
    azure_project_id = data.get('azureProjectId')
    
    if company_id != user.company_id:
        raise ForbiddenError('Cannot create agent instance for other companies')
    
    access_key = generate_access_key(40)
    access_key_hash = hash_access_key(access_key)
    
    keyvault_secret_id = None
    if azure_project_id:
        azure_credentials = {
            'azure_project_id': azure_project_id,
            'region': region,
            'model': model
        }
        secret_name = f"agent-{agent_type.lower()}-{company_id}-{datetime.utcnow().timestamp()}"
        keyvault_secret_id = store_secret(secret_name, azure_credentials)
    
    settings = {
        'region': region,
        'model': model
    }
    
    agent_instance = AgentInstance(
        company_id=company_id,
        agent_type=agent_type,
        azure_project_id=azure_project_id,
        client_access_key_hash=access_key_hash,
        keyvault_secret_id=keyvault_secret_id,
        settings=settings,
        status='ACTIVE' if azure_project_id else 'TO_PROVISION'
    )
    
    db.session.add(agent_instance)
    db.session.commit()
    
    log_audit('CREATE', 'AGENT_INSTANCE', agent_instance.id, {
        'agent_type': agent_type,
        'company_id': company_id
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
    
    instance.client_access_key_hash = new_access_key_hash
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
    user = get_current_user()
    data = request.get_json()
    
    instance = AgentInstance.query.get(instance_id)
    if not instance or instance.company_id != user.company_id:
        raise NotFoundError('Agent instance not found')
    
    if 'status' in data:
        instance.status = data['status']
    
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
