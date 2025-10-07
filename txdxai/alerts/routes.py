from flask import request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from txdxai.alerts import alerts_bp
from txdxai.extensions import db
from txdxai.db.models import Alert
from txdxai.common.errors import NotFoundError, ValidationError
from txdxai.common.utils import get_current_user, log_audit

@alerts_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_alerts():
    user = get_current_user()
    
    since = request.args.get('since')
    limit = request.args.get('limit', 100, type=int)
    
    query = Alert.query.filter_by(
        company_id=user.company_id,
        status='active'
    )
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            query = query.filter(Alert.created_at >= since_dt)
        except:
            raise ValidationError('Invalid since timestamp format')
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    log_audit('VIEW', 'ACTIVE_ALERTS', None, {'count': len(alerts)})
    
    return jsonify({
        'alerts': [a.to_dict() for a in alerts]
    }), 200


@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alert(alert_id):
    user = get_current_user()
    
    alert = Alert.query.get(alert_id)
    if not alert or alert.company_id != user.company_id:
        raise NotFoundError('Alert not found')
    
    if alert.status == 'resolved':
        raise ValidationError('Alert is already resolved')
    
    alert.status = 'resolved'
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by_user_id = user.id
    
    db.session.commit()
    
    log_audit('RESOLVE', 'ALERT', alert.id, {'title': alert.title})
    
    return jsonify({
        'message': 'Alert resolved successfully',
        'alert': alert.to_dict()
    }), 200
