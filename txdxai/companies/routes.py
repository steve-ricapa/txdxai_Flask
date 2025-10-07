from flask import request, jsonify
from flask_jwt_extended import jwt_required
from txdxai.companies import companies_bp
from txdxai.extensions import db
from txdxai.db.models import Company
from txdxai.common.errors import ValidationError, NotFoundError
from txdxai.common.utils import get_current_user, admin_required, log_audit

@companies_bp.route('', methods=['GET'])
@jwt_required()
def get_companies():
    user = get_current_user()
    
    if user.role == 'ADMIN':
        company = Company.query.get(user.company_id)
        companies = [company] if company else []
    else:
        companies = []
    
    return jsonify({
        'companies': [c.to_dict() for c in companies]
    }), 200


@companies_bp.route('/<int:company_id>', methods=['GET'])
@jwt_required()
def get_company(company_id):
    user = get_current_user()
    
    if user.company_id != company_id:
        raise NotFoundError('Company not found')
    
    company = Company.query.get(company_id)
    if not company:
        raise NotFoundError('Company not found')
    
    return jsonify(company.to_dict()), 200


@companies_bp.route('/<int:company_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_company(company_id):
    user = get_current_user()
    
    if user.company_id != company_id:
        raise NotFoundError('Company not found')
    
    company = Company.query.get(company_id)
    if not company:
        raise NotFoundError('Company not found')
    
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    
    if 'name' in data:
        company.name = data['name']
    
    db.session.commit()
    
    log_audit('UPDATE', 'COMPANY', company.id, {'name': company.name})
    
    return jsonify({
        'message': 'Company updated successfully',
        'company': company.to_dict()
    }), 200
