from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.knowledge import KnowledgeDocument

class IKnowledgeRepository(ABC):
    @abstractmethod
    def save(self, document: KnowledgeDocument) -> None:
        pass

    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[KnowledgeDocument]:
        pass

    @abstractmethod
    def list_all(self) -> List[KnowledgeDocument]:
        pass

    @abstractmethod
    def delete(self, document_id: str) -> None:
        pass
