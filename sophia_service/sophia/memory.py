"""
Memory and Session Management for SOPHIA
Handles thread creation, session persistence, and conversation context
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Stores conversation context for a session"""
    thread_id: str
    company_id: int
    user_id: int
    messages: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_updated = datetime.utcnow()
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """Get recent messages from conversation"""
        return self.messages[-limit:] if self.messages else []


class MemoryManager:
    """Manages conversation memory and threading"""
    
    def __init__(self):
        self._sessions: Dict[str, ConversationContext] = {}
        self._company_threads: Dict[int, List[str]] = {}
    
    def create_thread(self, company_id: int, user_id: int) -> str:
        """Create new conversation thread"""
        import secrets
        thread_id = f"thread_{company_id}_{secrets.token_hex(8)}"
        
        context = ConversationContext(
            thread_id=thread_id,
            company_id=company_id,
            user_id=user_id
        )
        
        self._sessions[thread_id] = context
        
        if company_id not in self._company_threads:
            self._company_threads[company_id] = []
        self._company_threads[company_id].append(thread_id)
        
        logger.info(f"Created new thread {thread_id} for company {company_id}")
        return thread_id
    
    def get_context(self, thread_id: str) -> Optional[ConversationContext]:
        """Get conversation context by thread ID"""
        return self._sessions.get(thread_id)
    
    def add_message(self, thread_id: str, role: str, content: str):
        """Add message to thread"""
        context = self.get_context(thread_id)
        if context:
            context.add_message(role, content)
        else:
            logger.warning(f"Thread {thread_id} not found for adding message")
    
    def get_company_threads(self, company_id: int) -> List[str]:
        """Get all thread IDs for a company"""
        return self._company_threads.get(company_id, [])
    
    def clear_thread(self, thread_id: str):
        """Clear a specific thread"""
        if thread_id in self._sessions:
            context = self._sessions[thread_id]
            company_id = context.company_id
            
            del self._sessions[thread_id]
            
            if company_id in self._company_threads:
                self._company_threads[company_id] = [
                    tid for tid in self._company_threads[company_id] if tid != thread_id
                ]
            
            logger.info(f"Cleared thread {thread_id}")
    
    def clear_company_threads(self, company_id: int):
        """Clear all threads for a company"""
        threads = self.get_company_threads(company_id)
        for thread_id in threads:
            if thread_id in self._sessions:
                del self._sessions[thread_id]
        
        if company_id in self._company_threads:
            del self._company_threads[company_id]
        
        logger.info(f"Cleared all threads for company {company_id}")


# Global memory manager instance
memory_manager = MemoryManager()
