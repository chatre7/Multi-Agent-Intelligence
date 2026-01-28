"""
Dynamic LangGraph builder (MVP).

This module creates a simple supervisor-style LangGraph based on loaded configs.
The agent execution is currently a deterministic placeholder; it is designed to be
replaced by an LLM-backed executor later without changing the graph shape.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Literal, TypedDict
import os

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig
from src.infrastructure.config.exceptions import ConfigError
from src.infrastructure.llm.streaming import llm_from_env
from src.domain.entities.handoff import HandoffRequest
from src.infrastructure.tools.registry import ToolRegistry
from src.infrastructure.persistence.chroma.memory_repository import ChromaMemoryRepository
from src.infrastructure.langgraph.memory_utils import extract_facts
from src.infrastructure.config.skill_loader import SkillLoader
from src.domain.repositories.skill_repository import ISkillRepository
from src.application.use_cases.skills import get_effective_system_prompt, get_effective_tools
from pathlib import Path


class ChatMessage(TypedDict, total=False):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    agent_id: str  # Track which agent generated this message


class ConversationState(TypedDict, total=False):
    domain_id: str
    messages: list[ChatMessage]
    selected_agent: str
    pending_tool_calls: list[dict[str, Any]]
    thoughts: list[dict[str, Any]] # New field for reasoning logs


def _extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [token for token in tokens if len(token) >= 3]


def _format_tool_prompt(tools: list[Any], available_agents: list[str] = None) -> str:
    if not tools and not available_agents:
        return ""
    
    tool_descs = []
    if tools:
        for t in tools:
            params = ", ".join(f"{k}: {v}" for k, v in t.parameters_schema.get("properties", {}).items())
            tool_descs.append(f"- {t.id}({params}): {t.description}")
        
    # Add virtual handoff tool
    if available_agents:
        agent_options = ", ".join(available_agents)
        tool_descs.append(f"- transfer_to_agent(target_agent: str, reason: str): Transfer control to another agent. Target must be one of: [{agent_options}]")

    return """
# TOOL CALLING RULES
You can provide a text response followed by a tool call if needed.
To invoke a tool, include a JSON block in your message:

Available Tools:
{}

Example:
```json
{{
  "tool": "save_file",
  "params": {{
    "file_path": "test.txt",
    "content": "hello world"
  }}
}}
```

Wait for the tool output before concluding.
""".format("\n".join(tool_descs))


@dataclass(frozen=True)
class ConversationGraphBuilder:
    """Builds a supervisor-style conversation graph from configs."""

    skill_repo: ISkillRepository | None = None
    skill_loader: SkillLoader | None = None

    def build(self, domain: DomainConfig, agents_by_id: dict[str, Agent]):
        missing_agents = [
            agent_id for agent_id in domain.agents if agent_id not in agents_by_id
        ]
        if missing_agents:
            raise ConfigError(
                f"Domain '{domain.id}' references missing agents: {missing_agents}"
            )

        # ========== WORKFLOW STRATEGY DETECTION ==========
        # Check if domain uses new workflow strategies (orchestrator, few_shot, hybrid)
        # Prioritize domain attribute, fallback to metadata for backward compat
        workflow_type = domain.workflow_type
        if workflow_type == "supervisor" and "workflow_type" in domain.metadata:
             workflow_type = domain.metadata["workflow_type"]
        
        if workflow_type in ["orchestrator", "few_shot", "hybrid", "social_simulation"]:
            # Use new workflow strategy system
            from src.infrastructure.langgraph.workflow_strategies import get_workflow_strategy
            
            print(f"[INFO] Using {workflow_type} workflow strategy for domain '{domain.id}'")
            strategy = get_workflow_strategy(domain)
            
            # Note: Strategies execute independently and return WorkflowResult
            # For now, we build a simple graph that executes the strategy
            # In a full implementation, this would convert WorkflowResult to ConversationState
            
            graph: StateGraph[ConversationState] = StateGraph(ConversationState)
            
            def strategy_executor(state: ConversationState, config: Any = None) -> ConversationState:
                """Execute workflow strategy and update conversation state."""
                messages = state.get("messages", [])
                
                # Get token callback from config if present
                token_callback = None
                enable_thinking = False
                if config and "configurable" in config:
                    token_callback = config["configurable"].get("token_callback")
                    enable_thinking = config["configurable"].get("enable_thinking", False)
                
                # Also check for system messages with thinking instructions
                for msg in messages:
                    if msg.get("role") == "system" and "<think>" in msg.get("content", ""):
                        enable_thinking = True
                        break
                
                # Get last user message as the request
                last_user_message = next(
                    (msg["content"] for msg in reversed(messages) if msg["role"] == "user"),
                    "",
                )
                
                # Execute strategy
                try:
                    result = strategy.execute(
                        domain=domain,
                        agents=agents_by_id,
                        user_request=last_user_message,
                        token_callback=token_callback,
                        enable_thinking=enable_thinking
                    )
                    
                    # Convert WorkflowResult to conversation messages and thoughts
                    new_messages = list(messages)
                    new_thoughts = state.get("thoughts", [])

                    for step in result.steps:
                        # Collect thoughts from all agents (worker + router)
                        step_thoughts = step.metadata.get("thoughts", [])
                        for st in step_thoughts:
                            new_thoughts.append({
                                "agent_id": step.agent_id,
                                "agent_name": agents_by_id.get(step.agent_id).name if agents_by_id.get(step.agent_id) else step.agent_id,
                                "thought": st.get("content", ""),
                                "type": st.get("type", "reasoning"),
                                "metadata": st # Keep original structure
                            })

                        if step.agent_id == "router":
                            # It's a dedicated thought/decision step
                            new_thoughts.append({
                                "agent_id": "router",
                                "agent_name": "Router",
                                "thought": step.metadata.get("thought", ""),
                                "decision": step.metadata.get("decision", {}),
                                "type": "routing"
                            })
                        else:
                            # It's a message
                            new_messages.append({
                                "role": "assistant",
                                "content": step.metadata.get("result", ""),
                                "agent_id": step.agent_id,
                            })
                    
                    # Determine last real agent
                    last_real_agent = domain.default_agent
                    if result.steps:
                        # Find last non-router agent
                        real_steps = [s for s in result.steps if s.agent_id != "router"]
                        if real_steps:
                            last_real_agent = real_steps[-1].agent_id

                    return {
                        **state,
                        "messages": new_messages,
                        "thoughts": new_thoughts,
                        "selected_agent": last_real_agent,
                    }
                except Exception as e:
                    print(f"[ERROR] Strategy execution failed: {e}")
                    # Fallback: return state unchanged
                    return state
            
            graph.add_node("strategy_executor", strategy_executor)
            graph.add_edge(START, "strategy_executor")
            graph.add_edge("strategy_executor", END)
            
            # Add Checkpointer for persistence
            checkpointer = MemorySaver()
            return graph.compile(checkpointer=checkpointer)
        
        # ========== LEGACY SUPERVISOR WORKFLOW ==========
        # Continue with existing supervisor-based workflow for backward compatibility
        
        # Initialize Tool Registry
        registry = ToolRegistry()
        # Pre-load tools from config (MVP: Assuming basic tools exist)
        # In a real app, we would load definitions from DB or Config here
        
        # Setup memory
        memory_repo = ChromaMemoryRepository()
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
                
                # Load skills for this agent (Must be done before get_effective_tools)
                all_skills = {}
                if self.skill_loader:
                    for skill_id in agent.skills:
                        skill = self.skill_loader.load_skill(skill_id)
                        if skill:
                            all_skills[skill.id] = skill
                
                if self.skill_repo:
                    db_skills = self.skill_repo.get_agent_skills(agent.id)
                    for s in db_skills:
                        all_skills[s.id] = s

                # Get effective tools (including skill-provided tools)
                effective_tools_ids = get_effective_tools(agent, list(all_skills.values()))
                tools = registry.get_tools_for_agent(effective_tools_ids)
                
                # 1. Search Memory
                user_query = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        user_query = m["content"]
                        break
                
                memories = []
                if user_query:
                    try:
                        print(f"[DEBUG] Searching memory for: '{user_query}'")
                        results = memory_repo.search_memories(user_query, limit=3)
                        memories = [r["content"] for r in results]
                        if memories:
                            print(f"[DEBUG] Found {len(memories)} relevant memories.")
                        else:
                            print("[DEBUG] No relevant memories found.")
                    except Exception as e:
                        print(f"[DEBUG] Memory search failed: {e}")

                # 2. Format system prompt with Agent instructions + Tool instructions + Memory
            
                # Get effective system prompt (includes skill instructions)
                base_system_prompt = get_effective_system_prompt(agent, list(all_skills.values()))
                
                if memories:
                    memory_context = "\n- ".join(memories)
                    base_system_prompt += f"\n\nRELEVANT PAST CONTEXT:\n- {memory_context}"

                tool_prompt = _format_tool_prompt(tools, available_agents=list(agents_by_id.keys()))
                
                # Create LLM adapter
                llm = llm_from_env()
                
                # Format messages - extract system messages to prepend to system prompt
                llm_messages = []
                extra_system_instructions = []
                for m in messages:
                    if m["role"] == "system":
                        # Collect system messages to add to system prompt
                        extra_system_instructions.append(m["content"])
                    elif m["role"] == "tool":
                        # Map tool output to user role with clear prefix for LLM compatibility
                        llm_messages.append({"role": "user", "content": f"[TOOL OBSERVATION] {m['content']}"})
                    else:
                        llm_messages.append({"role": m["role"], "content": m["content"]})
                
                # Get model and prompt
                model = agent.model_name or "llama3.2"
                # Build final system prompt: base + extra instructions + tools
                system_prompt = base_system_prompt
                if extra_system_instructions:
                    system_prompt = "\n\n".join([system_prompt] + extra_system_instructions)
                system_prompt = f"{system_prompt}\n{tool_prompt}"
                
                print(f"[DEBUG] Invoking LLM: {model}")
                print(f"[DEBUG] System Prompt Length: {len(system_prompt)}")
                print(f"[DEBUG] Message Count: {len(llm_messages)}")
                if llm_messages:
                    print(f"[DEBUG] Last Message: {llm_messages[-1]}")

                # Execute LLM
                response_chunks = []
                try:
                    for chunk in llm.stream_chat(
                        model=model,
                        system_prompt=system_prompt,
                        messages=llm_messages,
                        temperature=agent.temperature or 0.7,
                        max_tokens=agent.max_tokens or 2000
                    ):
                        response_chunks.append(chunk)
                except Exception as e:
                    print(f"[DEBUG] LLM Streaming Error: {e}")
                
                response_text = "".join(response_chunks).strip()
                
                # Parse Tool Calls (JSON)
                tool_calls = []
                
                # Debug: Print raw response to logs
                print(f"[DEBUG] Raw Agent Response: {response_text}")
                
                # 1. Try matching markdown json block
                json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
                
                # 2. If no block, try matching raw JSON object with "tool" key (more robust)
                if not json_match:
                    json_match = re.search(r"(\{[\s\S]*?['\"]tool['\"]\s*:[\s\S]*?\})", response_text, re.DOTALL)

                if json_match:
                    json_str = json_match.group(1)
                    print(f"[DEBUG] Found JSON candidate: {json_str}")
                    try:
                        # Try standard JSON first
                        tool_call = json.loads(json_str)
                    except json.JSONDecodeError:
                        try:
                            # Fallback to ast.literal_eval for single quotes or non-strict JSON
                            print("[DEBUG] JSON loads failed, trying ast.literal_eval")
                            tool_call = ast.literal_eval(json_str)
                        except Exception as e:
                            print(f"[DEBUG] Parsing failed: {e}")
                            tool_call = None
                            
                    if tool_call and isinstance(tool_call, dict) and "tool" in tool_call and "params" in tool_call:
                        tool_calls.append(tool_call)
                        print(f"[DEBUG] Valid tool call parsed: {tool_call}")
                
                # 3. HEURISTIC FALLBACK: If model is dumber and just writes code blocks
                if not tool_calls:
                    # Look for code blocks that resemble file creation
                    # Case A: echo "content" > filename
                    echo_match = re.search(r"echo\s+['\"](.*?)['\"]\s*>\s*([a-zA-Z0-9_\-\.]+)", response_text)
                    if echo_match:
                        content, filename = echo_match.groups()
                        tool_calls.append({"tool": "save_file", "params": {"file_path": filename, "content": content}})
                        print(f"[DEBUG] Heuristic match (echo): {filename}")
                    
                    # Case B: Python open() write
                    py_match = re.search(r"with\s+open\(['\"](.*?)['\"]\s*,\s*['\"]w['\"]\)\s*as\s+\w+:\s+\w+\.write\(['\"](.*?)['\"]\)", response_text)
                    if py_match:
                        filename, content = py_match.groups()
                        tool_calls.append({"tool": "save_file", "params": {"file_path": filename, "content": content}})
                        print(f"[DEBUG] Heuristic match (python): {filename}")
                    
                    # Case C: Plain text handoff mention
                    agent_pattern = "|".join(agents_by_id.keys())
                    handoff_text_match = re.search(rf"(?:handoff|transfer|send|invoke|ask)\s+.*?\b({agent_pattern})\b", response_text.lower())
                    if handoff_text_match:
                        target = handoff_text_match.group(1)
                        if target in agents_by_id:
                            tool_calls.append({"tool": "transfer_to_agent", "params": {"target_agent": target, "reason": "Detected via text heuristic"}})
                            print(f"[DEBUG] Heuristic match (handoff text): {target}")

                if not json_match and not tool_calls:
                     print("[DEBUG] No JSON pattern or heuristic found")
                
                messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "agent_id": agent.id  # Metadata: Who spoke?
                })
                
                if not tool_calls:
                     # Check for Handoff (JSON) - Legacy regex, but now we expect tool call style
                    pass
                
                # Check if any tool call is actually a handoff
                actual_tool_calls = []
                
                # Map Tools to Skills for Observability
                tool_to_skill_map = {}
                for skill in all_skills.values():
                    for tool_id in skill.tools:
                        tool_to_skill_map[tool_id] = skill.name

                for tc in tool_calls:
                    # Inject Skill Metadata
                    if tc["tool"] in tool_to_skill_map:
                        tc["metadata"] = {"skill_id": tool_to_skill_map[tc["tool"]]}
                        print(f"[DEBUG] Tool '{tc['tool']}' linked to Skill '{tool_to_skill_map[tc['tool']]}'")

                    if tc["tool"] == "transfer_to_agent":
                        target = tc["params"].get("target_agent")
                        reason = tc["params"].get("reason", "No reason")
                        print(f"[DEBUG] Handoff Tool DETECTED: {target}")
                        
                        system_note = {
                            "role": "system", 
                            "content": f"NOTICE: Agent '{agent.id}' transferred this task to '{target}'. Reason: {reason}. You are now '{target}'. Please proceed."
                        }
                        messages.append(system_note)
                        
                        return {**state, "messages": messages, "selected_agent": target}
                    else:
                        actual_tool_calls.append(tc)
                
                # Update tool calls to exclude handoff
                tool_calls = actual_tool_calls

                # If the response is final (not a tool call), extract facts for long-term memory
                if not tool_calls:
                    # Clear selected_agent to prevent loop (Agent is done)
                    # Unless we found a handoff above (which returns early)
                    state["selected_agent"] = None
                    
                    try:
                        model = os.getenv("LLM_MODEL", "gpt-oss:120b-cloud")
                        print(f"[DEBUG] Extracting facts using model: {model}")
                        new_facts = extract_facts(llm, model, messages)
                        if new_facts:
                            print(f"[DEBUG] Final extracted facts: {new_facts}")
                            memory_repo.add_memories(new_facts)
                        else:
                            print("[DEBUG] No new facts extracted.")
                    except Exception as e:
                        print(f"[DEBUG] Fact extraction failed: {e}")

                return {**state, "messages": messages, "pending_tool_calls": tool_calls}

            return run_agent

        for agent_id in domain.agents:
            agent = agents_by_id[agent_id]
            graph.add_node(f"agent__{agent_id}", make_agent_node(agent))

        def execute_tools(state: ConversationState) -> ConversationState:
            tool_calls = state.get("pending_tool_calls", [])
            messages = list(state.get("messages", []))
            
            for call in tool_calls:
                tool_id = call["tool"]
                params = call["params"]
                metadata = call.get("metadata", {})
                
                try:
                    result = registry.execute(tool_id, params)
                    output = f"Tool '{tool_id}' output: {result}"
                except Exception as e:
                    output = f"Tool '{tool_id}' error: {str(e)}"
                
                # Propagate metadata (skill_id) to the tool output message
                messages.append({"role": "tool", "content": output, "metadata": metadata})
            
            # Clear pending tools
            return {**state, "messages": messages, "pending_tool_calls": []}

        graph.add_node("tool_executor", execute_tools)

        def route(state: ConversationState) -> str:
            selected_agent = state.get("selected_agent")
            if not selected_agent:
                return f"agent__{domain.default_agent}"
            if selected_agent not in agents_by_id:
                return f"agent__{domain.default_agent}"
            return f"agent__{selected_agent}"

        def agent_router(state: ConversationState) -> str:
            # If tool calls exist, go to executor
            if state.get("pending_tool_calls"):
                return "tool_executor"
            
            # Check if selected_agent suggests a handoff (or continuation)
            # In a true supervisor mode, we might go back to supervisor. 
            # But here we want direct handoff.
            selected_agent = state.get("selected_agent")
            if selected_agent:
                 # Limitation: We don't know "who ran" just by looking at state unless we add it.
                 # BUT, we can just return the selected_agent node name.
                 # If it causes a self-loop, LangGraph usually handles it (min_steps/max_steps).
                 # To avoid infinite self-loops without generation, we might want a check.
                 # For MVP handoff: valid if target_agent != current_agent (which we can't easily see here without node info).
                 
                 # However, if selected_agent is set, we route there.
                 # If it's END, we go END.
                 target_node = f"agent__{selected_agent}"
                 
                 # We need to make sure this edge is valid. 
                 # The route_map contains all agents.
                 if target_node in route_map:
                     return target_node

            return END

        def tool_router(state: ConversationState) -> str:
            # After tools, go back to the agent who called them
            return f"agent__{state.get('selected_agent')}"

        route_map = {
            f"agent__{agent_id}": f"agent__{agent_id}" for agent_id in domain.agents
        }
        
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges("supervisor", route, route_map)
        
        for agent_id in domain.agents:
            node_name = f"agent__{agent_id}"
            # Agent can go to: ToolExecutor, Other Agents (Handoff), or END
            destinations = {**route_map, "tool_executor": "tool_executor", END: END}
            graph.add_conditional_edges(node_name, agent_router, destinations)
            
        graph.add_conditional_edges("tool_executor", tool_router, route_map)

        checkpointer = MemorySaver()
        return graph.compile(checkpointer=checkpointer)
