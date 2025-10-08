from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from txdxai.tickets import tickets_bp
from txdxai.extensions import db
from txdxai.db.models import Ticket
from txdxai.common.errors import ValidationError, NotFoundError, ForbiddenError
from txdxai.common.utils import get_current_user, log_audit

@tickets_bp.route('', methods=['GET'])
@jwt_required()
def get_tickets():
    user = get_current_user()
    
    status = request.args.get('status')
    
    query = Ticket.query.filter_by(company_id=user.company_id)
    
    if status:
        query = query.filter_by(status=status)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return jsonify({
        'tickets': [t.to_dict(include_creator=True) for t in tickets]
    }), 200


@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    user = get_current_user()
    
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.company_id != user.company_id:
        raise NotFoundError('Ticket not found')
    
    return jsonify(ticket.to_dict(include_creator=True)), 200


@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    user = get_current_user()
    data = request.get_json()
    
    if not data:
        raise ValidationError('Request body is required')
    
    subject = data.get('subject')
    description = data.get('description')
    
    if not subject:
        raise ValidationError('subject is required')
    
    ticket = Ticket(
        company_id=user.company_id,
        created_by_user_id=user.id,
        subject=subject,
        description=description,
        status='PENDING'
    )
    
    db.session.add(ticket)
    db.session.commit()
    
    log_audit('CREATE', 'TICKET', ticket.id, {'subject': subject, 'status': 'PENDING'})
    
    return jsonify({
        'message': 'Ticket created successfully',
        'ticket': ticket.to_dict(include_creator=True)
    }), 201


@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    user = get_current_user()
    
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.company_id != user.company_id:
        raise NotFoundError('Ticket not found')
    
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    
    if 'subject' in data:
        ticket.subject = data['subject']
    
    if 'description' in data:
        ticket.description = data['description']
    
    if 'status' in data:
        valid_statuses = ['PENDING', 'EXECUTED', 'FAILED', 'DERIVED']
        if data['status'] not in valid_statuses:
            raise ValidationError(f'status must be one of: {", ".join(valid_statuses)}')
        ticket.status = data['status']
        
        if data['status'] == 'EXECUTED':
            ticket.executed_at = datetime.utcnow()
    
    db.session.commit()
    
    log_audit('UPDATE', 'TICKET', ticket.id, {'subject': ticket.subject, 'status': ticket.status})
    
    return jsonify({
        'message': 'Ticket updated successfully',
        'ticket': ticket.to_dict(include_creator=True)
    }), 200


@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@jwt_required()
def delete_ticket(ticket_id):
    user = get_current_user()
    
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.company_id != user.company_id:
        raise NotFoundError('Ticket not found')
    
    db.session.delete(ticket)
    db.session.commit()
    
    log_audit('DELETE', 'TICKET', ticket_id, {'subject': ticket.subject})
    
    return jsonify({
        'message': 'Ticket deleted successfully'
    }), 200


@tickets_bp.route('/agent-create', methods=['POST'])
@jwt_required()
def agent_create_ticket():
    """
    Endpoint for SOPHIA agent to create tickets
    Requires agent JWT token with agent:invoke scope
    """
    claims = get_jwt()
    
    # Verify this is an agent token
    scopes = claims.get('scopes', [])
    if 'agent:invoke' not in scopes:
        raise ForbiddenError('Agent scope required')
    
    company_id = claims.get('company_id')
    if not company_id:
        raise ValidationError('company_id not found in token')
    
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    
    subject = data.get('subject')
    description = data.get('description')
    user_id = data.get('userId')
    severity = data.get('severity', 'medium')
    metadata = data.get('metadata', {})
    
    if not subject:
        raise ValidationError('subject is required')
    
    # Create ticket with backend-generated ID
    ticket = Ticket(
        company_id=company_id,
        created_by_user_id=user_id,
        subject=subject,
        description=description,
        status='PENDING'
    )
    
    db.session.add(ticket)
    db.session.commit()
    
    # Log the creation
    log_audit('CREATE', 'TICKET', ticket.id, {
        'subject': subject,
        'status': 'PENDING',
        'severity': severity,
        'agent_created': True
    })
    
    return jsonify({
        'success': True,
        'ticket_id': ticket.id,
        'ticket': ticket.to_dict(include_creator=False)
    }), 201
