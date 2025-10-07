from typing import Dict, Any
import requests

class CreateTicketTool:
    """Tool for creating tickets to hand off to VICTORIA agent"""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
    
    def create_ticket(
        self,
        company_id: int,
        user_id: int,
        title: str,
        description: str,
        priority: str,
        auth_token: str
    ) -> Dict[str, Any]:
        """
        Create a ticket for VICTORIA to handle infrastructure/provisioning actions
        
        Args:
            company_id: Company identifier
            user_id: User identifier
            title: Ticket title
            description: Detailed description of the request
            priority: Ticket priority (low, medium, high, critical)
            auth_token: JWT token for backend authentication
            
        Returns:
            Created ticket information
        """
        try:
            response = requests.post(
                f"{self.backend_url}/victoria/report",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "company_id": company_id,
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "source": "SOPHIA_HANDOFF",
                    "type": "infrastructure"
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "ticket_id": data.get("ticket_id"),
                    "message": "Ticket created successfully. VICTORIA will handle this request.",
                    "ticket": data.get("ticket", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create ticket: {response.status_code}",
                    "message": "Unable to escalate request to VICTORIA"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error communicating with backend ticket system"
            }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for Azure AI Agent Framework"""
        return {
            "type": "function",
            "function": {
                "name": "create_ticket",
                "description": "Create a ticket to hand off infrastructure, provisioning, or action requests to VICTORIA agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Brief title describing the action needed"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of what the user needs (include context from conversation)"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Priority level based on urgency"
                        }
                    },
                    "required": ["title", "description", "priority"]
                }
            }
        }
