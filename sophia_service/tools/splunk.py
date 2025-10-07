from typing import Dict, Any
import requests

class SplunkTool:
    """Tool for querying Splunk (read-only)"""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
    
    def query(self, company_id: int, integration_id: int, query: str, auth_token: str) -> Dict[str, Any]:
        """
        Execute read-only Splunk query via backend
        
        Args:
            company_id: Company identifier
            integration_id: Splunk integration ID
            query: Splunk search query
            auth_token: JWT token for backend authentication
            
        Returns:
            Query results
        """
        try:
            response = requests.post(
                f"{self.backend_url}/integrations/{integration_id}/execute",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "action": "search",
                    "params": {
                        "query": query,
                        "earliest_time": "-24h",
                        "latest_time": "now"
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "results": data.get("results", []),
                    "count": len(data.get("results", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"Splunk query failed: {response.status_code}",
                    "results": []
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for Azure AI Agent Framework"""
        return {
            "type": "function",
            "function": {
                "name": "splunk_query",
                "description": "Execute read-only Splunk queries to search security logs and events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "integration_id": {
                            "type": "integer",
                            "description": "The Splunk integration ID from the backend"
                        },
                        "query": {
                            "type": "string",
                            "description": "Splunk search query (SPL syntax)"
                        }
                    },
                    "required": ["integration_id", "query"]
                }
            }
        }
