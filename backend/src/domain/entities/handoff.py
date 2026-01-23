from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class HandoffRequest:
    """Signal raised by an agent to transfer control to another agent."""
    target_agent: str
    reason: str
    context: Optional[Dict[str, Any]] = None
