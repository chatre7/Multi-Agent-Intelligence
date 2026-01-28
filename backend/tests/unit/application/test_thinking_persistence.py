"""Unit tests for thought persistence in SendMessageUseCase."""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import UTC, datetime
from src.application.use_cases.conversations.send_message import (
    SendMessageRequest,
    SendMessageUseCase,
    SendMessageStreamEvent
)
from src.domain.entities.message import Message
from src.infrastructure.persistence.in_memory.conversations import InMemoryConversationRepository
from src.infrastructure.config.yaml_loader import YamlConfigLoader

@pytest.mark.asyncio
async def test_stream_accumulates_and_persists_thoughts() -> None:
    # 1. Setup mocks
    loader = YamlConfigLoader.from_default_backend_root()
    graph_builder = MagicMock()
    mock_graph = MagicMock()
    graph_builder.build.return_value = mock_graph
    
    # Simulate graph streaming states with thoughts
    def mock_graph_stream(*args, **kwargs):
        # Initial state
        yield {"messages": [], "thoughts": [], "selected_agent": "storyteller"}
        # State with a thought
        yield {
            "messages": [], 
            "thoughts": [{"thought": "I should tell a story"}],
            "selected_agent": "storyteller"
        }
        # Final state with assistant message
        yield {
            "messages": [{"role": "assistant", "content": "Once upon a time..."}],
            "thoughts": [{"thought": "I should tell a story"}],
            "selected_agent": "storyteller"
        }

    mock_graph.stream = mock_graph_stream
    
    repo = InMemoryConversationRepository()
    use_case = SendMessageUseCase(
        loader=loader,
        graph_builder=graph_builder,
        llm=MagicMock(), # LLM won't be used since graph provides message
        conversation_repo=repo
    )

    request = SendMessageRequest(
        domain_id="software_development",
        message="tell me a story",
        conversation_id="test-conv"
    )

    # 2. Execute stream
    events = []
    async for event in use_case.stream(request):
        events.append(event)

    # 3. Verify
    # Check that 'thought' event was yielded
    thought_events = [e for e in events if e.type == "thought"]
    assert len(thought_events) == 1
    assert thought_events[0].text == "I should tell a story"

    # Check persistence in repository
    messages = repo.list_messages("test-conv")
    assistant_msg = next(m for m in messages if m.role == "assistant")
    
    assert "thoughts" in assistant_msg.metadata
    assert len(assistant_msg.metadata["thoughts"]) == 1
    assert assistant_msg.metadata["thoughts"][0]["content"] == "I should tell a story"
    assert assistant_msg.metadata["thoughts"][0]["agentName"] == "storyteller"
