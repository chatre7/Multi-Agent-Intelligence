"""FastAPI application factory (MVP)."""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Response
from passlib.hash import pbkdf2_sha256
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from src.domain.entities.conversation import Conversation

from src.application.use_cases.conversations import (
    SendMessageRequest,
    SendMessageUseCase,
)
from src.application.use_cases.registry import (
    BumpAgentVersionRequest,
    BumpAgentVersionUseCase,
    GetRegisteredAgentRequest,
    GetRegisteredAgentUseCase,
    ListRegisteredAgentsRequest,
    ListRegisteredAgentsUseCase,
    PromoteRegisteredAgentRequest,
    PromoteRegisteredAgentUseCase,
    RegisterAgentRequest,
    RegisterAgentUseCase,
)
from src.application.use_cases.tools import (
    ApproveToolRunRequest,
    ApproveToolRunUseCase,
    ExecuteToolRunRequest,
    ExecuteToolRunUseCase,
    ListToolRunsRequest,
    ListToolRunsUseCase,
    RejectToolRunRequest,
    RejectToolRunUseCase,
    RequestToolRunRequest,
    RequestToolRunUseCase,
)
from src.infrastructure.auth import (
    JwtConfig,
    Permission,
    create_access_token,
    get_claims_from_token,
    parse_bearer,
    parse_permissions,
    permissions_for_role,
    require_permission_set,
    serialize_permissions,
)
from src.infrastructure.config import YamlConfigLoader
from src.infrastructure.langgraph import ConversationGraphBuilder
from src.infrastructure.llm.streaming import llm_from_env
from src.infrastructure.persistence.in_memory.conversations import (
    InMemoryConversationRepository,
)
from src.infrastructure.persistence.in_memory.workflow_logs import (
    InMemoryWorkflowLogRepository,
)
from src.infrastructure.persistence.in_memory.registered_agents import (
    InMemoryRegisteredAgentRepository,
)
from src.infrastructure.persistence.in_memory.tool_runs import InMemoryToolRunRepository
from src.infrastructure.persistence.sqlite.conversations import (
    SqliteConversationRepository,
)
from src.infrastructure.persistence.sqlite.workflow_logs import (
    SqliteWorkflowLogRepository,
)
from src.infrastructure.persistence.sqlite.registered_agents import (
    SqliteRegisteredAgentRepository,
)
from src.infrastructure.persistence.sqlite.tool_runs import SqliteToolRunRepository
from src.presentation.metrics import (
    CHAT_MESSAGES_TOTAL,
    TOOL_RUNS_APPROVED_TOTAL,
    TOOL_RUNS_EXECUTED_TOTAL,
    TOOL_RUNS_REJECTED_TOTAL,
    TOOL_RUNS_REQUESTED_TOTAL,
)
from src.presentation.websocket.handlers import register_websocket_routes

_CONVERSATION_CURSOR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T.+\|[0-9a-fA-F-]{8,}$")


class ChatRequest(BaseModel):
    domain_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None


class ToolRunCreateRequest(BaseModel):
    tool_id: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolRunRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ConversationCreateRequest(BaseModel):
    domain_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)


class RegistryAgentCreateRequest(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    endpoint: str = Field(default="")
    version: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    capabilities: list[str] = Field(default_factory=list)


class RegistryAgentPromoteRequest(BaseModel):
    state: str = Field(..., min_length=1)


class RegistryAgentBumpVersionRequest(BaseModel):
    kind: str = Field(..., min_length=1)


class RegistryAgentHeartbeatRequest(BaseModel):
    pass


def create_app() -> FastAPI:
    loader = YamlConfigLoader.from_default_backend_root()
    conversation_repo_name = (
        os.getenv("CONVERSATION_REPO", "memory") or "memory"
    ).lower()
    if conversation_repo_name == "sqlite":
        conversation_db = os.getenv("CONVERSATION_DB", "conversations.db")
        conversation_repo = SqliteConversationRepository(db_path=conversation_db)
        workflow_log_repo = SqliteWorkflowLogRepository(db_path=conversation_db)
    else:
        conversation_repo = InMemoryConversationRepository()
        workflow_log_repo = InMemoryWorkflowLogRepository()

    use_case = SendMessageUseCase(
        loader=loader,
        graph_builder=ConversationGraphBuilder(),
        llm=llm_from_env(),
        conversation_repo=conversation_repo,
        workflow_log_repo=workflow_log_repo,
    )
    tool_run_repo_name = (os.getenv("TOOL_RUN_REPO", "memory") or "memory").lower()
    if tool_run_repo_name == "sqlite":
        db_path = os.getenv("TOOL_RUN_DB", "tool_runs.db")
        tool_run_repo = SqliteToolRunRepository(db_path=db_path)
    else:
        tool_run_repo = InMemoryToolRunRepository()
    request_tool_run_uc = RequestToolRunUseCase(loader=loader, repo=tool_run_repo)
    approve_tool_run_uc = ApproveToolRunUseCase(loader=loader, repo=tool_run_repo)
    execute_tool_run_uc = ExecuteToolRunUseCase(loader=loader, repo=tool_run_repo)
    reject_tool_run_uc = RejectToolRunUseCase(loader=loader, repo=tool_run_repo)
    list_tool_runs_uc = ListToolRunsUseCase(repo=tool_run_repo)

    registry_repo_name = (os.getenv("REGISTRY_REPO", "memory") or "memory").lower()
    if registry_repo_name == "sqlite":
        registry_db = os.getenv("REGISTRY_DB", "registered_agents.db")
        registered_agent_repo = SqliteRegisteredAgentRepository(db_path=registry_db)
    else:
        registered_agent_repo = InMemoryRegisteredAgentRepository()
    register_agent_uc = RegisterAgentUseCase(repo=registered_agent_repo)
    promote_agent_uc = PromoteRegisteredAgentUseCase(repo=registered_agent_repo)
    bump_agent_version_uc = BumpAgentVersionUseCase(repo=registered_agent_repo)
    list_registered_agents_uc = ListRegisteredAgentsUseCase(repo=registered_agent_repo)
    get_registered_agent_uc = GetRegisteredAgentUseCase(repo=registered_agent_repo)

    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="Multi-Agent Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    auth_mode = (os.getenv("AUTH_MODE", "jwt") or "jwt").lower()
    jwt_config = JwtConfig(secret=os.getenv("AUTH_SECRET", "dev-secret"))

    users_env = os.getenv("AUTH_USERS", "")
    users: dict[str, dict[str, str]] = {}
    for item in [p.strip() for p in users_env.split(";") if p.strip()]:
        parts = item.split(":")
        if len(parts) != 3:
            continue
        username, password, role = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if username and password and role:
            users[username] = {"password": password, "role": role.lower()}

    def verify_password(stored: str, provided: str) -> bool:
        if stored.startswith("$pbkdf2-sha256$"):
            try:
                return pbkdf2_sha256.verify(provided, stored)
            except Exception:  # noqa: BLE001
                return False
        return secrets.compare_digest(stored, provided)

    def resolve_principal(
        *,
        x_role: str | None,
        authorization: str | None,
    ) -> tuple[str, str, frozenset]:
        if auth_mode == "jwt":
            token = parse_bearer(authorization)
            if not token:
                raise HTTPException(status_code=401, detail="Missing bearer token")
            try:
                claims = get_claims_from_token(token, config=jwt_config)
                sub = str(claims.get("sub", ""))
                role = str(claims.get("role", "")).lower()
                perms = parse_permissions(claims.get("perms"))
                return sub, role, perms
            except PermissionError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
        role = (x_role or "user").lower()
        return "", role, permissions_for_role(role)

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True}

    @app.get("/v1/health/details")
    def health_details(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.HEALTH_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        return {
            "ok": True,
            "auth_mode": auth_mode,
            "conversation_repo": conversation_repo_name,
            "tool_run_repo": tool_run_repo_name,
            "config_counts": {
                "domains": len(bundle.domains),
                "agents": len(bundle.agents),
                "tools": len(bundle.tools),
            },
            "version": "0.1.0",
        }

    @app.get("/v1/metrics")
    def metrics(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> Response:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.METRICS_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/auth/login")
    def login(payload: LoginRequest) -> dict[str, Any]:
        if auth_mode != "jwt":
            raise HTTPException(status_code=404, detail="Auth disabled")
        user = users.get(payload.username)
        if user is None or not verify_password(user["password"], payload.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        role = user["role"]
        perms = permissions_for_role(role)
        token = create_access_token(
            subject=payload.username,
            role=role,
            permissions=serialize_permissions(perms),
            config=jwt_config,
        )
        return {"access_token": token, "token_type": "bearer", "role": role}

    @app.get("/v1/auth/me")
    def me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        if auth_mode != "jwt":
            raise HTTPException(status_code=404, detail="Auth disabled")
        token = parse_bearer(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        try:
            claims = get_claims_from_token(token, config=jwt_config)
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        role = str(claims.get("role", "")).lower()
        subject = str(claims.get("sub", ""))
        perms = claims.get("perms", [])
        if not isinstance(perms, list):
            perms = []
        return {"sub": subject, "role": role, "perms": perms}

    @app.post("/v1/config/reload")
    def reload_config(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.CONFIG_RELOAD)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        use_case.invalidate_cache()
        return {"ok": True}

    @app.get("/v1/config/status")
    def config_status(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.DOMAIN_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        snap = loader.snapshot()
        return {
            "hash": snap.hash,
            "file_count": snap.file_count,
            "generated_at": snap.generated_at,
        }

    @app.get("/v1/config/sync")
    def config_sync(
        since_hash: str | None = None,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.DOMAIN_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        snap = loader.snapshot()
        if since_hash and since_hash == snap.hash:
            return {"changed": False, "hash": snap.hash}

        bundle = loader.load_bundle()
        return {
            "changed": True,
            "hash": snap.hash,
            "counts": {
                "domains": len(bundle.domains),
                "agents": len(bundle.agents),
                "tools": len(bundle.tools),
            },
            "bundle": {
                "domains": [d.to_dict() for d in bundle.domains.values()],
                "agents": [a.to_dict() for a in bundle.agents.values()],
                "tools": [t.to_dict() for t in bundle.tools.values()],
            },
        }

    @app.get("/v1/domains")
    def list_domains(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        _sub, role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.DOMAIN_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        domains = []
        for domain in bundle.domains.values():
            if role in {r.lower() for r in domain.allowed_roles}:
                domains.append(domain.to_dict())
        return domains

    @app.get("/v1/domains/{domain_id}")
    def get_domain(
        domain_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.DOMAIN_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        domain = bundle.domains.get(domain_id)
        if domain is None:
            raise HTTPException(status_code=404, detail="Unknown domain_id")
        if role not in {r.lower() for r in domain.allowed_roles}:
            raise HTTPException(
                status_code=403, detail="Role not allowed for this domain"
            )
        return domain.to_dict()

    @app.get("/v1/agents")
    def list_agents(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        return [agent.to_dict() for agent in bundle.agents.values()]

    @app.get("/v1/agents/{agent_id}")
    def get_agent(
        agent_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        agent = bundle.agents.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Unknown agent_id")
        return agent.to_dict()

    @app.post("/v1/registry/agents")
    def register_agent(
        payload: RegistryAgentCreateRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_WRITE)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        try:
            agent = register_agent_uc.execute(
                RegisterAgentRequest(
                    id=payload.id,
                    name=payload.name,
                    description=payload.description,
                    endpoint=payload.endpoint,
                    version=payload.version,
                    state=payload.state,
                    capabilities=list(payload.capabilities),
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return agent.to_dict()

    @app.get("/v1/registry/agents")
    def list_registered_agents(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        agents = list_registered_agents_uc.execute(ListRegisteredAgentsRequest())
        return [a.to_dict() for a in agents]

    @app.get("/v1/registry/agents/{agent_id}")
    def get_registered_agent(
        agent_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        try:
            agent = get_registered_agent_uc.execute(
                GetRegisteredAgentRequest(agent_id=agent_id)
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return agent.to_dict()

    @app.post("/v1/registry/agents/{agent_id}/promote")
    def promote_registered_agent(
        agent_id: str,
        payload: RegistryAgentPromoteRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_WRITE)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        try:
            agent = promote_agent_uc.execute(
                PromoteRegisteredAgentRequest(agent_id=agent_id, state=payload.state)
            )
        except ValueError as exc:
            msg = str(exc)
            if "Unknown agent_id" in msg:
                raise HTTPException(status_code=404, detail=msg) from exc
            raise HTTPException(status_code=400, detail=msg) from exc
        return agent.to_dict()

    @app.post("/v1/registry/agents/{agent_id}/heartbeat")
    def heartbeat_registered_agent(
        agent_id: str,
        payload: RegistryAgentHeartbeatRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _ = payload
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_WRITE)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        try:
            agent = get_registered_agent_uc.execute(
                GetRegisteredAgentRequest(agent_id=agent_id)
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        agent.heartbeat()
        registered_agent_repo.upsert(agent)
        return agent.to_dict()

    @app.post("/v1/registry/agents/{agent_id}/version/bump")
    def bump_registered_agent_version(
        agent_id: str,
        payload: RegistryAgentBumpVersionRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.AGENT_WRITE)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        try:
            agent = bump_agent_version_uc.execute(
                BumpAgentVersionRequest(agent_id=agent_id, kind=payload.kind)
            )
        except ValueError as exc:
            msg = str(exc)
            if "Unknown agent_id" in msg:
                raise HTTPException(status_code=404, detail=msg) from exc
            raise HTTPException(status_code=400, detail=msg) from exc
        return agent.to_dict()

    @app.get("/v1/tools")
    def list_tools(
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.TOOL_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        return [tool.to_dict() for tool in bundle.tools.values()]

    @app.get("/v1/tools/{tool_id}")
    def get_tool(
        tool_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.TOOL_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        bundle = use_case.loader.load_bundle()
        tool = bundle.tools.get(tool_id)
        if tool is None:
            raise HTTPException(status_code=404, detail="Unknown tool_id")
        return tool.to_dict()

    @app.post("/v1/chat")
    def chat(
        payload: ChatRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.CHAT_SEND)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        CHAT_MESSAGES_TOTAL.inc()
        bundle = use_case.loader.load_bundle()
        domain = bundle.domains.get(payload.domain_id)
        if domain is None:
            raise HTTPException(status_code=404, detail="Unknown domain_id")
        if role not in {r.lower() for r in domain.allowed_roles}:
            raise HTTPException(
                status_code=403, detail="Role not allowed for this domain"
            )

        try:
            response = use_case.execute(
                SendMessageRequest(
                    domain_id=payload.domain_id,
                    message=payload.message,
                    role=role,
                    conversation_id=payload.conversation_id,
                    subject=sub,
                )
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return asdict(response)

    @app.get("/v1/conversations/{conversation_id}")
    def get_conversation(
        conversation_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.CHAT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        convo = conversation_repo.get_conversation(conversation_id)
        if convo is None:
            raise HTTPException(status_code=404, detail="Unknown conversation_id")
        if (
            role not in {"admin", "developer"}
            and convo.created_by_sub
            and convo.created_by_sub != sub
        ):
            raise HTTPException(status_code=404, detail="Unknown conversation_id")
        return convo.to_dict()

    @app.get("/v1/conversations/{conversation_id}/messages")
    def list_conversation_messages(
        conversation_id: str,
        limit: int = 200,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.CHAT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        convo = conversation_repo.get_conversation(conversation_id)
        if convo is None:
            raise HTTPException(status_code=404, detail="Unknown conversation_id")
        if (
            role not in {"admin", "developer"}
            and convo.created_by_sub
            and convo.created_by_sub != sub
        ):
            raise HTTPException(status_code=404, detail="Unknown conversation_id")
        messages = conversation_repo.list_messages(conversation_id, limit=limit)
        return [m.to_dict() for m in messages]

    @app.post("/v1/conversations")
    def start_conversation(
        payload: ConversationCreateRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.CHAT_SEND)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        from uuid import uuid4
        conversation_id = str(uuid4())
        convo = Conversation(
            id=conversation_id,
            domain_id=payload.domain_id,
            created_by_role=role,
            created_by_sub=sub,
            title=f"Chat with {payload.agent_id}",
        )
        conversation_repo.create_conversation(convo)
        return convo.to_dict()

    @app.get("/v1/conversations")
    def list_conversations(
        response: Response,
        limit: int = 50,
        cursor: str | None = None,
        domain_id: str | None = None,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.CHAT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if cursor is not None and not _CONVERSATION_CURSOR_PATTERN.match(
            cursor.strip()
        ):
            raise HTTPException(status_code=400, detail="Invalid cursor format.")

        limit_int = int(limit)
        if limit_int < 1:
            limit_int = 1
        if limit_int > 200:
            limit_int = 200

        fetched = conversation_repo.list_conversations(
            limit=limit_int + 1,
            cursor=cursor,
            domain_id=domain_id,
            created_by_sub=None if role in {"admin", "developer"} else sub,
        )
        has_more = len(fetched) > limit_int
        conversations = fetched[:limit_int]
        next_cursor = conversation_repo.get_next_cursor(
            conversations, has_more=has_more
        )
        if next_cursor:
            response.headers["x-next-cursor"] = next_cursor
        return [c.to_dict() for c in conversations]

    @app.get("/v1/conversations/{conversation_id}/workflow-logs")
    def list_workflow_logs(
        conversation_id: str,
        limit: int = 100,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> list[dict[str, Any]]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.CHAT_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        convo = conversation_repo.get_conversation(conversation_id)
        if convo is None:
            raise HTTPException(status_code=404, detail="Unknown conversation_id")
        if (
            role not in {"admin", "developer"}
            and convo.created_by_sub
            and convo.created_by_sub != sub
        ):
            raise HTTPException(status_code=404, detail="Unknown conversation_id")

        logs = workflow_log_repo.list_by_conversation(conversation_id, limit=limit)
        return [
            {
                "id": l.id,
                "agentId": l.agent_id,
                "agentName": l.agent_name,
                "type": l.event_type,
                "content": l.content,
                "metadata": l.metadata,
                "timestamp": l.created_at.isoformat(),
            }
            for l in logs
        ]

    @app.delete("/v1/workflow-logs/{log_id}")
    def delete_workflow_log(
        log_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _sub, _role, perms = resolve_principal(
            x_role=x_role, authorization=authorization
        )
        try:
            require_permission_set(perms, Permission.CHAT_SEND)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        workflow_log_repo.delete(log_id)
        return {"status": "success"}

    @app.post("/v1/tool-runs")
    def request_tool_run(
        payload: ToolRunCreateRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        TOOL_RUNS_REQUESTED_TOTAL.inc()
        try:
            created = request_tool_run_uc.execute(
                RequestToolRunRequest(
                    tool_id=payload.tool_id,
                    parameters=payload.parameters,
                    requested_by_role=role,
                    requested_by_permissions=perms,
                    requested_by_subject=sub,
                )
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        tool_run = tool_run_repo.get(created.run_id)
        if tool_run is None:
            raise HTTPException(status_code=500, detail="Tool run was not persisted")
        return tool_run.to_dict()

    @app.get("/v1/tool-runs/{run_id}")
    def get_tool_run(
        run_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.TOOL_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        tool_run = tool_run_repo.get(run_id)
        if tool_run is None:
            raise HTTPException(status_code=404, detail="Unknown run_id")
        if (
            role not in {"admin", "developer"}
            and tool_run.requested_by_sub
            and tool_run.requested_by_sub != sub
        ):
            raise HTTPException(status_code=404, detail="Unknown run_id")
        return tool_run.to_dict()

    @app.get("/v1/tool-runs")
    def list_tool_runs(
        response: Response,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
        limit: int = 50,
        status: str | None = None,
        tool_id: str | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            require_permission_set(perms, Permission.TOOL_READ)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        try:
            result = list_tool_runs_uc.execute(
                ListToolRunsRequest(
                    limit=limit,
                    status=status,
                    tool_id=tool_id,
                    requested_by_sub=None if role in {"admin", "developer"} else sub,
                    cursor=cursor,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if result.next_cursor:
            response.headers["x-next-cursor"] = result.next_cursor
        return [run.to_dict() for run in result.runs]

    @app.post("/v1/tool-runs/{run_id}/approve")
    def approve_tool_run(
        run_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            approve_tool_run_uc.execute(
                ApproveToolRunRequest(
                    run_id=run_id, approved_by_role=role, approved_by_permissions=perms
                )
            )
            TOOL_RUNS_APPROVED_TOTAL.inc()
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        tool_run = tool_run_repo.get(run_id)
        if tool_run is None:
            raise HTTPException(status_code=404, detail="Unknown run_id")
        return tool_run.to_dict()

    @app.post("/v1/tool-runs/{run_id}/execute")
    def execute_tool_run(
        run_id: str,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            execute_tool_run_uc.execute(
                ExecuteToolRunRequest(
                    run_id=run_id, executed_by_role=role, executed_by_permissions=perms
                )
            )
            TOOL_RUNS_EXECUTED_TOTAL.inc()
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        tool_run = tool_run_repo.get(run_id)
        if tool_run is None:
            raise HTTPException(status_code=404, detail="Unknown run_id")
        return tool_run.to_dict()

    @app.post("/v1/tool-runs/{run_id}/reject")
    def reject_tool_run(
        run_id: str,
        payload: ToolRunRejectRequest,
        x_role: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        sub, role, perms = resolve_principal(x_role=x_role, authorization=authorization)
        try:
            reject_tool_run_uc.execute(
                RejectToolRunRequest(
                    run_id=run_id,
                    rejected_by_role=role,
                    rejected_by_permissions=perms,
                    reason=payload.reason,
                )
            )
            TOOL_RUNS_REJECTED_TOTAL.inc()
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            message = str(exc)
            if "Unknown run_id" in message:
                raise HTTPException(status_code=404, detail=message) from exc
            raise HTTPException(status_code=400, detail=message) from exc

        tool_run = tool_run_repo.get(run_id)
        if tool_run is None:
            raise HTTPException(status_code=404, detail="Unknown run_id")
        return tool_run.to_dict()

    register_websocket_routes(
        app,
        use_case,
        request_tool_run_uc=request_tool_run_uc,
        approve_tool_run_uc=approve_tool_run_uc,
        reject_tool_run_uc=reject_tool_run_uc,
        execute_tool_run_uc=execute_tool_run_uc,
        list_tool_runs_uc=list_tool_runs_uc,
    )
    return app
