from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class KnowledgeDocument:
    id: str
    filename: str
    content: str
    content_type: str
    size_bytes: int
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "processed"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API details (excluding specific massive content if needed, but keeping it simple for now)."""
        return {
            "id": self.id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "metadata": self.metadata
        }
