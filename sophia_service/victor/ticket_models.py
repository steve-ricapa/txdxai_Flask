"""
Ticket data models for VictorIA handoff
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class TicketDraft:
    """Draft ticket for VictorIA escalation"""
    subject: str
    description: str
    severity: str = "medium"
    context: Dict = field(default_factory=dict)
    company_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "subject": self.subject,
            "description": self.description,
            "severity": self.severity,
            "context": self.context,
            "company_id": self.company_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ActionRequest:
    """Action request from user"""
    intent: str
    action_type: str
    parameters: Dict = field(default_factory=dict)
    original_message: str = ""
    requires_escalation: bool = False
