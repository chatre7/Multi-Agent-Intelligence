"""
Agent Entity.

Core domain entity representing a configurable AI agent in the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..value_objects.agent_state import AgentState
from ..value_objects.version import SemanticVersion


@dataclass
class Agent:
    """
    Core Agent Entity - represents a configurable AI agent.

    Agents are the primary workers in the multi-agent system. Each agent
    has specific capabilities, tools, and routing keywords that determine
    when it should handle a task.

    Attributes:
        id: Unique identifier for the agent.
        name: Human-readable name.
        domain_id: ID of the domain this agent belongs to.
        description: Description of the agent's purpose.
        version: Semantic version of the agent configuration.
        state: Current lifecycle state (development, testing, production, etc.).
        system_prompt: The system prompt used to configure the LLM.
        capabilities: List of capabilities this agent has.
        tools: List of tool IDs this agent can use.
        model_name: Name of the LLM model to use.
        temperature: LLM temperature setting.
        max_tokens: Maximum tokens for LLM response.
        timeout_seconds: Timeout for agent operations.
        keywords: Keywords used for routing tasks to this agent.
        priority: Priority for routing when multiple agents match.
        author: Author of this agent configuration.
        created_at: When the agent was created.
        updated_at: When the agent was last updated.
        test_results: Results from testing this agent.
        performance_metrics: Performance metrics for this agent.
    """

    # Required fields
    id: str
    name: str
    domain_id: str
    description: str
    version: SemanticVersion
    state: AgentState
    system_prompt: str
    capabilities: list[str]
    tools: list[str]
    model_name: str

    # Optional fields with defaults
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout_seconds: float = 120.0
    keywords: list[str] = field(default_factory=list)
    priority: int = 0
    author: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    test_results: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, Any] = field(default_factory=dict)

    def can_handle(self, intent: str, keywords: list[str]) -> float:
        """
        Calculate confidence score for handling a request.

        Matches provided keywords against agent's routing keywords
        to determine suitability for handling a task.

        Args:
            intent: The classified intent of the request.
            keywords: Keywords extracted from the request.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if not self.keywords or not keywords:
            return 0.0

        agent_keywords_lower = {k.lower() for k in self.keywords}
        request_keywords_lower = {k.lower() for k in keywords}

        matches = agent_keywords_lower.intersection(request_keywords_lower)

        if not matches:
            return 0.0

        # Calculate score based on match ratio
        score = len(matches) * 0.2
        return min(score, 1.0)

    def promote(self, target_state: AgentState) -> None:
        """
        Promote agent to target state with validation.

        Validates that the transition is allowed according to the
        agent lifecycle state machine.

        Args:
            target_state: The target state to transition to.

        Raises:
            ValueError: If the transition is not allowed.
        """
        if not self.state.can_transition_to(target_state):
            raise ValueError(
                f"Invalid state transition from {self.state.value} to "
                f"{target_state.value}. Check valid transitions."
            )

        self.state = target_state
        self.updated_at = datetime.now(UTC)

    def has_capability(self, capability: str) -> bool:
        """
        Check if agent has a specific capability.

        Args:
            capability: The capability to check.

        Returns:
            True if agent has the capability.
        """
        return capability.lower() in {c.lower() for c in self.capabilities}

    def has_tool(self, tool_id: str) -> bool:
        """
        Check if agent has access to a specific tool.

        Args:
            tool_id: The tool ID to check.

        Returns:
            True if agent can use the tool.
        """
        return tool_id in self.tools

    def add_tool(self, tool_id: str) -> None:
        """
        Add a tool to the agent's available tools.

        Args:
            tool_id: The tool ID to add.
        """
        if tool_id not in self.tools:
            self.tools.append(tool_id)
            self.updated_at = datetime.now(UTC)

    def remove_tool(self, tool_id: str) -> None:
        """
        Remove a tool from the agent's available tools.

        Args:
            tool_id: The tool ID to remove.
        """
        if tool_id in self.tools:
            self.tools.remove(tool_id)
            self.updated_at = datetime.now(UTC)

    def update_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Update performance metrics.

        Args:
            metrics: Dictionary of metrics to update.
        """
        self.performance_metrics.update(metrics)
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize agent to dictionary.

        Returns:
            Dictionary representation of the agent.
        """
        return {
            "id": self.id,
            "name": self.name,
            "domain_id": self.domain_id,
            "description": self.description,
            "version": str(self.version),
            "state": self.state.value,
            "system_prompt": self.system_prompt,
            "capabilities": self.capabilities.copy(),
            "tools": self.tools.copy(),
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "keywords": self.keywords.copy(),
            "priority": self.priority,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "test_results": self.test_results.copy(),
            "performance_metrics": self.performance_metrics.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        """
        Deserialize agent from dictionary.

        Args:
            data: Dictionary containing agent data.

        Returns:
            Agent instance.
        """
        # Parse version
        version = data.get("version", "1.0.0")
        if isinstance(version, str):
            version = SemanticVersion.from_string(version)

        # Parse state
        state = data.get("state", "development")
        if isinstance(state, str):
            state = AgentState.from_string(state)

        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(UTC)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        elif updated_at is None:
            updated_at = datetime.now(UTC)

        return cls(
            id=data["id"],
            name=data["name"],
            domain_id=data["domain_id"],
            description=data.get("description", ""),
            version=version,
            state=state,
            system_prompt=data.get("system_prompt", ""),
            capabilities=data.get("capabilities", []),
            tools=data.get("tools", []),
            model_name=data.get("model_name", "gpt-oss:120b-cloud"),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens", 4096),
            timeout_seconds=data.get("timeout_seconds", 120.0),
            keywords=data.get("keywords", []),
            priority=data.get("priority", 0),
            author=data.get("author", "system"),
            created_at=created_at,
            updated_at=updated_at,
            test_results=data.get("test_results", {}),
            performance_metrics=data.get("performance_metrics", {}),
        )

    def __str__(self) -> str:
        """String representation."""
        return f"Agent({self.id}: {self.name} [{self.state.value}])"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Agent(id='{self.id}', name='{self.name}', "
            f"domain_id='{self.domain_id}', state={self.state})"
        )
