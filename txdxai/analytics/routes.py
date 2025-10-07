from flask import request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from txdxai.analytics import analytics_bp
from txdxai.extensions import db
from txdxai.db.models import Alert, Vulnerability, Ticket
from sqlalchemy import func
from txdxai.common.utils import get_current_user, log_audit

@analytics_bp.route('/incidents', methods=['GET'])
@jwt_required()
def get_incidents_analytics():
    user = get_current_user()
    
    hours = request.args.get('hours', 24, type=int)
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    alerts = Alert.query.filter(
        Alert.company_id == user.company_id,
        Alert.created_at >= time_threshold
    ).all()
    
    severity_count = {
        'critical': len([a for a in alerts if a.severity == 'critical']),
        'high': len([a for a in alerts if a.severity == 'high']),
        'medium': len([a for a in alerts if a.severity == 'medium']),
        'low': len([a for a in alerts if a.severity == 'low'])
    }
    
    log_audit('VIEW', 'ANALYTICS_INCIDENTS', None, severity_count)
    
    return jsonify({
        'period_hours': hours,
        'total_incidents': len(alerts),
        'by_severity': severity_count,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@analytics_bp.route('/response-time', methods=['GET'])
@jwt_required()
def get_response_time_analytics():
    user = get_current_user()
    
    days = request.args.get('days', 7, type=int)
    time_threshold = datetime.utcnow() - timedelta(days=days)
    
    resolved_alerts = Alert.query.filter(
        Alert.company_id == user.company_id,
        Alert.status == 'resolved',
        Alert.created_at >= time_threshold
    ).all()
    
    response_times = []
    for alert in resolved_alerts:
        if alert.resolved_at and alert.created_at:
            response_time = (alert.resolved_at - alert.created_at).total_seconds() / 60
            response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    log_audit('VIEW', 'ANALYTICS_RESPONSE_TIME', None, {'avg': avg_response_time})
    
    return jsonify({
        'period_days': days,
        'average_response_time_minutes': round(avg_response_time, 2),
        'total_resolved_alerts': len(resolved_alerts),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@analytics_bp.route('/vulnerability-distribution', methods=['GET'])
@jwt_required()
def get_vulnerability_distribution():
    user = get_current_user()
    
    vulns = Vulnerability.query.filter_by(
        company_id=user.company_id,
        status='open'
    ).all()
    
    severity_distribution = {
        'critical': len([v for v in vulns if v.severity == 'critical']),
        'high': len([v for v in vulns if v.severity == 'high']),
        'medium': len([v for v in vulns if v.severity == 'medium']),
        'low': len([v for v in vulns if v.severity == 'low'])
    }
    
    cvss_ranges = {
        '9.0-10.0': len([v for v in vulns if v.cvss_score and v.cvss_score >= 9.0]),
        '7.0-8.9': len([v for v in vulns if v.cvss_score and 7.0 <= v.cvss_score < 9.0]),
        '4.0-6.9': len([v for v in vulns if v.cvss_score and 4.0 <= v.cvss_score < 7.0]),
        '0.1-3.9': len([v for v in vulns if v.cvss_score and 0.1 <= v.cvss_score < 4.0])
    }
    
    log_audit('VIEW', 'ANALYTICS_VULNERABILITIES', None, severity_distribution)
    
    return jsonify({
        'total_active_vulnerabilities': len(vulns),
        'by_severity': severity_distribution,
        'by_cvss_range': cvss_ranges,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    user = get_current_user()
    
    active_alerts = Alert.query.filter_by(
        company_id=user.company_id,
        status='active'
    ).count()
    
    open_vulns = Vulnerability.query.filter_by(
        company_id=user.company_id,
        status='open'
    ).count()
    
    pending_tickets = Ticket.query.filter_by(
        company_id=user.company_id,
        status='PENDING'
    ).count()
    
    return jsonify({
        'active_alerts': active_alerts,
        'open_vulnerabilities': open_vulns,
        'pending_tickets': pending_tickets,
        'timestamp': datetime.utcnow().isoformat()
    }), 200
