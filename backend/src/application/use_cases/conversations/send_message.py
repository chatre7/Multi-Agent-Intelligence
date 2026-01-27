"""
Send message use case (MVP).

Routes a message to an agent (via domain config) and returns an assistant reply.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

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


@dataclass(frozen=True)
class SendMessageRequest:
    """Input DTO for sending a message."""

    domain_id: str
    message: str
    role: str = "user"
    conversation_id: str | None = None
    subject: str = ""


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
             # Only add if not already in graph messages? 
             # For now, just ensure we save what we return.
            self.conversation_repo.add_message(
                Message(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    role="assistant",
                    content=reply_text,
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

    def stream(self, request: SendMessageRequest) -> Iterable[SendMessageStreamEvent]:
        """Stream response events for a request.

        Notes
        -----
        Uses LangGraph streaming to surface routing decisions, then streams tokens from
        the configured LLM provider.
        """
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

        selected_agent: str | None = None
        last_state: ConversationState | None = None
        started = datetime.now(UTC)

        processed_thoughts_count = 0 
        reply_text = ""
        
        # Side-channel for tokens from inside graph nodes
        token_queue = queue.Queue()
        
        def token_callback(token: str):
            token_queue.put({"type": "token", "content": token})
            
        def run_graph():
            try:
                # Pass token_callback in configuration
                config = {"configurable": {"thread_id": conversation_id, "token_callback": token_callback}}
                for state in graph.stream(initial_state, config=config, stream_mode="values"):
                    token_queue.put({"type": "state", "content": state})
                token_queue.put(None) # Done
            except Exception as e:
                token_queue.put(e)
                
        threading.Thread(target=run_graph, daemon=True).start()
        
        while True:
            item = token_queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
                
            if item["type"] == "token":
                chunk = item["content"]
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
            
            # Check for new thoughts
            thoughts = state.get("thoughts", [])
            if len(thoughts) > processed_thoughts_count:
                new_thoughts = thoughts[processed_thoughts_count:]
                for t in new_thoughts:
                    if self.workflow_log_repo:
                        self.workflow_log_repo.save(WorkflowLog(
                            id=str(uuid4()),
                            conversation_id=conversation_id,
                            agent_id="router",
                            agent_name="Router",
                            event_type="thought",
                            content=t.get("thought", ""),
                            metadata=t,
                            created_at=datetime.now(UTC)
                        ))
                    yield SendMessageStreamEvent(
                        type="thought",
                        text=t.get("thought", ""),
                        agent_id="router"
                    )
                processed_thoughts_count = len(thoughts)

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
            for chunk in self.llm.stream_chat(
                model=agent.model_name,
                system_prompt=effective_prompt,
                messages=llm_messages,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
            ):
                reply_parts.append(chunk)
                yield SendMessageStreamEvent(type="delta", text=chunk)

            reply_text = "".join(reply_parts)
            messages.append({"role": "assistant", "content": reply_text})

        if self.conversation_repo is not None:
            self.conversation_repo.add_message(
                Message(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    role="assistant",
                    content=reply_text,
                    metadata={"agent_id": str(final_agent_id)},
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
