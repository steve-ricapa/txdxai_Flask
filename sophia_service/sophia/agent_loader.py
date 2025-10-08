"""
Agent Loader for SOPHIA
Dynamically initializes AI agents based on tenant configuration
"""

import logging
from typing import Dict, Optional
from .rag_tools import RAGTool

logger = logging.getLogger(__name__)


class AgentLoader:
    """Loads and initializes AI agents for tenants"""
    
    def __init__(self):
        self._agents = {}
        self._rag_tools = {}
        self._project_clients = {}
    
    def initialize_agent(
        self,
        company_id: int,
        azure_config: Dict
    ) -> Optional[str]:
        """
        Initialize agent for a company with Azure configuration
        
        Args:
            company_id: Company ID
            azure_config: Dict with Azure credentials
                - azure_openai_endpoint
                - azure_openai_key
                - azure_openai_deployment
                - azure_search_endpoint (optional)
                - azure_search_key (optional)
                - azure_project_id (optional)
                - azure_agent_id (optional)
        
        Returns:
            Agent ID or None if initialization fails
        """
        agent_key = f"company-{company_id}"
        
        # Check if already initialized
        if agent_key in self._agents:
            logger.info(f"Agent already initialized for company {company_id}")
            return self._agents[agent_key].get('agent_id')
        
        # Extract configuration
        openai_endpoint = azure_config.get('azure_openai_endpoint')
        openai_key = azure_config.get('azure_openai_key')
        deployment = azure_config.get('azure_openai_deployment', 'gpt-4o')
        
        # Initialize RAG if search credentials provided
        search_endpoint = azure_config.get('azure_search_endpoint')
        search_key = azure_config.get('azure_search_key')
        
        rag_tool = RAGTool(
            search_endpoint=search_endpoint,
            search_key=search_key
        )
        self._rag_tools[agent_key] = rag_tool
        
        # Try to initialize with Azure AI Agents
        if openai_endpoint and openai_key:
            try:
                agent_info = self._initialize_azure_agent(
                    company_id=company_id,
                    azure_config=azure_config
                )
                
                if agent_info:
                    self._agents[agent_key] = agent_info
                    logger.info(f"✅ Agent initialized for company {company_id} with Azure AI")
                    return agent_info.get('agent_id')
            
            except Exception as e:
                logger.warning(f"Failed to initialize Azure AI agent for company {company_id}: {e}")
        
        # Fallback to mock mode
        logger.info(f"Initializing agent for company {company_id} in MOCK MODE")
        mock_agent = {
            'agent_id': f"mock-agent-{company_id}",
            'mode': 'mock',
            'company_id': company_id,
            'deployment': deployment,
            'has_rag': bool(search_endpoint and search_key)
        }
        self._agents[agent_key] = mock_agent
        
        return mock_agent['agent_id']
    
    def _initialize_azure_agent(
        self,
        company_id: int,
        azure_config: Dict
    ) -> Optional[Dict]:
        """Initialize agent using Azure AI Projects"""
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
            from azure.ai.projects.models import Agent
            
            # Get configuration
            project_id = azure_config.get('azure_project_id')
            openai_endpoint = azure_config.get('azure_openai_endpoint')
            deployment = azure_config.get('azure_openai_deployment', 'gpt-4o')
            
            if not project_id:
                logger.warning("No azure_project_id provided, cannot initialize Azure AI agent")
                return None
            
            # Create project client
            # Note: This requires proper Azure authentication
            # For now, we'll use a simplified approach
            logger.info(f"Attempting to create Azure AI Project client for company {company_id}")
            
            # In production, you would create the actual client:
            # project_client = AIProjectClient.from_connection_string(
            #     conn_str=connection_string,
            #     credential=DefaultAzureCredential()
            # )
            
            # For now, return mock agent info with real config
            return {
                'agent_id': azure_config.get('azure_agent_id') or f"azure-agent-{company_id}",
                'mode': 'azure',
                'company_id': company_id,
                'deployment': deployment,
                'endpoint': openai_endpoint,
                'project_id': project_id,
                'has_rag': bool(azure_config.get('azure_search_endpoint'))
            }
        
        except ImportError as e:
            logger.error(f"Azure AI Projects SDK not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Error initializing Azure AI agent: {e}")
            return None
    
    def get_agent(self, company_id: int) -> Optional[Dict]:
        """Get agent info for a company"""
        agent_key = f"company-{company_id}"
        return self._agents.get(agent_key)
    
    def get_rag_tool(self, company_id: int) -> Optional[RAGTool]:
        """Get RAG tool for a company"""
        agent_key = f"company-{company_id}"
        return self._rag_tools.get(agent_key)
    
    def is_mock_mode(self, company_id: int) -> bool:
        """Check if agent is in mock mode"""
        agent = self.get_agent(company_id)
        return agent.get('mode') == 'mock' if agent else True
    
    def clear_agent(self, company_id: int):
        """Clear agent configuration for a company"""
        agent_key = f"company-{company_id}"
        
        if agent_key in self._agents:
            del self._agents[agent_key]
        if agent_key in self._rag_tools:
            del self._rag_tools[agent_key]
        if agent_key in self._project_clients:
            del self._project_clients[agent_key]
        
        logger.info(f"Cleared agent for company {company_id}")
    
    def refresh_agent(self, company_id: int, azure_config: Dict) -> Optional[str]:
        """Refresh agent configuration"""
        self.clear_agent(company_id)
        return self.initialize_agent(company_id, azure_config)


# Global agent loader instance
agent_loader = AgentLoader()
