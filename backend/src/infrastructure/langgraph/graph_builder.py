"""
Dynamic LangGraph builder (MVP).

This module creates a simple supervisor-style LangGraph based on loaded configs.
The agent execution is currently a deterministic placeholder; it is designed to be
replaced by an LLM-backed executor later without changing the graph shape.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig
from src.infrastructure.config.exceptions import ConfigError


class ChatMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str


class ConversationState(TypedDict, total=False):
    domain_id: str
    messages: list[ChatMessage]
    selected_agent: str


def _extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [token for token in tokens if len(token) >= 3]


@dataclass(frozen=True)
class ConversationGraphBuilder:
    """Builds a supervisor-style conversation graph from configs."""

    def build(self, domain: DomainConfig, agents_by_id: dict[str, Agent]):
        missing_agents = [
            agent_id for agent_id in domain.agents if agent_id not in agents_by_id
        ]
        if missing_agents:
            raise ConfigError(
                f"Domain '{domain.id}' references missing agents: {missing_agents}"
            )

        graph: StateGraph[ConversationState] = StateGraph(ConversationState)

        def supervisor(state: ConversationState) -> ConversationState:
            messages = state.get("messages", [])
            last_user_message = next(
                (msg["content"] for msg in reversed(messages) if msg["role"] == "user"),
                "",
            )
            request_keywords = _extract_keywords(last_user_message)

            selected_agent = domain.default_agent
            sorted_rules = sorted(domain.routing_rules, key=lambda rule: rule.priority)
            for rule in sorted_rules:
                if rule.matches(request_keywords):
                    selected_agent = rule.agent
                    break

            return {**state, "selected_agent": selected_agent}

        graph.add_node("supervisor", supervisor)

        def make_agent_node(agent: Agent):
            def run_agent(state: ConversationState) -> ConversationState:
                messages = list(state.get("messages", []))
                last_user_message = next(
                    (
                        msg["content"]
                        for msg in reversed(messages)
                        if msg["role"] == "user"
                    ),
                    "",
                )
                response_text = f"[{agent.name}] {last_user_message}".strip()
                messages.append({"role": "assistant", "content": response_text})
                return {**state, "messages": messages}

            return run_agent

        for agent_id in domain.agents:
            agent = agents_by_id[agent_id]
            graph.add_node(f"agent__{agent_id}", make_agent_node(agent))

        def route(state: ConversationState) -> str:
            selected_agent = state.get("selected_agent")
            if not selected_agent:
                return f"agent__{domain.default_agent}"
            if selected_agent not in agents_by_id:
                return f"agent__{domain.default_agent}"
            return f"agent__{selected_agent}"

        route_map = {
            f"agent__{agent_id}": f"agent__{agent_id}" for agent_id in domain.agents
        }
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges("supervisor", route, route_map)
        for agent_id in domain.agents:
            graph.add_edge(f"agent__{agent_id}", END)

        return graph.compile()
