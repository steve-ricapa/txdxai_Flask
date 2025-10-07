from typing import Dict, Any
import requests

class GrafanaTool:
    """Tool for fetching Grafana metrics (read-only)"""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
    
    def fetch_metrics(self, company_id: int, integration_id: int, dashboard_id: str, auth_token: str) -> Dict[str, Any]:
        """
        Fetch Grafana dashboard metrics via backend
        
        Args:
            company_id: Company identifier
            integration_id: Grafana integration ID
            dashboard_id: Dashboard identifier
            auth_token: JWT token for backend authentication
            
        Returns:
            Dashboard metrics and data
        """
        try:
            response = requests.post(
                f"{self.backend_url}/integrations/{integration_id}/execute",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "action": "get_dashboard",
                    "params": {
                        "dashboard_id": dashboard_id
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "metrics": data.get("result", {}),
                    "dashboard_id": dashboard_id
                }
            else:
                return {
                    "success": False,
                    "error": f"Grafana fetch failed: {response.status_code}",
                    "metrics": {}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "metrics": {}
            }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for Azure AI Agent Framework"""
        return {
            "type": "function",
            "function": {
                "name": "grafana_fetch",
                "description": "Fetch metrics and data from Grafana dashboards for monitoring and analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "integration_id": {
                            "type": "integer",
                            "description": "The Grafana integration ID from the backend"
                        },
                        "dashboard_id": {
                            "type": "string",
                            "description": "The Grafana dashboard ID to fetch"
                        }
                    },
                    "required": ["integration_id", "dashboard_id"]
                }
            }
        }
