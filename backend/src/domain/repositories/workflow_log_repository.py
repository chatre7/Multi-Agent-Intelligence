from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.workflow_log import WorkflowLog

class IWorkflowLogRepository(ABC):
    @abstractmethod
    def save(self, log: WorkflowLog) -> None:
        """Save a workflow log."""
        pass

    @abstractmethod
    def list_by_conversation(self, conversation_id: str, limit: int = 100) -> List[WorkflowLog]:
        """List workflow logs for a conversation."""
        pass

    @abstractmethod
    def delete(self, log_id: str) -> None:
        """Delete a workflow log."""
        pass
