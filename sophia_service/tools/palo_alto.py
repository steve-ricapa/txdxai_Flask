from typing import Dict, Any
import requests

class PaloAltoTool:
    """Tool for checking Palo Alto firewall status (read-only)"""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
    
    def get_status(self, company_id: int, integration_id: int, auth_token: str) -> Dict[str, Any]:
        """
        Get Palo Alto firewall status via backend
        
        Args:
            company_id: Company identifier
            integration_id: Palo Alto integration ID
            auth_token: JWT token for backend authentication
            
        Returns:
            Firewall status information
        """
        try:
            response = requests.post(
                f"{self.backend_url}/integrations/{integration_id}/execute",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "action": "get_system_info",
                    "params": {}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("result", {}),
                    "firewall_healthy": data.get("result", {}).get("system-status", "unknown") == "up"
                }
            else:
                return {
                    "success": False,
                    "error": f"Palo Alto status check failed: {response.status_code}",
                    "firewall_healthy": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "firewall_healthy": False
            }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for Azure AI Agent Framework"""
        return {
            "type": "function",
            "function": {
                "name": "palo_alto_status",
                "description": "Check Palo Alto firewall system status and health",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "integration_id": {
                            "type": "integer",
                            "description": "The Palo Alto integration ID from the backend"
                        }
                    },
                    "required": ["integration_id"]
                }
            }
        }
