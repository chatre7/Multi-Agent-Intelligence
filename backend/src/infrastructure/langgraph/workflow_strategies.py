"""
Workflow strategy implementations for different domain types.

Each domain can choose its own workflow strategy:
- Orchestrator: Deterministic, pre-defined pipeline
- Few-shot: LLM-based decisions with examples
- Hybrid: Combination of both
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Optional

from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig

# Import only what's needed for type hinting or runtime
# Use TYPE_CHECKING to avoid potential circular imports if necessary, 
# but here llm_from_env is a factory function so it's safe to import.
try:
    from src.infrastructure.llm.streaming import llm_from_env
except ImportError:
    # Graceful fallback for testing without full dependencies
    def llm_from_env(): return None


@dataclass
class WorkflowStep:
    """Single step in a workflow execution."""

    agent_id: str
    task: str
    metadata: dict[str, Any]


@dataclass
class WorkflowResult:
    """Result from workflow execution."""

    steps: List[WorkflowStep]
    final_response: str
    metadata: dict[str, Any]


@dataclass
class _AgentResult:
    """Internal result container for agent execution."""

    response: str
    handoff_to: Optional[str]


class WorkflowStrategy(ABC):
    """Base class for workflow strategies."""

    @abstractmethod
    def execute(
        self,
        domain: DomainConfig,
        agents: dict[str, Agent],
        user_request: str,
    ) -> WorkflowResult:
        """Execute the workflow for a given request."""


class OrchestratorStrategy(WorkflowStrategy):
    """Deterministic workflow with pre-defined pipeline.

    Executes agents in a fixed, pre-determined order based on domain configuration.
    Each agent receives the accumulated context from all previous agents.

    Example:
        software_development domain:
        User request -> Planner -> Coder -> Tester -> Reviewer -> Done

    Configuration:
        Domain metadata should include:
        {
            "workflow_type": "orchestrator",
            "orchestration": {
                "pipeline": ["agent1", "agent2", "agent3"]
            }
        }
    """

    def execute(
        self,
        domain: DomainConfig,
        agents: dict[str, Agent],
        user_request: str,
    ) -> WorkflowResult:
        """
        Execute deterministic pipeline from domain config.

        Args:
            domain: Domain configuration containing orchestration settings
            agents: Dictionary mapping agent IDs to Agent instances
            user_request: Initial user request to process

        Returns:
            WorkflowResult containing all steps and final response

        Raises:
            ValueError: If pipeline contains unknown agent IDs
            TypeError: If pipeline configuration is malformed
        """
        # Get and validate pipeline configuration
        orchestration_config = domain.metadata.get("orchestration", {})
        pipeline = orchestration_config.get("pipeline", [])

        # Validate pipeline is a list
        if not isinstance(pipeline, list):
            # Handle malformed config gracefully
            if isinstance(pipeline, str):
                raise TypeError(
                    f"Pipeline must be a list, got string: '{pipeline}'. "
                    f"Did you mean: pipeline: [{pipeline}]?"
                )
            raise TypeError(f"Pipeline must be a list, got {type(pipeline).__name__}")

        steps: List[WorkflowStep] = []
        current_context = user_request

        # Execute each agent in sequence
        for agent_id in pipeline:
            # Validate agent exists
            agent = agents.get(agent_id)
            if not agent:
                raise ValueError(
                    f"Unknown agent_id: {agent_id}. "
                    f"Available agents: {', '.join(agents.keys())}"
                )

            # Execute agent with accumulated context
            result = self._execute_agent(agent, current_context)

            # Record this step
            steps.append(
                WorkflowStep(
                    agent_id=agent_id,
                    task=current_context,
                    metadata={"result": result},
                )
            )

            # Build context for next agent
            current_context = f"{current_context}\n\nPrevious output:\n{result}"

        # Return final result
        return WorkflowResult(
            steps=steps,
            final_response=steps[-1].metadata["result"] if steps else "",
            metadata={"strategy": "orchestrator"},
        )

    def _execute_agent(self, agent: Agent, task: str) -> str:
        """
        Execute a single agent with the given task using real LLM.

        Args:
            agent: Agent to execute
            task: Task/context for the agent

        Returns:
            Agent's response as a string
        """
        try:
            llm = llm_from_env()
            if llm is None:
                raise ImportError("LLM service not available")

            messages = [{"role": "user", "content": task}]

            # Use agent's model or default
            model = agent.model_name
            if not model or model == "default":
                # Default fallback: check env or use 'llama3' for Ollama
                model = os.getenv("LLM_MODEL", "llama3")

            # Collect full response from stream
            full_response = ""
            for chunk in llm.stream_chat(
                model=model,
                system_prompt=agent.system_prompt,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            ):
                full_response += chunk

            return full_response

        except ImportError:
            # Fallback if dependencies issues
            return f"[{agent.id}] (LLM Error): Could not import LLM service. Processed: {task[:50]}..."
        except Exception as e:
            # Fallback on runtime error
            print(f"[ERROR] LLM Execution failed for agent {agent.id}: {e}")
            return f"[{agent.id}] (Execution Error): {str(e)}. Processed: {task[:50]}..."


class FewShotStrategy(WorkflowStrategy):
    """LLM-based workflow with few-shot examples.

    Uses LLM to decide agent handoffs based on conversation context and few-shot examples.
    Provides flexibility for creative and context-dependent agent routing.

    Example:
        social_chat domain:
        User request -> Empath (decides) -> Maybe Comedian -> Maybe Storyteller -> Done

    Configuration:
        Domain metadata should include:
        {
            "workflow_type": "few_shot",
            "few_shot": {
                "max_handoffs": 5,
                "examples_enabled": true
            }
        }
    """

    def execute(
        self,
        domain: DomainConfig,
        agents: dict[str, Agent],
        user_request: str,
    ) -> WorkflowResult:
        """
        Execute workflow with LLM deciding handoffs using few-shot examples.

        Args:
            domain: Domain configuration with default_agent and few_shot settings
            agents: Dictionary mapping agent IDs to Agent instances
            user_request: Initial user request to process

        Returns:
            WorkflowResult containing all steps and final response

        Raises:
            ValueError: If default_agent is not found
            KeyError: If required configuration is missing
        """
        steps: List[WorkflowStep] = []
        current_agent_id = domain.default_agent
        current_context = user_request

        # Get max_handoffs from config or use default
        few_shot_config = domain.metadata.get("few_shot", {})
        max_handoffs = few_shot_config.get("max_handoffs", 5)

        # Validate default agent exists
        if current_agent_id not in agents:
            raise ValueError(
                f"Default agent '{current_agent_id}' not found. "
                f"Available agents: {', '.join(agents.keys())}"
            )

        for iteration in range(max_handoffs):
            agent = agents.get(current_agent_id)
            if not agent:
                # Agent not found, stop gracefully
                break

            # Add few-shot examples to system prompt
            enhanced_prompt = self._add_few_shot_examples(
                agent.system_prompt, domain, agents
            )

            # Execute agent with enhanced prompt
            result = self._execute_agent_with_examples(
                agent, current_context, enhanced_prompt
            )

            # Record this step
            steps.append(
                WorkflowStep(
                    agent_id=current_agent_id,
                    task=current_context,
                    metadata={
                        "result": result.response,
                        "handoff_to": result.handoff_to,
                        "iteration": iteration,
                    },
                )
            )

            # Check if agent decided to handoff
            if result.handoff_to:
                # Validate target agent exists
                if result.handoff_to not in agents:
                    # Unknown agent, stop here
                    break

                current_agent_id = result.handoff_to
                current_context = f"{current_context}\n\n{result.response}"
            else:
                # Agent finished, no more handoffs
                break

        return WorkflowResult(
            steps=steps,
            final_response=steps[-1].metadata["result"] if steps else "",
            metadata={
                "strategy": "few_shot",
                "total_handoffs": len(steps) - 1,
            },
        )

    def _add_few_shot_examples(
        self, base_prompt: str, domain: DomainConfig, agents: dict[str, Agent]
    ) -> str:
        """
        Add few-shot handoff examples to the system prompt.

        Args:
            base_prompt: Original agent system prompt
            domain: Domain configuration
            agents: Available agents

        Returns:
            Enhanced prompt with handoff examples
        """
        agent_list = ", ".join(agents.keys())
        examples = f"""

# HANDOFF EXAMPLES

Available agents: {agent_list}

Example 1:
User: "I feel sad today"
Empath: "I'm sorry to hear that. Would you like me to get the Comedian to cheer you up?"
{{"tool": "transfer_to_agent", "params": {{"target_agent": "comedian", "reason": "User needs cheering up"}}}}

Example 2:
User: "Tell me about the meaning of life"
Empath: "That's a deep philosophical question. Let me hand you to our Philosopher."
{{"tool": "transfer_to_agent", "params": {{"target_agent": "philosopher", "reason": "Philosophical discussion"}}}}

Example 3 (Thai):
User: "เครียดจัง เล่าเรื่องตลกให้ฟังหน่อย"
Empath: "โธ่ อย่าเพิ่งเครียดนะครับ เดี๋ยวผมให้ Comedian มาช่วยทำให้ยิ้มดีกว่า"
{{"tool": "transfer_to_agent", "params": {{"target_agent": "comedian", "reason": "User requested a joke (Thai translation)"}}}}

Example 4 (Thai):
User: "อยากฟังนิทานก่อนนอน"
Empath: "ได้เลยครับ นักเล่าเรื่องของเราเก่งมาก เดี๋ยวผมส่งต่อให้นะครับ"
{{"tool": "transfer_to_agent", "params": {{"target_agent": "storyteller", "reason": "User requested a story (Thai translation)"}}}}

Now handle the user's request using these patterns.
"""
        return base_prompt + examples

    def _execute_agent_with_examples(
        self, agent: Agent, task: str, prompt: str
    ) -> _AgentResult:
        """
        Execute agent with few-shot enhanced prompt using real LLM.

        Args:
            agent: Agent to execute
            task: Task/context for the agent
            prompt: Enhanced system prompt with examples

        Returns:
            _AgentResult with response and optional handoff_to
        """
        try:
            llm = llm_from_env()
            if llm is None:
                raise ImportError("LLM service not available")

            messages = [{"role": "user", "content": task}]

            # Use agent's model or default fallback
            model = agent.model_name
            if not model or model == "default":
                model = os.getenv("LLM_MODEL", "llama3")

            full_response = ""
            for chunk in llm.stream_chat(
                model=model,
                system_prompt=prompt,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            ):
                full_response += chunk

            # Basic parsing for handoff (MVP)
            # Look for JSON-like pattern: "target_agent": "agent_name"
            handoff_to = None
            if "transfer_to_agent" in full_response:
                match = re.search(r'target_agent":\s*"([^"]+)"', full_response)
                if match:
                    handoff_to = match.group(1)

            return _AgentResult(response=full_response, handoff_to=handoff_to)

        except Exception as e:
            print(f"[ERROR] LLM Execution failed: {e}")
            return _AgentResult(
                response=f"[{agent.id}] (Error): {str(e)}. Original task: {task[:50]}...",
                handoff_to=None,
            )


class HybridStrategy(WorkflowStrategy):
    """Hybrid workflow combining orchestrator + few-shot.

    Composes deterministic orchestration for some phases and LLM-based
    handoffs for others, providing maximum flexibility for complex workflows.

    Example:
        research domain:
        User request -> Planner (orchestrated) ->
        Researcher (LLM decides which specialist) ->
        Validator (orchestrated) -> Done

    Configuration:
        Domain metadata should include:
        {
            "workflow_type": "hybrid",
            "hybrid": {
                "orchestrator_decides": ["planning", "validation"],
                "llm_decides": ["agent_selection", "handoff_timing"]
            }
        }
    """

    def execute(
        self,
        domain: DomainConfig,
        agents: dict[str, Agent],
        user_request: str,
    ) -> WorkflowResult:
        """
        Execute hybrid workflow combining orchestrator and few-shot strategies.

        Args:
            domain: Domain configuration with hybrid settings
            agents: Dictionary mapping agent IDs to Agent instances
            user_request: Initial user request to process

        Returns:
            WorkflowResult containing steps from both strategies
        """
        hybrid_config = domain.metadata.get("hybrid", {})
        orchestrated_phases = hybrid_config.get("orchestrator_decides", [])
        llm_phases = hybrid_config.get("llm_decides", [])

        steps: List[WorkflowStep] = []
        current_context = user_request

        # Phase 1: Orchestrated planning (if configured)
        if "planning" in orchestrated_phases:
            # Filter agents relevant to planning
            planning_agents = {
                k: v for k, v in agents.items() if "planner" in k.lower()
            }

            if planning_agents:
                # Use orchestrator for planning phase
                orchestrator = OrchestratorStrategy()

                # Create temporary domain config for planning
                planning_domain = DomainConfig(
                    id=f"{domain.id}_planning",
                    name=f"{domain.name} Planning",
                    description="Planning phase",
                    agents=list(planning_agents.keys()),
                    default_agent=list(planning_agents.keys())[0],
                    metadata={
                        "orchestration": {"pipeline": list(planning_agents.keys())}
                    },
                )

                planning_result = orchestrator.execute(
                    planning_domain,
                    planning_agents,
                    current_context,
                )
                steps.extend(planning_result.steps)

                # Update context with planning results
                if planning_result.final_response:
                    current_context = planning_result.final_response

        # Phase 2: LLM-based agent selection (if configured)
        if "agent_selection" in llm_phases:
            # Filter out planner agents for execution phase
            execution_agents = {
                k: v for k, v in agents.items() if "planner" not in k.lower()
            }

            if execution_agents:
                # Use few-shot for flexible agent handoffs
                few_shot = FewShotStrategy()

                # Create temporary domain for few-shot execution
                execution_domain = DomainConfig(
                    id=f"{domain.id}_execution",
                    name=f"{domain.name} Execution",
                    description="Execution phase",
                    agents=list(execution_agents.keys()),
                    default_agent=(
                        list(execution_agents.keys())[0]
                        if execution_agents
                        else domain.default_agent
                    ),
                    metadata={
                        "few_shot": {
                            "max_handoffs": 3  # Limit handoffs in hybrid mode
                        }
                    },
                )

                execution_result = few_shot.execute(
                    execution_domain,
                    execution_agents,
                    current_context,
                )
                steps.extend(execution_result.steps)

                # Update context
                if execution_result.final_response:
                    current_context = execution_result.final_response

        # Phase 3: Orchestrated validation (if configured)
        if "validation" in orchestrated_phases:
            # Filter validation-related agents
            validation_agents = {
                k: v
                for k, v in agents.items()
                if any(
                    keyword in k.lower() for keyword in ["validator", "reviewer", "tester"]
                )
            }

            if validation_agents:
                orchestrator = OrchestratorStrategy()

                validation_domain = DomainConfig(
                    id=f"{domain.id}_validation",
                    name=f"{domain.name} Validation",
                    description="Validation phase",
                    agents=list(validation_agents.keys()),
                    default_agent=list(validation_agents.keys())[0],
                    metadata={
                        "orchestration": {"pipeline": list(validation_agents.keys())}
                    },
                )

                validation_result = orchestrator.execute(
                    validation_domain,
                    validation_agents,
                    current_context,
                )
                steps.extend(validation_result.steps)

                # Update final response
                if validation_result.final_response:
                    current_context = validation_result.final_response

        return WorkflowResult(
            steps=steps,
            final_response=steps[-1].metadata["result"] if steps else "",
            metadata={
                "strategy": "hybrid",
                "orchestrated_phases": orchestrated_phases,
                "llm_phases": llm_phases,
                "total_phases": len(orchestrated_phases) + len(llm_phases),
            },
        )


def get_workflow_strategy(domain: DomainConfig) -> WorkflowStrategy:
    """Factory function to get appropriate strategy for domain."""
    workflow_type = domain.metadata.get("workflow_type", "few_shot")

    strategies = {
        "orchestrator": OrchestratorStrategy,
        "few_shot": FewShotStrategy,
        "hybrid": HybridStrategy,
    }

    strategy_class = strategies.get(workflow_type, FewShotStrategy)
    return strategy_class()
