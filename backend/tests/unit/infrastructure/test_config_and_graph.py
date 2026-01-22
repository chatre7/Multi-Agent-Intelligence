"""Unit tests for config loading and graph execution (MVP)."""

from __future__ import annotations

from src.infrastructure.config import YamlConfigLoader
from src.infrastructure.langgraph import ConversationGraphBuilder


def test_yaml_loader_loads_sample_configs() -> None:
    loader = YamlConfigLoader.from_default_backend_root()
    bundle = loader.load_bundle()

    assert "software_development" in bundle.domains
    assert "coder" in bundle.agents
    assert "save_file" in bundle.tools


def test_graph_builder_routes_and_replies() -> None:
    loader = YamlConfigLoader.from_default_backend_root()
    bundle = loader.load_bundle()

    domain = bundle.domains["software_development"]
    graph = ConversationGraphBuilder().build(domain, bundle.agents)

    state = {
        "domain_id": domain.id,
        "messages": [{"role": "user", "content": "Please debug this error traceback"}],
    }
    result = graph.invoke(state)

    assert result["selected_agent"] == "coder"
    assert result["messages"][-1]["role"] == "assistant"
    assert result["messages"][-1]["content"].startswith("[Coder]")


def test_fastapi_app_imports() -> None:
    from src.presentation.api.app import create_app

    app = create_app()
    assert app.title == "Multi-Agent Backend"
