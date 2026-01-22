"""TDD tests for SendMessageUseCase streaming support (MVP)."""

from __future__ import annotations

from src.application.use_cases.conversations.send_message import (
    SendMessageRequest,
    SendMessageUseCase,
)
from src.infrastructure.config.yaml_loader import YamlConfigLoader
from src.infrastructure.langgraph.graph_builder import ConversationGraphBuilder
from src.infrastructure.llm.streaming import DeterministicStreamingLLM
from src.infrastructure.persistence.in_memory.conversations import (
    InMemoryConversationRepository,
)


def test_send_message_stream_yields_deltas_that_reconstruct_reply() -> None:
    loader = YamlConfigLoader.from_default_backend_root()
    use_case = SendMessageUseCase(
        loader=loader,
        graph_builder=ConversationGraphBuilder(),
        llm=DeterministicStreamingLLM(),
        conversation_repo=InMemoryConversationRepository(),
    )

    events = list(
        use_case.stream(
            SendMessageRequest(
                domain_id="software_development",
                message="hello world",
                role="user",
                subject="alice",
            )
        )
    )
    assert events
    assert events[-1].type == "done"
    done = events[-1]
    assert done.response is not None
    assert done.response.reply
    assert done.response.reply.startswith("LLM(")

    reconstructed = "".join(
        e.text for e in events if e.type == "delta" and e.text is not None
    )
    assert reconstructed.strip() == done.response.reply.strip()
