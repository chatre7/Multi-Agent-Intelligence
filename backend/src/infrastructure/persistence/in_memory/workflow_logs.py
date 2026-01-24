from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from src.domain.entities.workflow_log import WorkflowLog
from src.domain.repositories.workflow_log_repository import IWorkflowLogRepository

@dataclass
class InMemoryWorkflowLogRepository(IWorkflowLogRepository):
    """In-memory repository for workflow logs."""
    _logs: List[WorkflowLog] = field(default_factory=list)

    def save(self, log: WorkflowLog) -> None:
        self._logs.append(log)

    def list_by_conversation(self, conversation_id: str, limit: int = 100) -> List[WorkflowLog]:
        return [l for l in self._logs if l.conversation_id == conversation_id][-limit:]

    def delete(self, log_id: str) -> None:
        self._logs = [l for l in self._logs if l.id != log_id]
