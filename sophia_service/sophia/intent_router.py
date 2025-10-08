"""
Intent Router for SOPHIA
Detects user intent and routes to appropriate handler
"""

import logging
from typing import Dict, Tuple
from victor.ticket_models import ActionRequest

logger = logging.getLogger(__name__)


class IntentRouter:
    """Routes user messages based on detected intent"""
    
    # Action keywords that indicate user wants to perform an action (English & Spanish)
    ACTION_KEYWORDS = {
        "block", "quarantine", "isolate", "shutdown", "disable", "remove",
        "delete", "terminate", "kill", "stop", "ban", "restrict",
        "execute", "run", "deploy", "configure", "change", "modify",
        "bloquea", "bloquear", "cuarentena", "aisla", "aislar", "apaga", "apagar",
        "deshabilita", "deshabilitar", "elimina", "eliminar", "detén", "detener",
        "ejecuta", "ejecutar", "despliega", "desplegar", "configura", "configurar",
        "cambia", "cambiar", "modifica", "modificar", "borra", "borrar"
    }
    
    # Query keywords for informational requests (English & Spanish)
    QUERY_KEYWORDS = {
        "show", "list", "get", "display", "what", "when", "where", "how",
        "status", "check", "see", "view", "tell", "explain", "describe",
        "muestra", "mostrar", "lista", "listar", "obtén", "obtener", "qué", "cuándo",
        "dónde", "cómo", "estado", "verifica", "verificar", "ve", "ver", "dime",
        "explica", "explicar", "describe", "describir", "hay", "cuáles", "cuál"
    }
    
    # High-risk actions that always require VictorIA escalation
    HIGH_RISK_ACTIONS = {
        "block_ip", "quarantine_device", "shutdown_system", "delete_user",
        "disable_firewall", "emergency_response", "isolate_network"
    }
    
    def detect_intent(self, message: str) -> Tuple[str, ActionRequest]:
        """
        Detect user intent from message
        
        Returns:
            Tuple of (intent_type, action_request)
            intent_type: 'query', 'action', or 'unknown'
        """
        message_lower = message.lower()
        words = message_lower.split()
        
        # Check for action keywords
        has_action = any(keyword in message_lower for keyword in self.ACTION_KEYWORDS)
        has_query = any(keyword in message_lower for keyword in self.QUERY_KEYWORDS)
        
        # Determine action type if it's an action intent
        action_type = self._determine_action_type(message_lower)
        requires_escalation = action_type in self.HIGH_RISK_ACTIONS
        
        if has_action and not has_query:
            # Clear action intent
            action_request = ActionRequest(
                intent="action",
                action_type=action_type,
                parameters=self._extract_parameters(message),
                original_message=message,
                requires_escalation=requires_escalation
            )
            return ("action", action_request)
        
        elif has_query or not has_action:
            # Informational query
            action_request = ActionRequest(
                intent="query",
                action_type="information_request",
                parameters={"query": message},
                original_message=message,
                requires_escalation=False
            )
            return ("query", action_request)
        
        else:
            # Unknown or ambiguous
            action_request = ActionRequest(
                intent="unknown",
                action_type="unclear",
                parameters={"message": message},
                original_message=message,
                requires_escalation=False
            )
            return ("unknown", action_request)
    
    def _determine_action_type(self, message: str) -> str:
        """Determine specific action type from message"""
        if "block" in message and "ip" in message:
            return "block_ip"
        elif "quarantine" in message or "isolate" in message:
            return "quarantine_device"
        elif "shutdown" in message or "shut down" in message:
            return "shutdown_system"
        elif "delete" in message and "user" in message:
            return "delete_user"
        elif "disable" in message and "firewall" in message:
            return "disable_firewall"
        elif "emergency" in message:
            return "emergency_response"
        elif "block" in message:
            return "block_resource"
        elif "configure" in message or "change" in message:
            return "configuration_change"
        else:
            return "general_action"
    
    def _extract_parameters(self, message: str) -> Dict:
        """Extract parameters from action message"""
        params = {}
        
        # Simple IP extraction
        import re
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, message)
        if ips:
            params['ip_addresses'] = ips
        
        # Extract device/host names (simple heuristic)
        if "device" in message.lower() or "host" in message.lower():
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["device", "host", "server"] and i + 1 < len(words):
                    params['device_name'] = words[i + 1].strip('.,!?')
        
        # Extract severity if mentioned
        if "critical" in message.lower():
            params['severity'] = "critical"
        elif "high" in message.lower():
            params['severity'] = "high"
        elif "urgent" in message.lower():
            params['severity'] = "urgent"
        
        return params
    
    def should_escalate_to_victoria(self, action_request: ActionRequest) -> bool:
        """Determine if action should be escalated to VictorIA"""
        return action_request.requires_escalation or action_request.intent == "action"


# Global intent router instance
intent_router = IntentRouter()
