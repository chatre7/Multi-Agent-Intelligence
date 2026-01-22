"""
DomainConfig Entity.

Represents a business domain configuration that groups related agents
and defines routing rules for task assignment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class RoutingRule:
    """
    Routing rule for directing tasks to specific agents.

    Attributes:
        keywords: Keywords that trigger this rule.
        agent: Agent ID to route to when matched.
        priority: Priority for rule matching (lower = higher priority).
    """

    keywords: list[str]
    agent: str
    priority: int = 0

    def matches(self, request_keywords: list[str]) -> bool:
        """
        Check if this rule matches the request keywords.

        Args:
            request_keywords: Keywords from the user request.

        Returns:
            True if any keyword matches.
        """
        rule_keywords_lower = {k.lower() for k in self.keywords}
        request_keywords_lower = {k.lower() for k in request_keywords}
        return bool(rule_keywords_lower.intersection(request_keywords_lower))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "keywords": self.keywords.copy(),
            "agent": self.agent,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoutingRule:
        """Deserialize from dictionary."""
        return cls(
            keywords=data.get("keywords", []),
            agent=data["agent"],
            priority=data.get("priority", 0),
        )


@dataclass
class DomainConfig:
    """
    Domain Configuration Entity - defines a business domain.

    A domain groups related agents together and defines how tasks
    should be routed between them.

    Attributes:
        id: Unique identifier for the domain.
        name: Human-readable name.
        description: Description of the domain's purpose.
        agents: List of agent IDs in this domain.
        default_agent: Default agent for handling tasks.
        workflow_type: Type of workflow (supervisor, sequential, parallel).
        max_iterations: Maximum iterations for workflow execution.
        routing_rules: Rules for routing tasks to agents.
        fallback_agent: Agent to use when no routing rule matches.
        allowed_roles: User roles allowed to access this domain.
        version: Configuration version.
        created_at: When the domain was created.
        updated_at: When the domain was last updated.
        is_active: Whether the domain is currently active.
        metadata: Additional metadata.
    """

    # Required fields
    id: str
    name: str
    description: str
    agents: list[str]
    default_agent: str

    # Optional fields with defaults
    workflow_type: str = "supervisor"
    max_iterations: int = 10
    routing_rules: list[RoutingRule] = field(default_factory=list)
    fallback_agent: str = ""
    allowed_roles: list[str] = field(
        default_factory=lambda: ["user", "developer", "admin"]
    )
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize fallback agent if not set."""
        if not self.fallback_agent:
            self.fallback_agent = self.default_agent

        # Convert dict routing rules to RoutingRule objects
        if self.routing_rules and isinstance(self.routing_rules[0], dict):
            self.routing_rules = [
                RoutingRule.from_dict(r) if isinstance(r, dict) else r
                for r in self.routing_rules
            ]

    def has_agent(self, agent_id: str) -> bool:
        """
        Check if domain contains an agent.

        Args:
            agent_id: The agent ID to check.

        Returns:
            True if agent is in this domain.
        """
        return agent_id in self.agents

    def add_agent(self, agent_id: str) -> None:
        """
        Add an agent to the domain.

        Args:
            agent_id: The agent ID to add.
        """
        if agent_id not in self.agents:
            self.agents.append(agent_id)
            self.updated_at = datetime.now(UTC)

    def remove_agent(self, agent_id: str) -> None:
        """
        Remove an agent from the domain.

        Args:
            agent_id: The agent ID to remove.
        """
        if agent_id in self.agents:
            self.agents.remove(agent_id)
            self.updated_at = datetime.now(UTC)

    def get_agent_for_keywords(self, keywords: list[str]) -> str:
        """
        Get the best agent for handling keywords.

        Evaluates routing rules to find the best matching agent.
        Falls back to default/fallback agent if no match.

        Args:
            keywords: Keywords from the user request.

        Returns:
            Agent ID to handle the request.
        """
        if not keywords:
            return self.default_agent

        # Sort rules by priority (lower = higher priority)
        sorted_rules = sorted(self.routing_rules, key=lambda r: r.priority)

        for rule in sorted_rules:
            if rule.matches(keywords):
                return rule.agent

        return self.fallback_agent

    def is_role_allowed(self, role: str) -> bool:
        """
        Check if a user role is allowed to access this domain.

        Args:
            role: The user role to check.

        Returns:
            True if role is allowed.
        """
        return role.lower() in {r.lower() for r in self.allowed_roles}

    def add_routing_rule(
        self,
        keywords: list[str],
        agent: str,
        priority: int = 0,
    ) -> None:
        """
        Add a routing rule to the domain.

        Args:
            keywords: Keywords that trigger this rule.
            agent: Agent ID to route to.
            priority: Rule priority.
        """
        rule = RoutingRule(keywords=keywords, agent=agent, priority=priority)
        self.routing_rules.append(rule)
        self.updated_at = datetime.now(UTC)

    def validate(self) -> list[str]:
        """
        Validate domain configuration.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        if not self.id:
            errors.append("Domain ID is required")

        if not self.name:
            errors.append("Domain name is required")

        if not self.agents:
            errors.append("Domain must have at least one agent")

        if self.default_agent and self.default_agent not in self.agents:
            errors.append(f"Default agent '{self.default_agent}' not in agents list")

        if self.fallback_agent and self.fallback_agent not in self.agents:
            errors.append(f"Fallback agent '{self.fallback_agent}' not in agents list")

        if self.workflow_type not in {
            "supervisor",
            "sequential",
            "parallel",
            "consensus",
        }:
            errors.append(f"Invalid workflow type: {self.workflow_type}")

        if self.max_iterations < 1:
            errors.append("Max iterations must be at least 1")

        # Validate routing rules reference valid agents
        for i, rule in enumerate(self.routing_rules):
            if rule.agent not in self.agents:
                errors.append(
                    f"Routing rule {i} references unknown agent: {rule.agent}"
                )

        return errors

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize domain to dictionary.

        Returns:
            Dictionary representation of the domain.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agents": self.agents.copy(),
            "default_agent": self.default_agent,
            "workflow_type": self.workflow_type,
            "max_iterations": self.max_iterations,
            "routing_rules": [r.to_dict() for r in self.routing_rules],
            "fallback_agent": self.fallback_agent,
            "allowed_roles": self.allowed_roles.copy(),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainConfig:
        """
        Deserialize domain from dictionary.

        Args:
            data: Dictionary containing domain data.

        Returns:
            DomainConfig instance.
        """
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

        # Parse routing rules
        routing_rules = [
            RoutingRule.from_dict(r) if isinstance(r, dict) else r
            for r in data.get("routing_rules", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            agents=data.get("agents", []),
            default_agent=data.get("default_agent", ""),
            workflow_type=data.get("workflow_type", "supervisor"),
            max_iterations=data.get("max_iterations", 10),
            routing_rules=routing_rules,
            fallback_agent=data.get("fallback_agent", ""),
            allowed_roles=data.get("allowed_roles", ["user", "developer", "admin"]),
            version=data.get("version", "1.0.0"),
            created_at=created_at,
            updated_at=updated_at,
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """String representation."""
        return f"DomainConfig({self.id}: {self.name})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"DomainConfig(id='{self.id}', name='{self.name}', "
            f"agents={len(self.agents)}, workflow_type='{self.workflow_type}')"
        )
