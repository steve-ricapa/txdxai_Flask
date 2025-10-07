from flask import request, jsonify
from flask_jwt_extended import jwt_required
from txdxai.systems import systems_bp
from txdxai.extensions import db
from txdxai.db.models import System, Integration
from txdxai.common.errors import NotFoundError
from txdxai.common.utils import get_current_user, log_audit

@systems_bp.route('/status', methods=['GET'])
@jwt_required()
def get_systems_status():
    user = get_current_user()
    
    systems = System.query.filter_by(company_id=user.company_id).all()
    
    systems_with_health = [s for s in systems if s.health_score is not None]
    avg_health = sum([s.health_score for s in systems_with_health]) / len(systems_with_health) if systems_with_health else 0
    
    status_summary = {
        'total_systems': len(systems),
        'online': len([s for s in systems if s.status == 'online']),
        'offline': len([s for s in systems if s.status == 'offline']),
        'degraded': len([s for s in systems if s.status == 'degraded']),
        'unknown': len([s for s in systems if s.status == 'unknown']),
        'average_health_score': round(avg_health, 2)
    }
    
    log_audit('VIEW', 'SYSTEMS_STATUS', None, status_summary)
    
    return jsonify(status_summary), 200


@systems_bp.route('', methods=['GET'])
@jwt_required()
def get_systems():
    user = get_current_user()
    
    systems = System.query.filter_by(company_id=user.company_id).all()
    
    log_audit('VIEW', 'SYSTEMS', None)
    
    return jsonify({
        'systems': [s.to_dict() for s in systems]
    }), 200


@systems_bp.route('/<int:system_id>', methods=['GET'])
@jwt_required()
def get_system(system_id):
    user = get_current_user()
    
    system = System.query.get(system_id)
    if not system or system.company_id != user.company_id:
        raise NotFoundError('System not found')
    
    return jsonify(system.to_dict()), 200
