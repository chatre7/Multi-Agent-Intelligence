"""
Domain Entities.

Core business entities for the multi-agent system.
"""

from .agent import Agent
from .conversation import Conversation
from .domain_config import DomainConfig, RoutingRule
from .message import Message
from .registered_agent import RegisteredAgent
from .tool import Tool
from .tool_run import ToolRun

__all__ = [
    # Configuration-defined agents
    "Agent",
    # Runtime-discovered agents
    "RegisteredAgent",
    # Domain management
    "DomainConfig",
    "RoutingRule",
    # Conversations and messages
    "Conversation",
    "Message",
    # Tools and executions
    "Tool",
    "ToolRun",
]
