"""
Send message use case (MVP).

Routes a message to an agent (via domain config) and returns an assistant reply.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4
import functools
import asyncio
import queue
import threading

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.workflow_log import WorkflowLog
from src.domain.repositories.conversation_repository import IConversationRepository
from src.domain.repositories.workflow_log_repository import IWorkflowLogRepository
from src.infrastructure.config import ConfigBundle, YamlConfigLoader
from src.infrastructure.langgraph import ConversationGraphBuilder, ConversationState
from src.infrastructure.llm import StreamingLLM
from src.infrastructure.config.skill_loader import SkillLoader
from src.domain.repositories.skill_repository import ISkillRepository
from src.application.use_cases.skills import get_effective_system_prompt
from pathlib import Path
import queue
import threading
import asyncio


@dataclass(frozen=True)
class SendMessageRequest:
    """Input DTO for sending a message."""

    domain_id: str
    message: str
    role: str = "user"
    conversation_id: str | None = None
    subject: str = ""
    enable_thinking: bool = False


@dataclass(frozen=True)
class SendMessageResponse:
    """Output DTO for send message."""

    domain_id: str
    agent_id: str
    conversation_id: str
    reply: str
    messages: list[dict]


@dataclass(frozen=True)
class SendMessageStreamEvent:
    """Streaming event emitted while generating a response."""

    type: str
    text: str | None = None
    response: SendMessageResponse | None = None
    agent_id: str | None = None
    metadata: dict | None = None


@dataclass
class SendMessageUseCase:
    """Application use case for sending a chat message."""

    loader: YamlConfigLoader
    graph_builder: ConversationGraphBuilder
    llm: StreamingLLM
    conversation_repo: IConversationRepository | None = None
    workflow_log_repo: IWorkflowLogRepository | None = None
    skill_repo: ISkillRepository | None = None
    skill_loader: SkillLoader | None = None
    _bundle_cache: ConfigBundle | None = None
    _bundle_cache_hash: str | None = None

    def _bundle(self) -> ConfigBundle:
        current_hash = self.loader.snapshot().hash
        if self._bundle_cache is None or self._bundle_cache_hash != current_hash:
            self._bundle_cache = self.loader.load_bundle()
            self._bundle_cache_hash = current_hash
        return self._bundle_cache

    def invalidate_cache(self) -> None:
        """Force configs to reload on the next request."""
        self._bundle_cache = None
        self._bundle_cache_hash = None

    def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        bundle = self._bundle()
        domain = bundle.domains.get(request.domain_id)
        if domain is None:
            raise ValueError(f"Unknown domain_id: {request.domain_id}")

        conversation_id = request.conversation_id or str(uuid4())
        if self.conversation_repo is not None:
            existing = self.conversation_repo.get_conversation(conversation_id)
            if existing is None:
                self.conversation_repo.create_conversation(
                    Conversation(
                        id=conversation_id,
                        domain_id=request.domain_id,
                        created_by_role=request.role,
                        created_by_sub=request.subject,
                    )
                )
            elif (
                request.conversation_id is not None
                and existing.created_by_sub
                and request.subject
            ):
                # Prevent users from writing into other users' conversations.
                if existing.created_by_sub != request.subject:
                    raise PermissionError("Not allowed to access this conversation.")
            self.conversation_repo.add_message(
                Message(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    role="user",
                    content=request.message,
                )
            )

        graph = self.graph_builder.build(domain, bundle.agents)
        initial_state: ConversationState = {
            "domain_id": request.domain_id,
            "messages": [{"role": "user", "content": request.message}],
        }
        final_state = graph.invoke(initial_state, config={"configurable": {"thread_id": conversation_id}})

        # Use the agent that actually did the work (or checking persistent state)
        # Verify if graph produced an assistant message
        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        reply_text = ""
        agent_id = domain.default_agent

        if last_message and last_message["role"] == "assistant":
            # Graph executed the agent. Use its output.
            reply_text = last_message["content"]
            # Try to resolve which agent generated it. 
            # In stateless execution, we might fallback to default if None
            agent_id = final_state.get("selected_agent") or agent_id 
        else:
             # Fallback to old behavior (Graph was just a router)
            selected_agent = final_state.get("selected_agent", domain.default_agent)
            agent = bundle.agents.get(selected_agent)
            if agent is None:
                # Handle case where selected_agent is explicitly None
                agent = bundle.agents.get(domain.default_agent)
                selected_agent = domain.default_agent
                
            agent_id = selected_agent
            
            # Load skills and get effective system prompt
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
            
            effective_prompt = get_effective_system_prompt(agent, list(all_skills.values()))
            
            reply_parts: list[str] = []
            for chunk in self.llm.stream_chat(
                model=agent.model_name,
                system_prompt=effective_prompt,
                messages=[{"role": "user", "content": request.message}],
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
            ):
                reply_parts.append(chunk)
            reply_text = "".join(reply_parts)
            messages = [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": reply_text},
            ]

        if self.conversation_repo is not None:
            # Sync all assistant messages that might have come from the graph
            existing_messages = self.conversation_repo.list_messages(conversation_id)
            existing_contents = {m.content for m in existing_messages if m.role == "assistant"}
            
            for msg in messages:
                if msg["role"] == "assistant" and msg["content"] not in existing_contents:
                    self.conversation_repo.add_message(
                        Message(
                            id=str(uuid4()),
                            conversation_id=conversation_id,
                            role="assistant",
                            content=msg["content"],
                            metadata={"agent_id": str(agent_id)},
                        )
                    )
        return SendMessageResponse(
            domain_id=request.domain_id,
            agent_id=str(agent_id or domain.default_agent),
            conversation_id=conversation_id,
            reply=reply_text,
            messages=messages,
        )

    async def stream(self, request: SendMessageRequest) -> Iterable[SendMessageStreamEvent]:
        """Stream response events for a request.

        Notes
        -----
        Uses LangGraph streaming to surface routing decisions, then streams tokens from
        the configured LLM provider.
        """
        bundle = await self._run_sync(self.loader.load_bundle)
        domain = bundle.domains.get(request.domain_id)
        if domain is None:
            raise ValueError(f"Unknown domain_id: {request.domain_id}")

        conversation_id = request.conversation_id or str(uuid4())
        if self.conversation_repo is not None:
            existing = await self._run_sync(self.conversation_repo.get_conversation, conversation_id)
            if existing is None:
                await self._run_sync(
                    self.conversation_repo.create_conversation,
                    Conversation(
                        id=conversation_id,
                        domain_id=request.domain_id,
                        created_by_role=request.role,
                        created_by_sub=request.subject,
                    )
                )
            elif (
                request.conversation_id is not None
                and existing.created_by_sub
                and request.subject
            ):
                if existing.created_by_sub != request.subject:
                    raise PermissionError("Not allowed to access this conversation.")
            await self._run_sync(
                self.conversation_repo.add_message,
                Message(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    role="user",
                    content=request.message,
                )
            )

        graph = self.graph_builder.build(domain, bundle.agents)
        
        # Build initial messages with optional thinking instruction
        user_message = {"role": "user", "content": request.message}
        initial_messages = [user_message]
        
        # When thinking mode enabled, prepend a system instruction
        if request.enable_thinking:
            thinking_instruction = {
                "role": "system",
                "content": (
                    "Before responding, wrap your internal reasoning inside <think>...</think> tags. "
                    "Show your thought process step by step. After the </think> tag, provide your final answer."
                )
            }
            initial_messages = [thinking_instruction, user_message]
        
        initial_state: ConversationState = {
            "domain_id": request.domain_id,
            "messages": initial_messages,
        }

        selected_agent: str | None = None
        last_state: ConversationState | None = None
        started = datetime.now(UTC)

        processed_thoughts_count = 0 
        accumulated_thoughts = []
        reply_text = ""
        is_thinking = False
        thought_buffer = ""
        
        # Async Queue for non-blocking consumption
        loop = asyncio.get_running_loop()
        token_queue = asyncio.Queue(maxsize=500)
        
        def token_callback(token: str):
            loop.call_soon_threadsafe(token_queue.put_nowait, {"type": "token", "content": token})
            
        def run_graph():
            try:
                # Pass token_callback in configuration
                config = {"configurable": {"thread_id": conversation_id, "token_callback": token_callback}}
                for state in graph.stream(initial_state, config=config, stream_mode="values"):
                    loop.call_soon_threadsafe(token_queue.put_nowait, {"type": "state", "content": state})
                loop.call_soon_threadsafe(token_queue.put_nowait, None) # Done
            except Exception as e:
                 loop.call_soon_threadsafe(token_queue.put_nowait, e)
                
        threading.Thread(target=run_graph, daemon=True).start()
        
        while True:
            # Async get - releases event loop!
            try:
                item = await asyncio.wait_for(token_queue.get(), timeout=120.0) # 2 min timeout safety
            except asyncio.TimeoutError:
                # Thread might have died or stuck
                yield SendMessageStreamEvent(type="error", text="Stream timeout")
                break
                
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
                
            if item["type"] == "token":
                chunk = item["content"]
                
                # REFINED STATE MACHINE FOR <THINK> TAGS
                # Current state variables defined above: is_thinking (bool), thought_buffer (str)
                
                # Check for tag transitions
                # Note: This handles potential split-across-chunks by checking the combined text
                # but for high-speed streaming, we check if the chunk contains the tags.
                
                if "<think>" in chunk:
                    parts = chunk.split("<think>", 1)
                    # Content before <think> is normal
                    if parts[0]:
                        yield SendMessageStreamEvent(type="delta", text=parts[0])
                        reply_text += parts[0]
                    
                    is_thinking = True
                    chunk = parts[1] # Process remainder as thinking
                
                if is_thinking:
                    if "</think>" in chunk:
                        parts = chunk.split("</think>", 1)
                        # Content before </think> is thinking
                        if parts[0]:
                            thought_buffer += parts[0]
                            yield SendMessageStreamEvent(type="thought", text=parts[0])
                        
                        # Finish this thinking block
                        accumulated_thoughts.append({
                            "content": thought_buffer,
                            "agentName": selected_agent or "Assistant",
                            "timestamp": datetime.now(UTC).isoformat()
                        })
                        thought_buffer = ""
                        is_thinking = False
                        
                        # Remainder is normal content
                        if parts[1]:
                            yield SendMessageStreamEvent(type="delta", text=parts[1])
                            reply_text += parts[1]
                    else:
                        # Pure thinking
                        thought_buffer += chunk
                        yield SendMessageStreamEvent(type="thought", text=chunk)
                else:
                    # Pure normal content
                    reply_text += chunk
                    yield SendMessageStreamEvent(type="delta", text=chunk)
                
                continue
                
            state = item["content"]
            last_state = state
            agent_id = state.get("selected_agent")
            if agent_id and agent_id != selected_agent:
                selected_agent = agent_id
                if self.workflow_log_repo:
                    agent_obj = bundle.agents.get(selected_agent)
                    self.workflow_log_repo.save(WorkflowLog(
                        id=str(uuid4()),
                        conversation_id=conversation_id,
                        agent_id=selected_agent,
                        agent_name=agent_obj.name if agent_obj else selected_agent,
                        event_type="handoff",
                        created_at=datetime.now(UTC)
                    ))
                yield SendMessageStreamEvent(
                    type="agent_selected", agent_id=selected_agent
                )
            
            # Check for thoughts
            thoughts = state.get("thoughts", [])
            if len(thoughts) > processed_thoughts_count:
                new_thoughts = thoughts[processed_thoughts_count:]
                for t in new_thoughts:
                    # Log thought to DB
                    thought_text = t.get("thought", "")
                    
                    # Accumulate for persistence
                    accumulated_thoughts.append({
                        "content": thought_text,
                        "agentName": selected_agent or "Router",
                        "timestamp": datetime.now(UTC).isoformat()
                    })

                    # DETECT SKILL USAGE IN THOUGHTS (CoT Tagging)
                    # Pattern: [USING SKILL: skill_id]
                    import re
                    skill_match = re.search(r"\[USING SKILL:\s*(.*?)\]", thought_text, re.IGNORECASE)
                    if skill_match:
                        skill_id = skill_match.group(1).strip()
                        # Emit a 'tool_start' event so the frontend renders the Badge
                        # behave as if it's a tool for observability purposes
                        if self.workflow_log_repo:
                            self.workflow_log_repo.save(WorkflowLog(
                                id=str(uuid4()),
                                conversation_id=conversation_id,
                                agent_id=selected_agent or domain.default_agent,
                                agent_name=selected_agent or domain.default_agent,
                                event_type="tool_start", # Reuse existing type for badge
                                content=f"Using skill: {skill_id}",
                                metadata={"skill_id": skill_id, "source": "thought_tag"},
                                created_at=datetime.now(UTC)
                            ))
                        
                        yield SendMessageStreamEvent(
                            type="tool_start",
                            text=f"Applying {skill_id}",
                            agent_id=selected_agent,
                            metadata={"skill_id": skill_id}
                        )

                    if self.workflow_log_repo:
                        self.workflow_log_repo.save(WorkflowLog(
                            id=str(uuid4()),
                            conversation_id=conversation_id,
                            agent_id=selected_agent or 'router',
                            agent_name='Router' if not selected_agent else selected_agent,
                            event_type="thought",
                            content=thought_text,
                            metadata={"reason": thought_text},
                            created_at=datetime.now(UTC)
                        ))
                    
                    yield SendMessageStreamEvent(
                        type="thought",
                        text=thought_text,
                        agent_id=selected_agent or "router"
                    )
                processed_thoughts_count = len(thoughts)
            
            # Check for tool calls (Skill Usage)
            pending_tools = state.get("pending_tool_calls", [])
            if pending_tools:
                for tool in pending_tools:
                    # Avoid duplicates if possible, though stream might re-emit.
                    # Simple de-dupe strategy: check if we already yielded for this thought/step?
                    # For now, relying on unique ID would be better, but we don't track yielded tool/call IDs.
                    # MVP: Emit. Handler should handle or UI will show multiple.
                    # Refinement: We can track yielded_tool_call_ids if needed.
                    
                    # Log to DB
                    meta = tool.get("metadata", {})
                    if self.workflow_log_repo:
                         self.workflow_log_repo.save(WorkflowLog(
                            id=str(uuid4()),
                            conversation_id=conversation_id,
                            agent_id=selected_agent or domain.default_agent,
                            agent_name=selected_agent or domain.default_agent,
                            event_type="tool_start",
                            content=f"Using tool: {tool['tool']}",
                            metadata={**meta, "tool": tool["tool"], "params": tool["params"]},
                            created_at=datetime.now(UTC)
                        ))
                    
                    yield SendMessageStreamEvent(
                        type="tool_start",
                        text=f"Executing {tool['tool']}",
                        agent_id=selected_agent,
                        metadata=meta
                    )

        final_state = last_state or initial_state
        
        # Check if graph produced valid output
        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        final_agent_id = selected_agent or domain.default_agent # Use tracked agent from loop

        if last_message and last_message["role"] == "assistant":
             # If we haven't streamed anything yet (e.g. node didn't use callback) 
             # or if there's more content, yield it.
             # Actually, if reply_text is empty, we MUST yield the full message.
             # If not empty, we assume we already streamed most of it.
             graph_reply = last_message["content"]
             if not reply_text:
                 reply_text = graph_reply
                 yield SendMessageStreamEvent(type="delta", text=reply_text)
             elif len(graph_reply) > len(reply_text):
                 # Yield the remaining part if any (rare edge case)
                 diff = graph_reply[len(reply_text):]
                 if diff:
                     yield SendMessageStreamEvent(type="delta", text=diff)
                     reply_text = graph_reply
             
        else:
            # Fallback for Router-only graph
            selected_agent_final = final_state.get("selected_agent") or selected_agent or domain.default_agent
            agent = bundle.agents.get(selected_agent_final)
            
            # Additional safety check
            if agent is None:
                agent = bundle.agents.get(domain.default_agent)
                selected_agent_final = domain.default_agent

            final_agent_id = selected_agent_final

            # Load skills and get effective system prompt
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
            
            effective_prompt = get_effective_system_prompt(agent, list(all_skills.values()))

            reply_parts: list[str] = []
            llm_messages = [{"role": "user", "content": request.message}]
            
            # Use non-blocking iterator for sync LLM stream
            async for chunk in self._iterate_sync(
                self.llm.stream_chat(
                    model=agent.model_name,
                    system_prompt=effective_prompt,
                    messages=llm_messages,
                    temperature=agent.temperature,
                    max_tokens=agent.max_tokens,
                )
            ):
                reply_parts.append(chunk)
                yield SendMessageStreamEvent(type="delta", text=chunk)

            reply_text = "".join(reply_parts)
            messages.append({"role": "assistant", "content": reply_text})

        if self.conversation_repo is not None:
            # Sync all assistant messages from graph state
            existing_messages = await self._run_sync(self.conversation_repo.list_messages, conversation_id)
            existing_contents = {m.content for m in existing_messages if m.role == "assistant"}

            for msg in messages:
                if msg["role"] == "assistant" and msg["content"] not in existing_contents:
                    await self._run_sync(
                        self.conversation_repo.add_message,
                        Message(
                            id=str(uuid4()),
                            conversation_id=conversation_id,
                            role="assistant",
                            content=msg["content"],
                            metadata={
                                "agent_id": str(final_agent_id),
                                "thoughts": accumulated_thoughts if msg["content"] == reply_text else []
                            },
                        )
                    )

        duration_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
        _ = duration_ms  # reserved for future metrics / metadata

        yield SendMessageStreamEvent(
            type="done",
            response=SendMessageResponse(
                domain_id=request.domain_id,
                agent_id=str(final_agent_id),
                conversation_id=conversation_id,
                reply=reply_text,
                messages=messages,
            ),
        )

    async def _run_sync(self, func, *args, **kwargs):
        """Run a synchronous function in a separate thread."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    async def _iterate_sync(self, generator):
        """Iterate a synchronous generator in a separate thread."""
        loop = asyncio.get_running_loop()
        q = asyncio.Queue(maxsize=100)
        
        def _producer():
            try:
                for item in generator:
                    loop.call_soon_threadsafe(q.put_nowait, item)
                loop.call_soon_threadsafe(q.put_nowait, None)
            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, e)
                
        loop.run_in_executor(None, _producer)
        
        while True:
            item = await q.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            yield item
