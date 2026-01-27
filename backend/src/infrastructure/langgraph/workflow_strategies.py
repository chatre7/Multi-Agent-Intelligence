"""
Workflow strategy implementations for different domain types.

Each domain can choose its own workflow strategy:
- Orchestrator: Deterministic, pre-defined pipeline
- Few-shot: LLM-based decisions with examples
- Hybrid: Combination of both
"""

from __future__ import annotations

import json
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

# Import skill system
from src.infrastructure.config.skill_loader import SkillLoader
from src.application.use_cases.skills import get_effective_system_prompt
from pathlib import Path


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

            # Execute agent with retry and validation
            # Pass full validation context logic here if needed
            print(f"[INFO] Orchestrator: Executing agent '{agent_id}'")
            result = self._execute_agent_with_retry(agent, current_context)

            # Record this step
            steps.append(
                WorkflowStep(
                    agent_id=agent_id,
                    task=current_context,
                    metadata={"result": result},
                )
            )

            # Build context for next agent
            current_context = f"{current_context}\n\nPrevious output from {agent_id}:\n{result}"

        # Return final result
        return WorkflowResult(
            steps=steps,
            final_response=steps[-1].metadata["result"] if steps else "",
            metadata={"strategy": "orchestrator"},
        )

    def _execute_agent_with_retry(
        self, agent: Agent, task: str, max_retries: int = 3
    ) -> str:
        """
        Execute agent with validation and retry logic.
        
        Args:
            agent: Agent to execute.
            task: Task context.
            max_retries: Maximum number of retries.
            
        Returns:
            Valid response string.
        """
        attempts = 0
        last_error = None
        
        # Temporary feedback history
        feedback_history = ""
        
        while attempts < max_retries:
            current_task = task
            if feedback_history:
                current_task += f"\n\n[SYSTEM FEEDBACK]: Previous attempt invalid. Fix based on: {feedback_history}"
            
            response = self._execute_agent(agent, current_task)
            
            # Simple validation (can be extended to Pydantic/JSON schema later)
            is_valid, error_msg = self._validate_output(response)
            
            if is_valid:
                return response
                
            print(f"[WARN] Agent {agent.id} output validation failed: {error_msg}. Retrying ({attempts+1}/{max_retries})...")
            feedback_history = error_msg
            attempts += 1
        
        # Fallback if allowed, or raise
        print(f"[ERROR] Agent {agent.id} failed all validation attempts.")
        return f"[FATAL] Could not produce valid output after {max_retries} attempts. Last error: {feedback_history}"

    def _validate_output(self, response: str) -> tuple[bool, str]:
        """
        Validate agent output.
        
        Currently checks for:
        1. Empty content
        2. Error prefixes
        
        Future: Integrate Pydantic schema validation here.
        """
        if not response or not response.strip():
            return False, "Output is empty"
            
        # Check for common refusal/error patterns
        if response.strip().startswith("[ERROR]"):
            return False, "Output indicates internal error"
            
        # TODO: Add specific Schema Validation logic here
        # e.g., if agent.id == 'coder': validate_code_block(response)
        
        return True, ""

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

            # Load skills and get effective system prompt
            skill_loader = SkillLoader(Path("backend/configs/skills"))
            loaded_skills = []
            for skill_id in agent.skills:
                skill = skill_loader.load_skill(skill_id)
                if skill:
                    loaded_skills.append(skill)
            
            effective_prompt = get_effective_system_prompt(agent, loaded_skills)

            # Collect full response from stream
            full_response = ""
            for chunk in llm.stream_chat(
                model=model,
                system_prompt=effective_prompt,
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
        # Execute agent with accumulated context
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
                break

            # 1. EXECUTE CURRENT AGENT
            # Note: We don't force handoff examples into the *worker* agent anymore.
            # Let the worker just do the work.
            result_response = self._execute_agent(agent, current_context)

            steps.append(
                WorkflowStep(
                    agent_id=current_agent_id,
                    task=current_context,
                    metadata={
                        "result": result_response,
                        "iteration": iteration,
                    },
                )
            )

            # 2. ROUTER DECISION (Dediciated Step)
            # Ask a "Router" (can be LLM) what to do next based on the result
            decision = self._decide_next_step(
                domain, agents, current_context, result_response, steps
            )

            # Record router thought
            steps.append(
                WorkflowStep(
                    agent_id="router",
                    task="Route Decision",
                    metadata={
                        "result": "", # No visible content
                        "decision": decision,
                        "thought": decision.get("reason", "Deciding next step")
                    },
                )
            )

            if decision.get("action") == "handoff":
                target = decision.get("target_agent")
                if target and target in agents:
                    current_agent_id = target
                    current_context = f"{current_context}\n\n[Previous Agent {agent.id}]: {result_response}"
                    print(f"[INFO] Handoff to {target} (Reason: {decision.get('reason')})")
                    continue
            
            # If action is 'finish' or invalid, stop
            break

        # Get final response from last agent step (not router step)
        final_response = ""
        for step in reversed(steps):
            if step.agent_id != "router":
                final_response = step.metadata.get("result", "")
                break

        return WorkflowResult(
            steps=steps,
            final_response=final_response,
            metadata={
                "strategy": "few_shot",
                "total_handoffs": len(steps) - 1,
            },
        )

    def _decide_next_step(
        self,
        domain: DomainConfig,
        agents: dict[str, Agent],
        original_request: str,
        last_response: str,
        history: List[WorkflowStep]
    ) -> dict[str, Any]:
        """
        Act as a Router Decision Maker.
        """
        # Prepare dynamic examples
        examples = self._get_routing_examples(domain)
        agent_list = ", ".join(agents.keys())
        
        system_prompt = f"""You are a Workflow Router.
Your goal is to decide if the task is complete or if it needs to be passed to another specialist agent.

Available Agents: {agent_list}

ROUTING RULES:
1. If the last response fully answers the user's request, output action: "finish".
2. If another agent can add value or is specifically requested, output action: "handoff".
3. Do not handoff to the same agent immediately.

{examples}

RESPONSE FORMAT (JSON ONLY):
{{
    "action": "finish" | "handoff",
    "target_agent": "agent_id_if_handoff",
    "reason": "short explanation"
}}
"""
        
        user_context = f"""
Original Request: {original_request}
Last Agent Response: {last_response[:500]}...
Current Handoff Count: {len(history)}
"""
        
        try:
            llm = llm_from_env()
            if not llm:
                return {"action": "finish", "reason": "LLM not available"}

            # Use a capable model for routing if possible, or fallback to main model
            router_model = os.getenv("ROUTER_MODEL", os.getenv("LLM_MODEL", "llama3")) 
            
            # Stricter prompt for smaller models
            system_prompt += "\nIMPORTANT: Return ONLY raw JSON. No conversational text before or after."

            response_text = ""
            for chunk in llm.stream_chat(
                model=router_model,
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_context}],
                temperature=0.1, # Low temp for deterministic routing
                max_tokens=300
            ):
                response_text += chunk

            # Parse JSON with robust extraction
            # Find first { and last }
            match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if not match:
                 return {"action": "finish", "reason": f"No JSON block in: {response_text[:50]}..."}
            
            clean_json = match.group(1).strip()
            return json.loads(clean_json)
            
        except Exception as e:
            print(f"[WARN] Router decision failed: {e}. Output was: {response_text}")
            return {"action": "finish", "reason": f"Routing error: {str(e)}"}

    def _get_routing_examples(self, domain: DomainConfig) -> str:
        """Get routing examples from domain metadata or defaults."""
        few_shot_config = domain.metadata.get("few_shot", {})
        custom_examples = few_shot_config.get("routing_examples", [])
        
        if custom_examples:
            formatted = "\nEXAMPLES:\n"
            for ex in custom_examples:
                formatted += f"Situation: {ex['situation']}\nDecision: {json.dumps(ex['decision'])}\n\n"
            return formatted
            
        # Default Examples
        return """
EXAMPLES:

Situation: User asked for a joke, Empath replied "Here is a joke...".
Decision: {"action": "finish", "reason": "Request fulfilled"}

Situation: User asked for code review, Planner outlined the plan.
Decision: {"action": "handoff", "target_agent": "coder", "reason": "Move to implementation phase"}
"""

    def _execute_agent(self, agent: Agent, task: str) -> str:
        """Re-use base execution logic (same as Orchestrator base implementation)."""
        # This duplicates _execute_agent from Orchestrator slightly to avoid mixin complexity for now,
        # or we could make a Mixin. For safety, a simple direct call integration:
        try:
            llm = llm_from_env()
            if llm is None: raise ImportError("No LLM")
            
            # Load skills and get effective system prompt
            skill_loader = SkillLoader(Path("backend/configs/skills"))
            loaded_skills = []
            for skill_id in agent.skills:
                skill = skill_loader.load_skill(skill_id)
                if skill:
                    loaded_skills.append(skill)
            
            effective_prompt = get_effective_system_prompt(agent, loaded_skills)
            
            full_resp = ""
            for chunk in llm.stream_chat(
                model=agent.model_name or "default",
                system_prompt=effective_prompt,
                messages=[{"role": "user", "content": task}],
                temperature=0.7,
                max_tokens=2000
            ):
                full_resp += chunk
            return full_resp
        except Exception as e:
            return f"Error: {e}"


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

                # Update context with planning results (Summarized)
                if planning_result.final_response:
                    raw_context = planning_result.final_response
                    current_context = self._summarize_context(raw_context, "Planning")
                    print(f"[INFO] Hybrid: Planning Phase summarized. Length: {len(raw_context)} -> {len(current_context)}")

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

                # Update context (Summarized)
                if execution_result.final_response:
                    raw_context = execution_result.final_response
                    current_context = self._summarize_context(raw_context, "Execution")
                    print(f"[INFO] Hybrid: Execution Phase summarized. Length: {len(raw_context)} -> {len(current_context)}")

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

    def _summarize_context(self, current_context: str, phase_name: str) -> str:
        """
        Compress context using LLM before handing off to next phase.
        
        Args:
            current_context: Full text context to summarize.
            phase_name: Name of the completed phase (e.g., "Planning").
            
        Returns:
            Summarized context string.
        """
        # If context is short, no need to summarize
        if len(current_context) < 1000:
            return current_context
            
        try:
            llm = llm_from_env()
            if not llm:
                return current_context

            summary_prompt = f"""
You are a Technical Summarizer.
Summarize the key information from the '{phase_name}' phase.
Capture all decisions, plan steps, and constraints.
Discard conversational fluff.

CONTENT TO SUMMARIZE:
{current_context[:10000]} # Limit input length just in case

SUMMARY:
"""
            model = os.getenv("LLM_MODEL", "llama3")
            summary = ""
            for chunk in llm.stream_chat(
                model=model,
                system_prompt=summary_prompt,
                messages=[],
                temperature=0.0,
                max_tokens=500
            ):
                summary += chunk
                
            return f"--- {phase_name} Phase Summary ---\n{summary.strip()}\n--------------------------------"
            
        except Exception as e:
            print(f"[WARN] Context summarization failed: {e}")
            return current_context


def get_workflow_strategy(domain: DomainConfig) -> WorkflowStrategy:
    """Factory function to get appropriate strategy for domain."""
    workflow_type = domain.workflow_type
    
    # Fallback to metadata
    if workflow_type == "supervisor" and "workflow_type" in domain.metadata:
        workflow_type = domain.metadata["workflow_type"]

    strategies = {
        "orchestrator": OrchestratorStrategy,
        "few_shot": FewShotStrategy,
        "hybrid": HybridStrategy,
    }

    strategy_class = strategies.get(workflow_type, FewShotStrategy)
    return strategy_class()
