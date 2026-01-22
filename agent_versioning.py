"""Agent Versioning State Machine.

Implements Microsoft's recommended state machine for agent lifecycle management.
Provides version tracking, environment transitions, and production sealing.
"""

import json
from typing import Dict, List, Optional, Any, NamedTuple
from datetime import datetime, UTC
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class AgentState(Enum):
    """Agent lifecycle states following Microsoft's architecture."""

    DEVELOPMENT = "dev"
    TESTING = "test"
    PRODUCTION = "prod"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class TransitionAction(Enum):
    """Allowed state transition actions."""

    PROMOTE = "promote"
    DEMOTE = "demote"
    DEPRECATE = "deprecate"
    ARCHIVE = "archive"
    ROLLBACK = "rollback"


class ValidationError(Exception):
    """Raised when agent validation fails."""

    pass


class StateTransitionError(Exception):
    """Raised when invalid state transition is attempted."""

    pass


@dataclass
class AgentVersion:
    """Represents a specific version of an agent."""

    agent_name: str
    version: str
    state: AgentState
    created_at: str
    updated_at: str
    promoted_at: Optional[str] = None
    deprecated_at: Optional[str] = None
    archived_at: Optional[str] = None

    # Metadata
    author: str = ""
    description: str = ""
    dependencies: List[str] = None
    test_results: Dict[str, Any] = None
    performance_metrics: Dict[str, Any] = None
    security_scan_results: Dict[str, Any] = None

    # Environment-specific configs
    dev_config: Dict[str, Any] = None
    test_config: Dict[str, Any] = None
    prod_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.test_results is None:
            self.test_results = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.security_scan_results is None:
            self.security_scan_results = {}
        if self.dev_config is None:
            self.dev_config = {}
        if self.test_config is None:
            self.test_config = {}
        if self.prod_config is None:
            self.prod_config = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["state"] = self.state.value  # Convert enum to string
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentVersion":
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["state"] = AgentState(data_copy["state"])
        return cls(**data_copy)


class StateTransition(NamedTuple):
    """Represents a state transition."""

    from_state: AgentState
    to_state: AgentState
    action: TransitionAction
    requires_validation: bool = True
    requires_approval: bool = False


class AgentVersionManager:
    """State machine for managing agent versions and lifecycle.

    Implements Microsoft's recommended versioning workflow:
    dev → test → prod with rollback and sealing capabilities.
    """

    # Define allowed state transitions
    ALLOWED_TRANSITIONS = {
        AgentState.DEVELOPMENT: [
            StateTransition(
                AgentState.DEVELOPMENT,
                AgentState.TESTING,
                TransitionAction.PROMOTE,
                requires_validation=True,
            ),
            StateTransition(
                AgentState.DEVELOPMENT,
                AgentState.DEPRECATED,
                TransitionAction.DEPRECATE,
            ),
        ],
        AgentState.TESTING: [
            StateTransition(
                AgentState.TESTING,
                AgentState.PRODUCTION,
                TransitionAction.PROMOTE,
                requires_validation=True,
                requires_approval=True,
            ),
            StateTransition(
                AgentState.TESTING, AgentState.DEVELOPMENT, TransitionAction.DEMOTE
            ),
            StateTransition(
                AgentState.TESTING, AgentState.DEPRECATED, TransitionAction.DEPRECATE
            ),
        ],
        AgentState.PRODUCTION: [
            StateTransition(
                AgentState.PRODUCTION,
                AgentState.DEPRECATED,
                TransitionAction.DEPRECATE,
                requires_approval=True,
            ),
            # Rollback to testing for hotfixes
            StateTransition(
                AgentState.PRODUCTION,
                AgentState.TESTING,
                TransitionAction.ROLLBACK,
                requires_approval=True,
            ),
        ],
        AgentState.DEPRECATED: [
            StateTransition(
                AgentState.DEPRECATED, AgentState.ARCHIVED, TransitionAction.ARCHIVE
            ),
        ],
    }

    def __init__(self, storage_path: str = "./agent_versions.json"):
        """Initialize version manager.

        Parameters
        ----------
        storage_path : str
            Path to store version data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._versions: Dict[
            str, Dict[str, AgentVersion]
        ] = {}  # agent_name -> {version -> AgentVersion}
        self._current_versions: Dict[str, str] = {}  # agent_name -> current_version
        self._load_versions()

    def create_version(
        self,
        agent_name: str,
        version: str,
        author: str,
        description: str = "",
        dependencies: Optional[List[str]] = None,
    ) -> AgentVersion:
        """Create a new agent version in development state.

        Parameters
        ----------
        agent_name : str
            Name of the agent
        version : str
            Version string (e.g., "1.0.0", "v2.1.3")
        author : str
            Author of the version
        description : str
            Version description
        dependencies : Optional[List[str]]
            List of dependencies

        Returns
        -------
        AgentVersion
            Created agent version
        """
        if agent_name in self._versions and version in self._versions[agent_name]:
            raise ValueError(f"Version {version} already exists for agent {agent_name}")

        now = datetime.now(UTC).isoformat()

        agent_version = AgentVersion(
            agent_name=agent_name,
            version=version,
            state=AgentState.DEVELOPMENT,
            created_at=now,
            updated_at=now,
            author=author,
            description=description,
            dependencies=dependencies or [],
        )

        if agent_name not in self._versions:
            self._versions[agent_name] = {}
        self._versions[agent_name][version] = agent_version

        self._save_versions()
        return agent_version

    def get_version(self, agent_name: str, version: str) -> Optional[AgentVersion]:
        """Get a specific agent version.

        Parameters
        ----------
        agent_name : str
            Name of the agent
        version : str
            Version to retrieve

        Returns
        -------
        Optional[AgentVersion]
            Agent version or None if not found
        """
        return self._versions.get(agent_name, {}).get(version)

    def get_current_version(
        self, agent_name: str, environment: str = "prod"
    ) -> Optional[AgentVersion]:
        """Get current version for an agent in specific environment.

        Parameters
        ----------
        agent_name : str
            Name of the agent
        environment : str
            Environment (dev, test, prod)

        Returns
        -------
        Optional[AgentVersion]
            Current version for the environment
        """
        if agent_name not in self._versions:
            return None

        # Find the highest version in the requested environment state
        env_state_map = {
            "dev": AgentState.DEVELOPMENT,
            "test": AgentState.TESTING,
            "prod": AgentState.PRODUCTION,
        }

        target_state = env_state_map.get(environment, AgentState.PRODUCTION)

        # Get versions in target state, sorted by version (simple string sort)
        versions_in_state = [
            v for v in self._versions[agent_name].values() if v.state == target_state
        ]

        if not versions_in_state:
            return None

        # Return the "latest" version (simple string comparison)
        return max(versions_in_state, key=lambda v: v.version)

    def list_versions(self, agent_name: Optional[str] = None) -> List[AgentVersion]:
        """List all agent versions.

        Parameters
        ----------
        agent_name : Optional[str]
            Filter by agent name, or None for all

        Returns
        -------
        List[AgentVersion]
            List of agent versions
        """
        if agent_name:
            return list(self._versions.get(agent_name, {}).values())
        else:
            return [
                version
                for agent_versions in self._versions.values()
                for version in agent_versions.values()
            ]

    def update_version_metadata(
        self, agent_name: str, version: str, **metadata
    ) -> AgentVersion:
        """Update version metadata.

        Parameters
        ----------
        agent_name : str
            Name of the agent
        version : str
            Version to update
        **metadata
            Metadata fields to update

        Returns
        -------
        AgentVersion
            Updated agent version
        """
        agent_version = self.get_version(agent_name, version)
        if not agent_version:
            raise ValueError(f"Version {version} not found for agent {agent_name}")

        # Update allowed metadata fields
        allowed_fields = [
            "description",
            "dependencies",
            "test_results",
            "performance_metrics",
            "security_scan_results",
            "dev_config",
            "test_config",
            "prod_config",
        ]

        for field in allowed_fields:
            if field in metadata:
                setattr(agent_version, field, metadata[field])

        agent_version.updated_at = datetime.now(UTC).isoformat()
        self._save_versions()
        return agent_version

    def transition_version(
        self,
        agent_name: str,
        version: str,
        action: TransitionAction,
        user: str = "system",
        skip_validation: bool = False,
    ) -> AgentVersion:
        """Transition an agent version to a new state.

        Parameters
        ----------
        agent_name : str
            Name of the agent
        version : str
            Version to transition
        action : TransitionAction
            Transition action to perform
        user : str
            User performing the transition
        skip_validation : bool
            Skip validation checks

        Returns
        -------
        AgentVersion
            Updated agent version
        """
        agent_version = self.get_version(agent_name, version)
        if not agent_version:
            raise ValueError(f"Version {version} not found for agent {agent_name}")

        current_state = agent_version.state

        # Find the transition
        allowed_transitions = self.ALLOWED_TRANSITIONS.get(current_state, [])
        transition = None

        for t in allowed_transitions:
            if t.action == action:
                transition = t
                break

        if not transition:
            raise StateTransitionError(
                f"Invalid transition {action.value} from state {current_state.value}"
            )

        # Validate if required
        if transition.requires_validation and not skip_validation:
            self._validate_transition(agent_version, transition)

        # Perform transition
        agent_version.state = transition.to_state
        agent_version.updated_at = datetime.now(UTC).isoformat()

        # Set timestamps based on new state
        now = datetime.now(UTC).isoformat()
        if transition.to_state == AgentState.PRODUCTION:
            agent_version.promoted_at = now
        elif transition.to_state == AgentState.DEPRECATED:
            agent_version.deprecated_at = now
        elif transition.to_state == AgentState.ARCHIVED:
            agent_version.archived_at = now

        self._save_versions()
        return agent_version

    def _validate_transition(
        self, agent_version: AgentVersion, transition: StateTransition
    ) -> None:
        """Validate a state transition.

        Parameters
        ----------
        agent_version : AgentVersion
            Agent version to validate
        transition : StateTransition
            Transition to validate

        Raises
        ------
        ValidationError
            If validation fails
        """
        if transition.to_state == AgentState.TESTING:
            # Require test results
            if not agent_version.test_results:
                raise ValidationError("Test results required for promotion to testing")

        elif transition.to_state == AgentState.PRODUCTION:
            # Require comprehensive validation
            required_checks = [
                ("test_results", "Test results required"),
                ("performance_metrics", "Performance metrics required"),
                ("security_scan_results", "Security scan results required"),
            ]

            for field, message in required_checks:
                if not getattr(agent_version, field):
                    raise ValidationError(f"{message} for production deployment")

            # Check if there are any higher versions in production
            prod_versions = [
                v
                for v in self._versions.get(agent_version.agent_name, {}).values()
                if v.state == AgentState.PRODUCTION
            ]

            for prod_version in prod_versions:
                if (
                    self._version_compare(prod_version.version, agent_version.version)
                    > 0
                ):
                    raise ValidationError(
                        f"Higher version {prod_version.version} already in production"
                    )

    def _version_compare(self, v1: str, v2: str) -> int:
        """Simple version comparison (basic string comparison).

        Parameters
        ----------
        v1 : str
            First version
        v2 : str
            Second version

        Returns
        -------
        int
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        # Simple comparison - in production, use proper semver
        return (v1 > v2) - (v1 < v2)

    def get_transition_history(
        self, agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transition history for agents.

        Parameters
        ----------
        agent_name : Optional[str]
            Filter by agent name

        Returns
        -------
        List[Dict[str, Any]]
            Transition history
        """
        # This would require audit logging - simplified for now
        versions = self.list_versions(agent_name)
        history = []

        for version in versions:
            history.append(
                {
                    "agent_name": version.agent_name,
                    "version": version.version,
                    "current_state": version.state.value,
                    "created_at": version.created_at,
                    "updated_at": version.updated_at,
                    "promoted_at": version.promoted_at,
                    "author": version.author,
                }
            )

        return sorted(history, key=lambda x: x["updated_at"], reverse=True)

    def _load_versions(self) -> None:
        """Load versions from storage."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for agent_name, versions_data in data.items():
                    self._versions[agent_name] = {}
                    for version_str, version_data in versions_data.items():
                        self._versions[agent_name][version_str] = (
                            AgentVersion.from_dict(version_data)
                        )

        except Exception as e:
            print(f"Failed to load agent versions: {e}")
            self._versions = {}

    def _save_versions(self) -> None:
        """Save versions to storage."""
        try:
            data = {}
            for agent_name, versions in self._versions.items():
                data[agent_name] = {}
                for version_str, version in versions.items():
                    data[agent_name][version_str] = version.to_dict()

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Failed to save agent versions: {e}")


# Singleton instance
_version_manager: Optional[AgentVersionManager] = None


def get_version_manager(
    storage_path: str = "./agent_versions.json",
) -> AgentVersionManager:
    """Get or create version manager singleton instance.

    Parameters
    ----------
    storage_path : str
        Path to version storage file

    Returns
    -------
    AgentVersionManager
        Version manager instance
    """
    global _version_manager
    if _version_manager is None:
        _version_manager = AgentVersionManager(storage_path)
    return _version_manager


if __name__ == "__main__":
    # Example usage
    vm = get_version_manager()

    # Create a new agent version
    version = vm.create_version(
        agent_name="calculator",
        version="1.0.0",
        author="developer@example.com",
        description="Basic calculator agent",
        dependencies=["math"],
    )
    print(
        f"Created version: {version.agent_name} v{version.version} in {version.state.value}"
    )

    # Update metadata
    vm.update_version_metadata(
        "calculator",
        "1.0.0",
        test_results={"passed": 10, "failed": 0},
        performance_metrics={"latency_ms": 150},
    )

    # Promote to testing
    try:
        updated_version = vm.transition_version(
            "calculator", "1.0.0", TransitionAction.PROMOTE
        )
        print(f"Promoted to: {updated_version.state.value}")
    except ValidationError as e:
        print(f"Validation failed: {e}")

    # List all versions
    versions = vm.list_versions("calculator")
    print(f"Total versions for calculator: {len(versions)}")
