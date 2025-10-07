from typing import Dict, Any, List
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

class RAGSearchTool:
    """Tool for searching company-specific vector stores"""
    
    def __init__(self, search_endpoint: str, search_key: str):
        self.search_endpoint = search_endpoint
        self.search_key = search_key
    
    def search(self, company_id: int, vector_store_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search in company-specific vector store
        
        Args:
            company_id: Company identifier
            vector_store_id: Azure vector store ID
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with content and metadata
        """
        try:
            if not self.search_endpoint or not self.search_key:
                return [{
                    "content": "RAG search not configured. Please configure Azure Search credentials.",
                    "score": 0.0,
                    "metadata": {}
                }]
            
            index_name = f"company-{company_id}-{vector_store_id}"
            
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=index_name,
                credential=AzureKeyCredential(self.search_key)
            )
            
            results = search_client.search(
                search_text=query,
                top=top_k,
                select=["content", "metadata", "title"]
            )
            
            documents = []
            for result in results:
                documents.append({
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "score": result.get("@search.score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return documents if documents else [{
                "content": "No relevant documents found in knowledge base.",
                "score": 0.0,
                "metadata": {}
            }]
            
        except Exception as e:
            return [{
                "content": f"RAG search error: {str(e)}",
                "score": 0.0,
                "metadata": {"error": True}
            }]
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for Azure AI Agent Framework"""
        return {
            "type": "function",
            "function": {
                "name": "rag_search",
                "description": "Search the company's security knowledge base for relevant documentation and information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documentation"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
