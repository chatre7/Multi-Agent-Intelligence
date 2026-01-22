"""TDD tests for SQLite Conversation repository adapter."""

from __future__ import annotations

from uuid import uuid4

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message


def test_sqlite_conversation_repository_roundtrip() -> None:
    from src.infrastructure.persistence.sqlite.conversations import (
        SqliteConversationRepository,
    )

    db_uri = f"file:conversations_{uuid4()}?mode=memory&cache=shared"
    repo = SqliteConversationRepository(db_path=db_uri)

    conversation = Conversation(
        id=str(uuid4()),
        domain_id="software_development",
        created_by_role="user",
    )
    repo.create_conversation(conversation)

    message = Message(
        id=str(uuid4()),
        conversation_id=conversation.id,
        role="user",
        content="hello",
    )
    repo.add_message(message)

    loaded = repo.get_conversation(conversation.id)
    assert loaded is not None
    assert loaded.id == conversation.id
    assert loaded.domain_id == "software_development"

    messages = repo.list_messages(conversation.id, limit=10)
    assert len(messages) == 1
    assert messages[0].content == "hello"
