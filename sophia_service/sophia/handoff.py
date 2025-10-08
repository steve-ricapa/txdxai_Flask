"""
Handoff Module for VictorIA Integration
Creates ticket stubs and prepares escalation to VictorIA
"""

import logging
import requests
from typing import Dict, Optional
from datetime import datetime
from victor.ticket_models import TicketDraft, ActionRequest
from victor.client_stub import send_ticket_to_victoria
from config import config

logger = logging.getLogger(__name__)


def create_ticket_stub(
    action_request: ActionRequest,
    company_id: int,
    user_id: int,
    auth_token: str,
    context: Dict = {}
) -> Dict:
    """
    Create a ticket stub for VictorIA escalation
    Backend PostgreSQL assigns the unique ticket ID
    
    Args:
        action_request: Detected action request from user
        company_id: Company ID
        user_id: User ID
        auth_token: Agent JWT token for backend authentication
        context: Additional context (conversation history, system state, etc.)
    
    Returns:
        Dict with ticket info and VictorIA response
    """
    severity = _determine_severity(action_request)
    subject = f"Solicitud de Acción de Seguridad: {action_request.action_type}"
    description = f"""
Acción solicitada por el usuario: {action_request.original_message}

Intención detectada: {action_request.intent}
Tipo de acción: {action_request.action_type}
Parámetros: {action_request.parameters}
Requiere escalación: {action_request.requires_escalation}

Esta acción requiere revisión manual y ejecución por VictorIA.
    """.strip()
    
    # Create ticket in backend database (gets unique ID from PostgreSQL)
    backend_ticket = _create_backend_ticket(
        company_id=company_id,
        user_id=user_id,
        subject=subject,
        description=description,
        severity=severity,
        auth_token=auth_token,
        metadata={
            "action_type": action_request.action_type,
            "parameters": action_request.parameters,
            "created_by": "SOPHIA",
            "auto_escalated": action_request.requires_escalation
        }
    )
    
    if backend_ticket:
        ticket_id = backend_ticket.get('ticket_id')
        logger.info(f"Created backend ticket for company {company_id}: {ticket_id}")
        
        # Prepare VictorIA response with backend ticket ID
        victoria_response = {
            "status": "pending",
            "ticket_id": str(ticket_id),
            "message": "Ticket created and escalated to VictorIA",
            "estimated_response_time": "15 minutes"
        }
    else:
        # Fallback to stub if backend fails
        logger.warning(f"Backend ticket creation failed, using stub for company {company_id}")
        ticket = TicketDraft(
            subject=subject,
            description=description,
            severity=severity,
            context=context or {},
            company_id=company_id,
            user_id=user_id,
            metadata={}
        )
        victoria_response = send_ticket_to_victoria(ticket)
        ticket_id = victoria_response.get('ticket_id')
    
    return {
        "ticket_id": ticket_id,
        "victoria_response": victoria_response,
        "escalation_message": _create_escalation_message_with_id(ticket_id, severity, victoria_response)
    }


def _create_backend_ticket(
    company_id: int,
    user_id: int,
    subject: str,
    description: str,
    severity: str,
    auth_token: str,
    metadata: Dict = {}
) -> Optional[Dict]:
    """
    Create ticket in backend database (gets unique ID from PostgreSQL)
    
    Returns:
        Ticket data with backend-generated ID or None if failed
    """
    try:
        response = requests.post(
            f"{config.BACKEND_URL}/tickets/agent-create",
            headers={
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            },
            json={
                'subject': subject,
                'description': description,
                'userId': user_id,
                'severity': severity,
                'metadata': metadata
            },
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            return data
        else:
            logger.error(f"Failed to create backend ticket: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error creating backend ticket: {e}")
        return None


def _determine_severity(action_request: ActionRequest) -> str:
    """Determine ticket severity based on action request"""
    if action_request.requires_escalation:
        return "critical"
    elif action_request.action_type in ["block_ip", "quarantine_device", "shutdown_system"]:
        return "high"
    elif action_request.intent == "action":
        return "medium"
    else:
        return "low"


def _create_escalation_message_with_id(ticket_id: str, severity: str, victoria_response: Dict) -> str:
    """Create user-friendly escalation message with ticket ID"""
    estimated_time = victoria_response.get('estimated_response_time', '15 minutes')
    
    return f"""
🎫 **Este caso requiere intervención de VictorIA**

Su solicitud ha sido escalada para revisión manual:
- **Ticket ID**: {ticket_id}
- **Severidad**: {severity}
- **Tiempo estimado de respuesta**: {estimated_time}

VictorIA revisará su solicitud y tomará las acciones necesarias. Recibirá una notificación cuando se complete.

💡 **Nota**: Las acciones de seguridad críticas requieren aprobación manual para garantizar la seguridad del sistema.
    """.strip()


def check_handoff_status(ticket_id: str) -> Dict:
    """
    Check status of a VictorIA handoff ticket
    
    Args:
        ticket_id: Ticket ID to check
    
    Returns:
        Dict with ticket status
    """
    from victor.client_stub import check_victoria_status
    return check_victoria_status(ticket_id)


def cancel_handoff(ticket_id: str) -> Dict:
    """
    Cancel a VictorIA handoff ticket
    
    Args:
        ticket_id: Ticket ID to cancel
    
    Returns:
        Dict with cancellation status
    """
    from victor.client_stub import cancel_victoria_ticket
    return cancel_victoria_ticket(ticket_id)
