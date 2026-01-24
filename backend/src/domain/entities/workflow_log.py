from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class WorkflowLog:
    id: str
    conversation_id: str
    agent_id: str
    agent_name: str
    event_type: str
    created_at: datetime
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
