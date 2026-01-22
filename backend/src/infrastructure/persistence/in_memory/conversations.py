"""In-memory conversation repository (MVP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.repositories.conversation_repository import IConversationRepository


def _cursor_for(conversation: Conversation) -> str:
    return f"{conversation.updated_at.isoformat()}|{conversation.id}"


@dataclass
class InMemoryConversationRepository(IConversationRepository):
    _conversations: dict[str, Conversation] = field(default_factory=dict)
    _messages_by_conversation: dict[str, list[Message]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def create_conversation(self, conversation: Conversation) -> None:
        with self._lock:
            self._conversations[conversation.id] = conversation
            self._messages_by_conversation.setdefault(conversation.id, [])

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            return self._conversations.get(conversation_id)

    def add_message(self, message: Message) -> None:
        with self._lock:
            if message.conversation_id not in self._conversations:
                raise KeyError("Unknown conversation_id")
            self._messages_by_conversation.setdefault(
                message.conversation_id, []
            ).append(message)
            self._conversations[message.conversation_id].touch()

    def list_messages(self, conversation_id: str, limit: int = 200) -> list[Message]:
        with self._lock:
            msgs = list(self._messages_by_conversation.get(conversation_id, []))
        return msgs[: int(limit)]

    def list_conversations(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        domain_id: str | None = None,
        created_by_sub: str | None = None,
    ) -> list[Conversation]:
        with self._lock:
            conversations = list(self._conversations.values())

        if domain_id is not None:
            conversations = [c for c in conversations if c.domain_id == domain_id]
        if created_by_sub is not None:
            conversations = [
                c for c in conversations if c.created_by_sub == created_by_sub
            ]

        conversations.sort(key=lambda c: c.updated_at, reverse=True)

        start_index = 0
        if cursor:
            cursor = cursor.strip().replace(" ", "+")
            for index, convo in enumerate(conversations):
                if _cursor_for(convo) == cursor:
                    start_index = index + 1
                    break

        return conversations[start_index : start_index + int(limit)]

    def get_next_cursor(
        self, conversations: list[Conversation], *, has_more: bool
    ) -> str | None:
        if not has_more or not conversations:
            return None
        return _cursor_for(conversations[-1])
