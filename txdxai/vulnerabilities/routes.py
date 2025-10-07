from flask import request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from txdxai.vulnerabilities import vulnerabilities_bp
from txdxai.extensions import db
from txdxai.db.models import Vulnerability
from txdxai.common.errors import NotFoundError, ValidationError
from txdxai.common.utils import get_current_user, log_audit

@vulnerabilities_bp.route('', methods=['GET'])
@jwt_required()
def get_vulnerabilities():
    user = get_current_user()
    
    status = request.args.get('status')
    severity = request.args.get('severity')
    
    query = Vulnerability.query.filter_by(company_id=user.company_id)
    
    if status:
        query = query.filter_by(status=status)
    if severity:
        query = query.filter_by(severity=severity)
    
    vulnerabilities = query.order_by(Vulnerability.created_at.desc()).all()
    
    log_audit('VIEW', 'VULNERABILITIES', None, {'count': len(vulnerabilities)})
    
    return jsonify({
        'vulnerabilities': [v.to_dict() for v in vulnerabilities]
    }), 200


@vulnerabilities_bp.route('/<int:vuln_id>', methods=['GET'])
@jwt_required()
def get_vulnerability(vuln_id):
    user = get_current_user()
    
    vuln = Vulnerability.query.get(vuln_id)
    if not vuln or vuln.company_id != user.company_id:
        raise NotFoundError('Vulnerability not found')
    
    return jsonify(vuln.to_dict()), 200


@vulnerabilities_bp.route('/<int:vuln_id>/patch', methods=['POST'])
@jwt_required()
def patch_vulnerability(vuln_id):
    user = get_current_user()
    
    vuln = Vulnerability.query.get(vuln_id)
    if not vuln or vuln.company_id != user.company_id:
        raise NotFoundError('Vulnerability not found')
    
    if vuln.status == 'resolved':
        raise ValidationError('Vulnerability is already resolved')
    
    vuln.status = 'patching'
    vuln.patch_status = 'initiated'
    
    db.session.commit()
    
    log_audit('PATCH', 'VULNERABILITY', vuln.id, {'cve_id': vuln.cve_id})
    
    return jsonify({
        'message': 'Patch process initiated',
        'vulnerability': vuln.to_dict()
    }), 200
