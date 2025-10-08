"""
RAG (Retrieval-Augmented Generation) Tools for SOPHIA
Integrates with Azure AI Search for knowledge retrieval
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RAGTool:
    """RAG tool for knowledge retrieval using Azure AI Search"""
    
    def __init__(
        self,
        search_endpoint: Optional[str] = None,
        search_key: Optional[str] = None,
        index_name: str = "knowledge-base"
    ):
        self.search_endpoint = search_endpoint
        self.search_key = search_key
        self.index_name = index_name
        self.search_client = None
        
        if search_endpoint and search_key:
            try:
                from azure.search.documents import SearchClient
                from azure.core.credentials import AzureKeyCredential
                
                self.search_client = SearchClient(
                    endpoint=search_endpoint,
                    index_name=index_name,
                    credential=AzureKeyCredential(search_key)
                )
                logger.info(f"RAG initialized with Azure AI Search: {search_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure AI Search: {e}")
                self.search_client = None
        else:
            logger.info("RAG initialized in mock mode (no Azure Search credentials)")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search knowledge base for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant documents
        """
        if self.search_client:
            return self._search_azure(query, top_k)
        else:
            return self._search_mock(query, top_k)
    
    def _search_azure(self, query: str, top_k: int) -> List[Dict]:
        """Search using Azure AI Search"""
        try:
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                include_total_count=True
            )
            
            documents = []
            for result in results:
                documents.append({
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "score": result.get("@search.score", 0),
                    "metadata": {
                        "source": result.get("source", "unknown"),
                        "category": result.get("category", "general")
                    }
                })
            
            logger.info(f"Azure Search returned {len(documents)} results for query: {query}")
            return documents
        
        except Exception as e:
            logger.error(f"Azure Search error: {e}")
            return self._search_mock(query, top_k)
    
    def _search_mock(self, query: str, top_k: int) -> List[Dict]:
        """Mock search for testing without Azure"""
        logger.info(f"[MOCK RAG] Searching for: {query}")
        
        # Mock knowledge base
        mock_knowledge = [
            {
                "content": "SOPHIA is a multi-tenant AI agent for cybersecurity operations. It can analyze security alerts, provide threat intelligence, and coordinate incident response.",
                "title": "SOPHIA Overview",
                "score": 0.95,
                "metadata": {"source": "documentation", "category": "sophia"}
            },
            {
                "content": "To block an IP address, you need to configure firewall rules. This action requires VictorIA approval for security compliance.",
                "title": "IP Blocking Procedures",
                "score": 0.88,
                "metadata": {"source": "security-procedures", "category": "firewall"}
            },
            {
                "content": "Security alerts can be retrieved from Palo Alto Networks, Splunk, Wazuh, and other integrated security tools.",
                "title": "Security Alert Sources",
                "score": 0.82,
                "metadata": {"source": "integrations", "category": "alerts"}
            },
            {
                "content": "High-risk security actions like device quarantine, network isolation, or system shutdown require manual approval through VictorIA escalation.",
                "title": "Security Action Escalation Policy",
                "score": 0.79,
                "metadata": {"source": "policies", "category": "escalation"}
            },
            {
                "content": "System metrics and performance data can be monitored through Grafana dashboards. Key metrics include CPU, memory, disk usage, and network throughput.",
                "title": "System Monitoring",
                "score": 0.75,
                "metadata": {"source": "monitoring", "category": "metrics"}
            }
        ]
        
        # Simple keyword matching for mock results
        query_lower = query.lower()
        relevant_docs = []
        
        for doc in mock_knowledge:
            if any(word in doc["content"].lower() or word in doc["title"].lower() 
                   for word in query_lower.split()):
                relevant_docs.append(doc)
        
        # Return top-k results
        return relevant_docs[:top_k] if relevant_docs else mock_knowledge[:top_k]
    
    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get context for a query by searching and formatting results
        
        Args:
            query: Search query
            max_tokens: Maximum tokens for context (approximate)
        
        Returns:
            Formatted context string
        """
        documents = self.search(query, top_k=5)
        
        if not documents:
            return "No relevant information found in knowledge base."
        
        context_parts = ["**Relevant Information:**\n"]
        total_chars = 0
        max_chars = max_tokens * 4  # Rough approximation
        
        for doc in documents:
            doc_text = f"\n**{doc['title']}** (relevance: {doc['score']:.2f})\n{doc['content']}\n"
            if total_chars + len(doc_text) > max_chars:
                break
            context_parts.append(doc_text)
            total_chars += len(doc_text)
        
        return "\n".join(context_parts)
