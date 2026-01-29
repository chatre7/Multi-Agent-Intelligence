from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    """Represents a request to execute a tool."""
    tool: str = Field(..., description="The name of the tool to execute.")
    params: Dict[str, Any] = Field(..., description="The parameters to pass to the tool.")
    thought: Optional[str] = Field(None, description="Reasoning behind using this tool.")

class AgentResponse(BaseModel):
    """The structured output expected from an AI Agent."""
    thought: str = Field(..., description="The agent's internal reasoning process (Chain of Thought).")
    response: str = Field(..., description="The final text response to the user. Leave empty if calling a tool.")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="A list of tools to execute, if any.")

class RoutingDecision(BaseModel):
    """The structured output expected from a Workflow Router."""
    action: Literal["finish", "handoff"] = Field(..., description="Whether to finish the task or handoff to another agent.")
    target_agent: Optional[str] = Field(None, description="The ID of the target agent if action is handoff.")
    reason: str = Field(..., description="Short explanation for the routing decision.")

class SocialPost(BaseModel):
    """The structured output expected from a Social Simulation Agent."""
    thought: str = Field(..., description="Internal reasoning about the topic and audience.")
    content: str = Field(..., description="The actual post content (e.g. tweet or reply).")
    likes: int = Field(default=0, description="Simulated number of likes (0-100).")
