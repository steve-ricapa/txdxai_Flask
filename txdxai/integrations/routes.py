from flask import request, jsonify
from flask_jwt_extended import jwt_required
from txdxai.integrations import integrations_bp
from txdxai.integrations.keyvault import store_secret, retrieve_secret, delete_secret
from txdxai.extensions import db
from txdxai.db.models import Integration
from txdxai.common.errors import ValidationError, NotFoundError
from txdxai.common.utils import get_current_user, admin_required, log_audit

@integrations_bp.route('', methods=['GET'])
@jwt_required()
def get_integrations():
    user = get_current_user()
    
    integrations = Integration.query.filter_by(company_id=user.company_id).all()
    
    return jsonify({
        'integrations': [i.to_dict() for i in integrations]
    }), 200


@integrations_bp.route('/<int:integration_id>', methods=['GET'])
@jwt_required()
def get_integration(integration_id):
    user = get_current_user()
    
    integration = Integration.query.get(integration_id)
    if not integration or integration.company_id != user.company_id:
        raise NotFoundError('Integration not found')
    
    return jsonify(integration.to_dict()), 200


@integrations_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_integration():
    user = get_current_user()
    data = request.get_json()
    
    if not data:
        raise ValidationError('Request body is required')
    
    provider = data.get('provider')
    credentials = data.get('credentials')
    extra_json = data.get('extra_json', {})
    
    if not provider:
        raise ValidationError('provider is required')
    
    if not credentials:
        raise ValidationError('credentials is required')
    
    valid_providers = ['palo_alto', 'splunk', 'wazuh', 'meraki']
    if provider not in valid_providers:
        raise ValidationError(f'provider must be one of: {", ".join(valid_providers)}')
    
    secret_name = f"{user.company_id}-{provider}-{data.get('name', 'default')}"
    
    try:
        keyvault_secret_id = store_secret(secret_name, str(credentials))
    except Exception as e:
        raise ValidationError(f'Failed to store credentials: {str(e)}')
    
    integration = Integration(
        company_id=user.company_id,
        provider=provider,
        keyvault_secret_id=keyvault_secret_id,
        extra_json=extra_json
    )
    
    db.session.add(integration)
    db.session.commit()
    
    log_audit('CREATE', 'INTEGRATION', integration.id, {'provider': provider})
    
    return jsonify({
        'message': 'Integration created successfully',
        'integration': integration.to_dict()
    }), 201


@integrations_bp.route('/<int:integration_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_integration(integration_id):
    user = get_current_user()
    
    integration = Integration.query.get(integration_id)
    if not integration or integration.company_id != user.company_id:
        raise NotFoundError('Integration not found')
    
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    
    if 'credentials' in data:
        try:
            store_secret(integration.keyvault_secret_id, str(data['credentials']))
        except Exception as e:
            raise ValidationError(f'Failed to update credentials: {str(e)}')
    
    if 'extra_json' in data:
        integration.extra_json = data['extra_json']
    
    db.session.commit()
    
    log_audit('UPDATE', 'INTEGRATION', integration.id, {'provider': integration.provider})
    
    return jsonify({
        'message': 'Integration updated successfully',
        'integration': integration.to_dict()
    }), 200


@integrations_bp.route('/<int:integration_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_integration(integration_id):
    user = get_current_user()
    
    integration = Integration.query.get(integration_id)
    if not integration or integration.company_id != user.company_id:
        raise NotFoundError('Integration not found')
    
    try:
        delete_secret(integration.keyvault_secret_id)
    except:
        pass
    
    db.session.delete(integration)
    db.session.commit()
    
    log_audit('DELETE', 'INTEGRATION', integration_id, {'provider': integration.provider})
    
    return jsonify({
        'message': 'Integration deleted successfully'
    }), 200


@integrations_bp.route('/<int:integration_id>/credentials', methods=['GET'])
@jwt_required()
@admin_required
def get_integration_credentials(integration_id):
    user = get_current_user()
    
    integration = Integration.query.get(integration_id)
    if not integration or integration.company_id != user.company_id:
        raise NotFoundError('Integration not found')
    
    try:
        credentials = retrieve_secret(integration.keyvault_secret_id)
    except Exception as e:
        raise ValidationError(f'Failed to retrieve credentials: {str(e)}')
    
    return jsonify({
        'credentials': credentials
    }), 200
