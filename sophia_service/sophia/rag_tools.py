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
        
        # Base de conocimiento mock
        mock_knowledge = [
            {
                "content": "SOPHIA es un agente de IA multi-tenant para operaciones de ciberseguridad. Puede analizar alertas de seguridad, proporcionar inteligencia de amenazas y coordinar la respuesta a incidentes.",
                "title": "Resumen de SOPHIA",
                "score": 0.95,
                "metadata": {"source": "documentation", "category": "sophia"}
            },
            {
                "content": "Para bloquear una dirección IP, necesitas configurar reglas de firewall. Esta acción requiere aprobación de VictorIA para cumplir con las políticas de seguridad.",
                "title": "Procedimientos de Bloqueo de IP",
                "score": 0.88,
                "metadata": {"source": "security-procedures", "category": "firewall"}
            },
            {
                "content": "Las alertas de seguridad pueden obtenerse desde Palo Alto Networks, Splunk, Wazuh y otras herramientas de seguridad integradas.",
                "title": "Fuentes de Alertas de Seguridad",
                "score": 0.82,
                "metadata": {"source": "integrations", "category": "alerts"}
            },
            {
                "content": "Las acciones de seguridad de alto riesgo como cuarentena de dispositivos, aislamiento de red o apagado de sistemas requieren aprobación manual a través de escalación a VictorIA.",
                "title": "Política de Escalación de Acciones de Seguridad",
                "score": 0.79,
                "metadata": {"source": "policies", "category": "escalation"}
            },
            {
                "content": "Las métricas del sistema y datos de rendimiento pueden monitorearse a través de dashboards de Grafana. Las métricas clave incluyen CPU, memoria, uso de disco y throughput de red.",
                "title": "Monitoreo de Sistemas",
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
            return "No se encontró información relevante en la base de conocimiento."
        
        context_parts = ["**Información Relevante:**\n"]
        total_chars = 0
        max_chars = max_tokens * 4  # Rough approximation
        
        for doc in documents:
            doc_text = f"\n**{doc['title']}** (relevance: {doc['score']:.2f})\n{doc['content']}\n"
            if total_chars + len(doc_text) > max_chars:
                break
            context_parts.append(doc_text)
            total_chars += len(doc_text)
        
        return "\n".join(context_parts)
