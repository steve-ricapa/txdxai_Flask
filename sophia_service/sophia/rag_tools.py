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
                "content": "Un firewall es un sistema de seguridad de red que monitorea y controla el tráfico entrante y saliente basándose en reglas de seguridad predeterminadas. Actúa como una barrera entre una red interna confiable y redes externas no confiables como Internet. Los firewalls pueden ser de hardware, software o una combinación de ambos. Funciones principales: filtrado de paquetes, inspección de estado, prevención de intrusiones y control de aplicaciones.",
                "title": "¿Qué es un Firewall?",
                "score": 0.92,
                "metadata": {"source": "education", "category": "concepts"}
            },
            {
                "content": "Para bloquear una dirección IP, necesitas configurar reglas de firewall. Esta acción requiere aprobación de VictorIA para cumplir con las políticas de seguridad.",
                "title": "Procedimientos de Bloqueo de IP",
                "score": 0.88,
                "metadata": {"source": "security-procedures", "category": "procedures"}
            },
            {
                "content": "Un IDS (Sistema de Detección de Intrusiones) es una herramienta de seguridad que monitorea el tráfico de red en busca de actividades sospechosas y violaciones de políticas. A diferencia de un firewall que bloquea el tráfico, un IDS solo detecta y alerta sobre amenazas. Un IPS (Sistema de Prevención de Intrusiones) va un paso más allá al detectar Y bloquear automáticamente las amenazas.",
                "title": "IDS vs IPS",
                "score": 0.90,
                "metadata": {"source": "education", "category": "concepts"}
            },
            {
                "content": "Un ataque DDoS (Distributed Denial of Service) es un intento malicioso de interrumpir el tráfico normal de un servidor, servicio o red inundándolo con tráfico de Internet. Los ataques DDoS utilizan múltiples sistemas comprometidos como fuentes de tráfico de ataque. Las defensas incluyen rate limiting, filtrado de tráfico, CDN y servicios anti-DDoS especializados.",
                "title": "Ataques DDoS",
                "score": 0.89,
                "metadata": {"source": "education", "category": "threats"}
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
            },
            {
                "content": "Un ransomware es un tipo de malware que cifra los archivos de la víctima y exige un pago (rescate) para restaurar el acceso. Las medidas preventivas incluyen: backups regulares, actualizaciones de seguridad, educación de usuarios, segmentación de red y sistemas de detección de comportamiento anómalo.",
                "title": "Ransomware",
                "score": 0.87,
                "metadata": {"source": "education", "category": "threats"}
            },
            {
                "content": "La autenticación multifactor (MFA) es un método de seguridad que requiere que los usuarios proporcionen dos o más factores de verificación para acceder a un recurso. Los factores pueden ser: algo que sabes (contraseña), algo que tienes (token/teléfono), o algo que eres (biometría). MFA reduce significativamente el riesgo de acceso no autorizado.",
                "title": "Autenticación Multifactor (MFA)",
                "score": 0.86,
                "metadata": {"source": "education", "category": "concepts"}
            }
        ]
        
        # Improved keyword matching with scoring
        query_lower = query.lower()
        query_words = query_lower.split()
        scored_docs = []
        
        for doc in mock_knowledge:
            doc_text = (doc["content"] + " " + doc["title"]).lower()
            
            # Calculate relevance score based on keyword matches
            match_count = sum(1 for word in query_words if word in doc_text and len(word) > 2)
            
            # Bonus for exact phrase match
            if query_lower in doc_text:
                match_count += 10
            
            # Bonus for category match
            if 'métrica' in query_lower and doc['metadata']['category'] == 'metrics':
                match_count += 5
            elif 'alert' in query_lower and doc['metadata']['category'] == 'alerts':
                match_count += 5
            
            # Priority boost for educational/conceptual content when user asks "what is" questions
            if any(phrase in query_lower for phrase in ['qué es', 'que es', 'what is', 'cómo funciona', 'explica', 'explain']):
                if doc['metadata']['category'] in ['concepts', 'education', 'threats']:
                    match_count += 15  # Strong boost for educational content
                elif doc['metadata']['category'] in ['procedures']:
                    match_count -= 5   # Reduce procedural content for conceptual questions
            
            if match_count > 0:
                scored_docs.append((doc, match_count))
        
        # Sort by match count (descending) and return top-k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        relevant_docs = [doc for doc, _ in scored_docs[:top_k]]
        
        # Return relevant docs or top-k from knowledge base
        return relevant_docs if relevant_docs else mock_knowledge[:top_k]
    
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
    
    def generate_natural_response(self, query: str) -> str:
        """
        Generate a natural conversational response based on the query
        
        Args:
            query: User query
        
        Returns:
            Natural language response
        """
        documents = self.search(query, top_k=3)
        
        if not documents:
            return "Lo siento, no tengo información sobre eso en este momento. ¿Hay algo más en lo que pueda ayudarte?"
        
        query_lower = query.lower()
        
        # Detectar tipo de pregunta y generar respuesta apropiada
        if any(word in query_lower for word in ['nombre', 'llamas', 'eres', 'quien', 'quién']):
            # Pregunta sobre identidad
            for doc in documents:
                if 'sophia' in doc['title'].lower() or 'sophia' in doc['content'].lower():
                    return f"Soy SOPHIA, un agente de IA multi-tenant para operaciones de ciberseguridad. Puedo analizar alertas de seguridad, proporcionar inteligencia de amenazas y coordinar la respuesta a incidentes. ¿En qué puedo ayudarte?"
        
        elif any(word in query_lower for word in ['alertas', 'alert', 'avisos', 'notificaciones']):
            # Pregunta sobre alertas
            for doc in documents:
                if 'alert' in doc['content'].lower() or 'alert' in doc['title'].lower():
                    return f"Puedo ayudarte con las alertas de seguridad. {doc['content']}"
            return "Puedo ayudarte con las alertas de seguridad. Las alertas de seguridad pueden obtenerse desde Palo Alto Networks, Splunk, Wazuh y otras herramientas de seguridad integradas."
        
        elif any(word in query_lower for word in ['bloque', 'bloquear', 'firewall']):
            # Pregunta sobre bloqueo
            for doc in documents:
                if 'bloque' in doc['content'].lower() or 'firewall' in doc['content'].lower():
                    return doc['content']
        
        elif any(word in query_lower for word in ['métrica', 'monitoreo', 'rendimiento', 'cpu', 'memoria', 'sistema']):
            # Pregunta sobre métricas
            for doc in documents:
                if 'métrica' in doc['content'].lower() or 'monitoreo' in doc['content'].lower() or 'sistema' in doc['content'].lower():
                    return doc['content']
        
        # Respuesta genérica basada en el documento más relevante
        top_doc = documents[0]
        if top_doc['score'] > 0.7:
            return top_doc['content']
        else:
            return f"Basándome en la información disponible: {top_doc['content']}"
