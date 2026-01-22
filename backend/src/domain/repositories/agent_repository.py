"""
Agent Repository Interface (Port).

Defines the contract for persisting and retrieving Agent entities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.agent import Agent
from ..value_objects.agent_state import AgentState


class IAgentRepository(ABC):
    """Port for Agent persistence operations."""

    @abstractmethod
    async def save(self, agent: Agent) -> Agent:
        """
        Persist an agent (create or update).

        Parameters
        ----------
        agent : Agent
            The agent to persist.

        Returns
        -------
        Agent
            The persisted agent (possibly with updated timestamps).

        Raises
        ------
        ValueError
            If agent data is invalid.
        """
        pass

    @abstractmethod
    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Find agent by ID.

        Parameters
        ----------
        agent_id : str
            The agent ID to search for.

        Returns
        -------
        Optional[Agent]
            The agent if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Agent]:
        """
        Find agent by name.

        Parameters
        ----------
        name : str
            The agent name to search for.

        Returns
        -------
        Optional[Agent]
            The agent if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_domain(self, domain_id: str) -> List[Agent]:
        """
        Find all agents in a domain.

        Parameters
        ----------
        domain_id : str
            The domain ID to filter by.

        Returns
        -------
        List[Agent]
            List of agents in the domain.
        """
        pass

    @abstractmethod
    async def find_by_state(self, state: AgentState) -> List[Agent]:
        """
        Find agents by lifecycle state.

        Parameters
        ----------
        state : AgentState
            The state to filter by.

        Returns
        -------
        List[Agent]
            List of agents in the specified state.
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[Agent]:
        """
        Get all agents.

        Returns
        -------
        List[Agent]
            All agents in the system.
        """
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """
        Delete an agent by ID.

        Parameters
        ----------
        agent_id : str
            The agent ID to delete.

        Returns
        -------
        bool
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def find_by_keywords(self, keywords: List[str]) -> List[Agent]:
        """
        Find agents matching keywords.

        Parameters
        ----------
        keywords : List[str]
            Keywords to match against agent routing keywords.

        Returns
        -------
        List[Agent]
            Matching agents sorted by match confidence.
        """
        pass

    @abstractmethod
    async def find_active(self) -> List[Agent]:
        """
        Get all active agents (not deprecated/archived).

        Returns
        -------
        List[Agent]
            All active agents.
        """
        pass
