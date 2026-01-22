"""
AgentState Value Object.

Represents the lifecycle state of an agent in the system.
Implements state machine transitions with validation.
"""

from enum import Enum


class AgentState(Enum):
    """
    Enumeration of possible agent lifecycle states.

    State Transitions:
        DEVELOPMENT -> TESTING -> PRODUCTION -> DEPRECATED -> ARCHIVED
        TESTING -> DEVELOPMENT (demote)
        Any -> DEPRECATED (deprecate)
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

    @classmethod
    def from_string(cls, value: str) -> "AgentState":
        """
        Create AgentState from string value.

        Args:
            value: String representation of the state.

        Returns:
            AgentState enum member.

        Raises:
            ValueError: If the string doesn't match any state.
        """
        value_lower = value.lower().strip()
        for state in cls:
            if state.value == value_lower:
                return state
        valid_states = [s.value for s in cls]
        raise ValueError(
            f"Invalid agent state: '{value}'. Valid states: {valid_states}"
        )

    def can_transition_to(self, target: "AgentState") -> bool:
        """
        Check if transition to target state is valid.

        Args:
            target: The target state to transition to.

        Returns:
            True if transition is valid, False otherwise.
        """
        valid_transitions = self._get_valid_transitions()
        return target in valid_transitions

    def _get_valid_transitions(self) -> set["AgentState"]:
        """
        Get set of valid transition states from current state.

        Returns:
            Set of valid target states.
        """
        transitions = {
            AgentState.DEVELOPMENT: {
                AgentState.TESTING,
                AgentState.DEPRECATED,
            },
            AgentState.TESTING: {
                AgentState.PRODUCTION,
                AgentState.DEVELOPMENT,  # Demote back
                AgentState.DEPRECATED,
            },
            AgentState.PRODUCTION: {
                AgentState.DEPRECATED,
            },
            AgentState.DEPRECATED: {
                AgentState.ARCHIVED,
            },
            AgentState.ARCHIVED: set(),  # Terminal state
        }
        return transitions.get(self, set())

    def is_active(self) -> bool:
        """
        Check if this state represents an active agent.

        Returns:
            True if agent is active (can process requests).
        """
        return self in {
            AgentState.DEVELOPMENT,
            AgentState.TESTING,
            AgentState.PRODUCTION,
        }

    def is_deployable(self) -> bool:
        """
        Check if agent in this state can be deployed.

        Returns:
            True if agent can be used in production.
        """
        return self == AgentState.PRODUCTION

    def __str__(self) -> str:
        """String representation."""
        return self.value
