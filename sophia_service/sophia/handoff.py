"""
Handoff Module for VictorIA Integration
Creates ticket stubs and prepares escalation to VictorIA
"""

import logging
from typing import Dict
from datetime import datetime
from victor.ticket_models import TicketDraft, ActionRequest
from victor.client_stub import send_ticket_to_victoria

logger = logging.getLogger(__name__)


def create_ticket_stub(
    action_request: ActionRequest,
    company_id: int,
    user_id: int,
    context: Dict = None
) -> Dict:
    """
    Create a ticket stub for VictorIA escalation
    
    Args:
        action_request: Detected action request from user
        company_id: Company ID
        user_id: User ID
        context: Additional context (conversation history, system state, etc.)
    
    Returns:
        Dict with ticket info and VictorIA response
    """
    # Create ticket draft
    ticket = TicketDraft(
        subject=f"Security Action Request: {action_request.action_type}",
        description=f"""
User requested action: {action_request.original_message}

Detected Intent: {action_request.intent}
Action Type: {action_request.action_type}
Parameters: {action_request.parameters}
Requires Escalation: {action_request.requires_escalation}

This action requires manual review and execution by VictorIA.
        """.strip(),
        severity=_determine_severity(action_request),
        context=context or {},
        company_id=company_id,
        user_id=user_id,
        metadata={
            "action_type": action_request.action_type,
            "parameters": action_request.parameters,
            "created_by": "SOPHIA",
            "auto_escalated": action_request.requires_escalation
        }
    )
    
    # Send to VictorIA (stub)
    victoria_response = send_ticket_to_victoria(ticket)
    
    logger.info(f"Created ticket stub for company {company_id}: {victoria_response.get('ticket_id')}")
    
    return {
        "ticket": ticket.to_dict(),
        "victoria_response": victoria_response,
        "escalation_message": _create_escalation_message(ticket, victoria_response)
    }


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


def _create_escalation_message(ticket: TicketDraft, victoria_response: Dict) -> str:
    """Create user-friendly escalation message"""
    ticket_id = victoria_response.get('ticket_id', 'UNKNOWN')
    estimated_time = victoria_response.get('estimated_response_time', 'shortly')
    
    return f"""
🎫 **Este caso requiere intervención de VictorIA**

Su solicitud ha sido escalada para revisión manual:
- **Ticket ID**: {ticket_id}
- **Severidad**: {ticket.severity}
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
