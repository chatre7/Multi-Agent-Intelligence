"""Repository interface for conversations and messages."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message


class IConversationRepository(ABC):
    """Port for persisting conversations and messages."""

    @abstractmethod
    def create_conversation(self, conversation: Conversation) -> None:
        """Persist new conversation."""

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Fetch conversation."""

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Persist a message."""

    @abstractmethod
    def list_messages(self, conversation_id: str, limit: int = 200) -> list[Message]:
        """List messages in chronological order."""

    @abstractmethod
    def list_conversations(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        domain_id: str | None = None,
        created_by_sub: str | None = None,
    ) -> list[Conversation]:
        """List conversations by most recent updated_at."""

    @abstractmethod
    def get_next_cursor(
        self, conversations: list[Conversation], *, has_more: bool
    ) -> str | None:
        """Return a cursor for the next page if available."""
