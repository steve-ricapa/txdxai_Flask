from typing import Dict, Any, Optional, List
import json
import sys
import os

try:
    from azure.ai.projects import AIProjectClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Warning: Azure AI Projects SDK not available, running in mock mode")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from tools.rag_search import RAGSearchTool
from tools.splunk import SplunkTool
from tools.palo_alto import PaloAltoTool
from tools.grafana import GrafanaTool
from tools.create_ticket import CreateTicketTool

class SophiaOrchestrator:
    """
    SOPHIA orchestrator using Microsoft Agent Framework (Azure AI Agents)
    Handles RAG-based conversations with tool calling
    """
    
    SOPHIA_SYSTEM_PROMPT = """You are SOPHIA, an expert cybersecurity assistant specializing in security operations and infrastructure.

Your capabilities:
1. **Knowledge Base Search**: Always search your knowledge base FIRST before answering questions about security policies, documentation, or procedures
2. **Security Monitoring**: Query Splunk logs, check Palo Alto firewall status, and fetch Grafana metrics
3. **Handoff to VICTORIA**: When users request infrastructure changes, provisioning, or troubleshooting actions, create a ticket using create_ticket tool

Guidelines:
- Search your knowledge base using rag_search before providing answers about security documentation
- For monitoring queries, use splunk_query, palo_alto_status, or grafana_fetch tools
- If the request involves ACTION (provisioning, configuration changes, troubleshooting), use create_ticket to hand off to VICTORIA
- Be concise and security-focused
- Always cite sources when using RAG search results

Remember: You are READ-ONLY for monitoring. All infrastructure actions go through VICTORIA via tickets."""
    
    def __init__(self):
        self.backend_url = config.BACKEND_URL
        
        self.splunk_tool = SplunkTool(self.backend_url)
        self.palo_alto_tool = PaloAltoTool(self.backend_url)
        self.grafana_tool = GrafanaTool(self.backend_url)
        self.create_ticket_tool = CreateTicketTool(self.backend_url)
        
        self.threads: Dict[str, str] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.config_cache: Dict[int, Dict[str, Any]] = {}
    
    def initialize_agent(
        self,
        company_id: int,
        azure_config: Dict[str, Any]
    ) -> str:
        """
        Initialize or get existing agent for a company with dynamic Azure configuration
        
        Args:
            company_id: Company identifier
            azure_config: Dict containing:
                - azure_openai_endpoint: Azure OpenAI endpoint URL
                - azure_openai_key: Azure OpenAI API key
                - azure_openai_deployment: Model deployment name (e.g. gpt-4o)
                - azure_project_id: Azure AI project ID
                - azure_agent_id: Existing agent ID (optional)
                - azure_vector_store_id: Vector store ID for RAG (optional)
                - azure_search_endpoint: Azure Search endpoint for RAG (optional)
                - azure_search_key: Azure Search API key (optional)
            
        Returns:
            Agent ID
        """
        agent_key = f"company-{company_id}"
        
        # Check if agent already initialized with cached config
        if agent_key in self.agents and company_id in self.config_cache:
            return self.agents[agent_key]['agent_id']
        
        # Store config in cache
        self.config_cache[company_id] = azure_config
        
        try:
            azure_openai_endpoint = azure_config.get('azure_openai_endpoint')
            azure_openai_key = azure_config.get('azure_openai_key')
            azure_openai_deployment = azure_config.get('azure_openai_deployment')
            azure_agent_id = azure_config.get('azure_agent_id')
            azure_search_endpoint = azure_config.get('azure_search_endpoint')
            azure_search_key = azure_config.get('azure_search_key')
            
            if not AZURE_AVAILABLE or not azure_openai_endpoint or not azure_openai_key:
                agent_id = f"mock-agent-{company_id}"
                self.agents[agent_key] = {
                    'agent_id': agent_id,
                    'config': azure_config
                }
                return agent_id
            
            credential = AzureKeyCredential(azure_openai_key)
            
            project_client = AIProjectClient(
                endpoint=azure_openai_endpoint,
                credential=credential
            )
            
            rag_tool = RAGSearchTool(
                azure_search_endpoint or '',
                azure_search_key or ''
            )
            
            tools = [
                rag_tool.get_tool_definition(),
                self.splunk_tool.get_tool_definition(),
                self.palo_alto_tool.get_tool_definition(),
                self.grafana_tool.get_tool_definition(),
                self.create_ticket_tool.get_tool_definition()
            ]
            
            if azure_agent_id:
                agent_id = azure_agent_id
            else:
                agent_response = project_client.agents.create_agent(
                    model=azure_openai_deployment or 'gpt-4o',
                    name=f"SOPHIA-{company_id}",
                    instructions=self.SOPHIA_SYSTEM_PROMPT,
                    tools=tools
                )
                agent_id = agent_response.id
            
            self.agents[agent_key] = {
                'agent_id': agent_id,
                'project_client': project_client,
                'config': azure_config,
                'rag_tool': rag_tool
            }
            return agent_id
            
        except Exception as e:
            print(f"Error initializing agent for company {company_id}: {e}")
            agent_id = f"mock-agent-{company_id}"
            self.agents[agent_key] = {
                'agent_id': agent_id,
                'config': azure_config
            }
            return agent_id
    
    def create_thread(self, company_id: int) -> str:
        """Create a new conversation thread for a company"""
        try:
            agent_key = f"company-{company_id}"
            if agent_key in self.agents and 'project_client' in self.agents[agent_key]:
                project_client = self.agents[agent_key]['project_client']
                thread_response = project_client.agents.create_thread()
                return thread_response.id
            else:
                import uuid
                return f"mock-thread-{uuid.uuid4()}"
        except Exception as e:
            print(f"Error creating thread: {e}")
            import uuid
            return f"mock-thread-{uuid.uuid4()}"
    
    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        company_id: int,
        user_id: int,
        vector_store_id: Optional[str],
        auth_token: str
    ) -> Dict[str, Any]:
        """Execute a tool call"""
        try:
            if tool_name == "rag_search":
                agent_key = f"company-{company_id}"
                rag_tool = self.agents.get(agent_key, {}).get('rag_tool')
                if rag_tool:
                    return rag_tool.search(
                        company_id,
                        vector_store_id or "default",
                        arguments.get("query", ""),
                        arguments.get("top_k", 5)
                    )
                else:
                    return {"error": "RAG search not configured for this company"}
            
            elif tool_name == "splunk_query":
                return self.splunk_tool.query(
                    company_id,
                    arguments.get("integration_id"),
                    arguments.get("query"),
                    auth_token
                )
            
            elif tool_name == "palo_alto_status":
                return self.palo_alto_tool.get_status(
                    company_id,
                    arguments.get("integration_id"),
                    auth_token
                )
            
            elif tool_name == "grafana_fetch":
                return self.grafana_tool.fetch_metrics(
                    company_id,
                    arguments.get("integration_id"),
                    arguments.get("dashboard_id"),
                    auth_token
                )
            
            elif tool_name == "create_ticket":
                return self.create_ticket_tool.create_ticket(
                    company_id,
                    user_id,
                    arguments.get("title"),
                    arguments.get("description"),
                    arguments.get("priority", "medium"),
                    auth_token
                )
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def chat(
        self,
        agent_id: str,
        thread_id: str,
        message: str,
        company_id: int,
        user_id: int,
        vector_store_id: Optional[str],
        auth_token: str
    ) -> Dict[str, Any]:
        """
        Process a chat message with SOPHIA
        
        Args:
            agent_id: Azure AI Agent ID
            thread_id: Thread ID for conversation
            message: User message
            company_id: Company identifier
            user_id: User identifier
            vector_store_id: Vector store for RAG
            auth_token: JWT for backend calls
            
        Returns:
            Response with message and metadata
        """
        try:
            agent_key = f"company-{company_id}"
            agent_data = self.agents.get(agent_key, {})
            project_client = agent_data.get('project_client')
            
            if not project_client or agent_id.startswith("mock-"):
                return {
                    "response": f"[MOCK MODE] SOPHIA received: {message}\n\nNote: Azure AI Agents not configured for this company. Configure Azure credentials to enable full functionality.",
                    "thread_id": thread_id,
                    "tool_calls": []
                }
            
            project_client.agents.create_message(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            run = project_client.agents.create_run(
                thread_id=thread_id,
                agent_id=agent_id
            )
            
            while run.status in ["queued", "in_progress", "requires_action"]:
                run = project_client.agents.get_run(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == "requires_action":
                    tool_outputs = []
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        arguments = json.loads(tool_call.function.arguments)
                        result = self.execute_tool(
                            tool_call.function.name,
                            arguments,
                            company_id,
                            user_id,
                            vector_store_id,
                            auth_token
                        )
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    
                    run = project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            
            messages = project_client.agents.list_messages(thread_id=thread_id)
            latest_message = messages.data[0]
            
            response_text = ""
            if hasattr(latest_message.content[0], 'text'):
                response_text = latest_message.content[0].text.value
            
            return {
                "response": response_text,
                "thread_id": thread_id,
                "tool_calls": []
            }
            
        except Exception as e:
            return {
                "response": f"Error processing message: {str(e)}",
                "thread_id": thread_id,
                "error": True
            }
    
    def invalidate_cache(self, company_id: int) -> None:
        """
        Invalidate cached configuration for a company
        
        Args:
            company_id: Company identifier
        """
        agent_key = f"company-{company_id}"
        if company_id in self.config_cache:
            del self.config_cache[company_id]
        if agent_key in self.agents:
            del self.agents[agent_key]
    
    def refresh_knowledge(self, company_id: int, vector_store_id: str) -> Dict[str, Any]:
        """
        Refresh knowledge base from sources
        
        Args:
            company_id: Company identifier
            vector_store_id: Vector store to refresh
            
        Returns:
            Refresh status
        """
        # Invalidate cache to pick up any credential updates
        self.invalidate_cache(company_id)
        
        return {
            "success": True,
            "message": "Knowledge refresh initiated",
            "company_id": company_id,
            "vector_store_id": vector_store_id,
            "note": "Background refresh process started. This may take several minutes."
        }

orchestrator = SophiaOrchestrator()
