"""
Configuration bundle.

Aggregates loaded domain/agent/tool configs for the application layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig
from src.domain.entities.tool import Tool


@dataclass(frozen=True)
class ConfigBundle:
    """In-memory configuration snapshot."""

    domains: dict[str, DomainConfig]
    agents: dict[str, Agent]
    tools: dict[str, Tool]
