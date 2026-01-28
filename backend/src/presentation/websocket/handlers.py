"""WebSocket handlers (MVP)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import asdict
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

from src.application.use_cases.conversations import (
    SendMessageRequest,
    SendMessageUseCase,
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
    get_claims_from_token,
    parse_bearer,
    parse_permissions,
    permissions_for_role,
    require_permission_set,
)

_CURSOR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T.+\|[0-9a-fA-F-]{8,}$")

_STREAM_TASKS: dict[str, asyncio.Task] = {}
_CONVERSATION_SOCKETS: dict[str, set[int]] = {}
_SOCKET_SENDERS: dict[int, Any] = {}


def _parse_tool_command(text: str) -> tuple[str, dict] | None:
    raw = text.strip()
    if not raw.startswith("/tool "):
        return None
    rest = raw[len("/tool ") :].strip()
    if not rest:
        return None
    parts = rest.split(" ", 1)
    tool_id = parts[0].strip()
    if not tool_id:
        return None
    params: dict = {}
    if len(parts) == 2 and parts[1].strip():
        try:
            loaded = json.loads(parts[1].strip())
        except json.JSONDecodeError:
            return None
        if not isinstance(loaded, dict):
            return None
        params = loaded
    return tool_id, params


def register_websocket_routes(
    app: FastAPI,
    chat_use_case: SendMessageUseCase,
    request_tool_run_uc: RequestToolRunUseCase | None = None,
    approve_tool_run_uc: ApproveToolRunUseCase | None = None,
    reject_tool_run_uc: RejectToolRunUseCase | None = None,
    execute_tool_run_uc: ExecuteToolRunUseCase | None = None,
    list_tool_runs_uc: ListToolRunsUseCase | None = None,
) -> None:
    @app.websocket("/ws/chat")
    async def chat_socket(websocket: WebSocket) -> None:
        auth_mode = (os.getenv("AUTH_MODE", "jwt") or "jwt").lower()
        claims: dict[str, Any] = {}
        if auth_mode == "jwt":
            jwt_config = JwtConfig(secret=os.getenv("AUTH_SECRET", "dev-secret"))
            token = parse_bearer(websocket.headers.get("authorization"))
            if not token:
                token = websocket.query_params.get("token")

            if not token:
                await websocket.close(code=1008)
                return
            try:
                claims = get_claims_from_token(token, config=jwt_config)
                perms = parse_permissions(claims.get("perms"))
                require_permission_set(perms, Permission.CHAT_SEND)
            except Exception:  # noqa: BLE001
                await websocket.close(code=1008)
                return
        await websocket.accept()

        try:
            while True:
                payload: dict[str, Any] = await websocket.receive_json()
                domain_id = str(payload.get("domain_id", "")).strip()
                message = str(payload.get("message", "")).strip()
                if not domain_id or not message:
                    await websocket.send_json(
                        {"type": "error", "error": "domain_id and message are required"}
                    )
                    continue

                events = chat_use_case.stream(
                    SendMessageRequest(
                        domain_id=domain_id,
                        message=message,
                        role=str(claims.get("role", "user")).lower()
                        if auth_mode == "jwt"
                        else "user",
                        subject=str(claims.get("sub", ""))
                        if auth_mode == "jwt"
                        else "",
                    )
                )
                done = None
                async for event in events:
                    if event.type == "delta":
                        await websocket.send_json(
                            {"type": "delta", "text": event.text or ""}
                        )
                        # await asyncio.sleep(0)  # No longer needed with native async iterator
                    if event.type == "done":
                        done = event
                if done is None or done.response is None:
                    await websocket.send_json(
                        {"type": "error", "error": "Stream terminated without response"}
                    )
                    continue

                await websocket.send_json(
                    {"type": "done", "message": asdict(done.response)}
                )

        except WebSocketDisconnect:
            return

    @app.websocket("/ws")
    async def multiplexer_socket(websocket: WebSocket) -> None:
        logger.info("WebSocket handler invoked")
        socket_key = None
        try:
            # Auth gate: default is JWT mode, but this handler is used by both modes.
            auth_mode = (os.getenv("AUTH_MODE", "jwt") or "jwt").lower()
            logger.debug(f"WebSocket auth_mode={auth_mode}")
            claims: dict[str, Any] = {}
            role = "user"
            subject = ""
            perms = permissions_for_role(role)

            if auth_mode == "jwt":
                jwt_config = JwtConfig(secret=os.getenv("AUTH_SECRET", "dev-secret"))
                # Try header first, then query param
                token = parse_bearer(websocket.headers.get("authorization"))
                if not token:
                    token = websocket.query_params.get("token")
                    logger.debug("Token from query params")
                else:
                    logger.debug("Token from Authorization header")

                if not token:
                    logger.warning("WebSocket no token provided")
                    await websocket.close(code=1008)
                    return
                try:
                    # We need to manually validate token here since we don't have Depends checks in WS
                    claims = get_claims_from_token(token, config=jwt_config)
                    subject = str(claims.get("sub", ""))
                    role = str(claims.get("role", "user")).lower()
                    perms = parse_permissions(claims.get("perms"))
                    logger.debug(f"WebSocket auth success: role={role}, subject={subject}")
                except PermissionError as exc:
                    logger.error(f"WebSocket auth token validation failed: {exc}")
                    await websocket.close(code=1008)
                    return
                except Exception as exc:
                    logger.error(f"WebSocket auth unexpected error: {exc}", exc_info=True)
                    await websocket.close(code=1008)
                    return

            logger.info("WebSocket accepting connection")
            await websocket.accept()
            logger.info("WebSocket connection accepted")

            socket_key = id(websocket)
            logger.info(f"WebSocket socket_key={socket_key}")
        except Exception as exc:
            logger.error(f"WebSocket setup failed: {exc}", exc_info=True)
            return
        send_lock = asyncio.Lock()

        async def ws_send(payload: dict[str, Any]) -> None:
            async with send_lock:
                await websocket.send_json(payload)

        socket_key = id(websocket)
        _SOCKET_SENDERS[socket_key] = ws_send

        async def broadcast(conversation_id: str, payload: dict[str, Any]) -> None:
            targets = list(_CONVERSATION_SOCKETS.get(conversation_id, set()))
            for target in targets:
                sender = _SOCKET_SENDERS.get(target)
                if sender is not None:
                    await sender(payload)

        async def ws_error(
            message: str, *, code: str = "error", conversation_id: str | None = None
        ) -> None:
            payload: dict[str, Any] = {
                "type": "error",
                "error": message,
                "payload": {"code": code, "message": message},
            }
            if conversation_id:
                payload["conversationId"] = conversation_id
            await ws_send(payload)

        try:
            while True:
                try:
                    payload: dict[str, Any] = await websocket.receive_json()
                except WebSocketDisconnect:
                    logger.info("WebSocket client disconnected normally")
                    return
                except Exception as exc:
                    logger.error(f"WebSocket receive JSON failed: {exc}", exc_info=True)
                    return  # Don't raise - just close gracefully
                event_type = str(payload.get("type", "")).strip()
                if event_type == "PING":
                    await ws_send({"type": "PONG"})
                    continue

                if event_type == "start_conversation":
                    try:
                        require_permission_set(perms, Permission.CHAT_SEND)
                    except PermissionError as exc:
                        await ws_error(str(exc), code="forbidden")
                        continue

                    domain_id = str(
                        (payload.get("payload") or {}).get("domainId", "")
                    ).strip()
                    if not domain_id:
                        await ws_error("domainId is required", code="bad_request")
                        continue

                    conversation_repo = getattr(
                        chat_use_case, "conversation_repo", None
                    )
                    if conversation_repo is None:
                        await ws_error(
                            "Conversation store not configured", code="not_configured"
                        )
                        continue

                    bundle = chat_use_case.loader.load_bundle()
                    domain = bundle.domains.get(domain_id)
                    if domain is None:
                        await ws_error("Unknown domainId", code="not_found")
                        continue
                    if role not in {r.lower() for r in domain.allowed_roles}:
                        await ws_error(
                            "Role not allowed for this domain", code="forbidden"
                        )
                        continue

                    conversation_id = str(uuid4())
                    from src.domain.entities.conversation import (
                        Conversation,  # local import to avoid cycles
                    )

                    conversation_repo.create_conversation(
                        Conversation(
                            id=conversation_id,
                            domain_id=domain_id,
                            created_by_role=role,
                            created_by_sub=subject,
                        )
                    )
                    _CONVERSATION_SOCKETS.setdefault(conversation_id, set()).add(
                        socket_key
                    )
                    await ws_send(
                        {
                            "type": "conversation_started",
                            "payload": {
                                "conversationId": conversation_id,
                                "domainId": domain_id,
                                "activeAgent": domain.default_agent,
                            },
                        }
                    )
                    continue

                if event_type == "send_message":
                    try:
                        require_permission_set(perms, Permission.CHAT_SEND)
                    except PermissionError as exc:
                        await ws_error(str(exc), code="forbidden")
                        continue

                    conversation_id = str(payload.get("conversationId", "")).strip()
                    content = str(
                        (payload.get("payload") or {}).get("content", "")
                    ).strip()
                    enable_thinking = bool(
                        (payload.get("payload") or {}).get("enableThinking", False)
                    )
                    if not conversation_id or not content:
                        await ws_error(
                            "conversationId and payload.content are required",
                            code="bad_request",
                        )
                        continue

                    conversation_repo = getattr(
                        chat_use_case, "conversation_repo", None
                    )
                    if conversation_repo is None:
                        await ws_error(
                            "Conversation store not configured",
                            code="not_configured",
                            conversation_id=conversation_id,
                        )
                        continue
                    convo = conversation_repo.get_conversation(conversation_id)
                    if convo is None:
                        await ws_error(
                            "Unknown conversationId",
                            code="not_found",
                            conversation_id=conversation_id,
                        )
                        continue
                    if (
                        role not in {"admin", "developer"}
                        and convo.created_by_sub
                        and convo.created_by_sub != subject
                    ):
                        await ws_error(
                            "Unknown conversationId",
                            code="not_found",
                            conversation_id=conversation_id,
                        )
                        continue

                    _CONVERSATION_SOCKETS.setdefault(conversation_id, set()).add(
                        socket_key
                    )

                    tool_cmd = _parse_tool_command(content)
                    if tool_cmd is not None:
                        if (
                            request_tool_run_uc is None
                            or approve_tool_run_uc is None
                            or reject_tool_run_uc is None
                            or execute_tool_run_uc is None
                        ):
                            await ws_error(
                                "Tool runs not configured",
                                code="not_configured",
                                conversation_id=conversation_id,
                            )
                            continue
                        tool_id, params = tool_cmd
                        try:
                            require_permission_set(perms, Permission.TOOL_REQUEST)
                        except PermissionError as exc:
                            await ws_error(
                                str(exc),
                                code="forbidden",
                                conversation_id=conversation_id,
                            )
                            continue

                        try:
                            created = request_tool_run_uc.execute(
                                RequestToolRunRequest(
                                    tool_id=tool_id,
                                    parameters=params,
                                    requested_by_role=role,
                                    requested_by_permissions=perms,
                                    requested_by_subject=subject,
                                    conversation_id=conversation_id,
                                )
                            )
                        except Exception as exc:  # noqa: BLE001
                            await ws_error(
                                str(exc),
                                code="tool_request_failed",
                                conversation_id=conversation_id,
                            )
                            continue

                        bundle = chat_use_case.loader.load_bundle()
                        tool = bundle.tools.get(tool_id)
                        request_id = created.run_id
                        if tool is None:
                            await ws_error(
                                "Unknown tool",
                                code="not_found",
                                conversation_id=conversation_id,
                            )
                            continue

                        if tool.requires_approval:
                            await broadcast(
                                conversation_id,
                                {
                                    "type": "tool_approval_required",
                                    "conversationId": conversation_id,
                                    "payload": {
                                        "requestId": request_id,
                                        "toolName": tool.name,
                                        "toolArgs": params,
                                        "description": tool.description,
                                        "agentName": tool.domain or "system",
                                    },
                                },
                            )
                            continue

                        # Auto-execute non-approvable tools with developer perms (MVP).
                        try:
                            exec_resp = execute_tool_run_uc.execute(
                                ExecuteToolRunRequest(
                                    run_id=request_id,
                                    executed_by_role="developer",
                                    executed_by_permissions=permissions_for_role(
                                        "developer"
                                    ),
                                )
                            )
                            await broadcast(
                                conversation_id,
                                {
                                    "type": "tool_executed",
                                    "conversationId": conversation_id,
                                    "payload": {
                                        "requestId": request_id,
                                        "toolName": tool.name,
                                        "result": exec_resp.result,
                                        "success": True,
                                    },
                                },
                            )
                            await broadcast(
                                conversation_id,
                                {
                                    "type": "message_complete",
                                    "conversationId": conversation_id,
                                    "payload": {
                                        "messageId": str(uuid4()),
                                        "content": json.dumps(
                                            exec_resp.result, ensure_ascii=False
                                        ),
                                        "agentName": tool.domain or "system",
                                        "metadata": {"tokenCount": 0, "durationMs": 0},
                                    },
                                },
                            )
                        except Exception as exc:  # noqa: BLE001
                            await ws_error(
                                str(exc),
                                code="tool_execute_failed",
                                conversation_id=conversation_id,
                            )
                        continue

                    task_key = f"{id(websocket)}:{conversation_id}"
                    existing = _STREAM_TASKS.pop(task_key, None)
                    if existing is not None:
                        existing.cancel()

                    message_id = str(uuid4())
                    convo_local = convo
                    content_local = content
                    conversation_id_local = conversation_id
                    task_key_local = task_key
                    message_id_local = message_id

                    async def run_stream(
                        *,
                        convo=convo_local,
                        content=content_local,
                        conversation_id=conversation_id_local,
                        task_key=task_key_local,
                        message_id=message_id_local,
                        enable_thinking=enable_thinking,
                    ) -> None:
                        started_at = asyncio.get_event_loop().time()
                        chunks: list[str] = []
                        agent_name = ""
                        try:
                            async for event in chat_use_case.stream(
                                SendMessageRequest(
                                    domain_id=convo.domain_id,
                                    message=content,
                                    role=role,
                                    conversation_id=conversation_id,
                                    subject=subject,
                                    enable_thinking=enable_thinking,
                                )
                            ):
                                if event.type == "agent_selected" and event.agent_id:
                                    bundle = chat_use_case.loader.load_bundle()
                                    agent = bundle.agents.get(event.agent_id)
                                    new_agent_name = agent.name if agent else event.agent_id
                                    
                                    # Detect handoff (agent change)
                                    if agent_name and agent_name != new_agent_name:
                                        await ws_send({
                                            "type": "workflow_handoff",
                                            "conversationId": conversation_id,
                                            "payload": {
                                                "fromAgent": agent_name,
                                                "toAgent": new_agent_name,
                                                "fromAgentId": getattr(event, 'previous_agent_id', agent_name),
                                                "toAgentId": event.agent_id,
                                                "reason": "Agent handoff detected",
                                                "timestamp": asyncio.get_event_loop().time(),
                                            },
                                        })
                                    
                                    agent_name = new_agent_name
                                    # Forward event to client
                                    await ws_send({
                                        "type": "agent_selected",
                                        "conversationId": conversation_id,
                                        "agent_id": event.agent_id,
                                        "agent_name": agent_name
                                    })
                                    # Emit workflow visualization event
                                    await ws_send({
                                        "type": "workflow_step_start",
                                        "conversationId": conversation_id,
                                        "payload": {
                                            "agentId": event.agent_id,
                                            "agentName": agent_name,
                                            "timestamp": asyncio.get_event_loop().time(),
                                        },
                                    })
                                if event.type == "tool_start":
                                    # Ensure agent_name is up to date
                                    if event.agent_id:
                                         if not agent_name:
                                             bundle = chat_use_case.loader.load_bundle()
                                             agent = bundle.agents.get(event.agent_id)
                                             agent_name = agent.name if agent else event.agent_id
                                    
                                    await ws_send({
                                        "type": "workflow_step_start",
                                        "conversationId": conversation_id,
                                        "payload": {
                                            "agentId": event.agent_id or "router",
                                            "agentName": agent_name or "System",
                                            "timestamp": asyncio.get_event_loop().time(),
                                            "content": event.text, # "Executing [Tool]"
                                            "metadata": event.metadata or {} # Includes skill_id
                                        },
                                    })
                                if event.type == "thought":
                                    # Ensure agent_name is up to date
                                    current_agent_name = "Router"
                                    if event.agent_id and event.agent_id != "router":
                                         if not agent_name or agent_name == "Router":
                                             bundle = chat_use_case.loader.load_bundle()
                                             agent = bundle.agents.get(event.agent_id)
                                             current_agent_name = agent.name if agent else event.agent_id
                                         else:
                                             current_agent_name = agent_name
                                    
                                    await ws_send({
                                        "type": "workflow_thought",
                                        "conversationId": conversation_id,
                                        "payload": {
                                            "agentId": event.agent_id or "router",
                                            "agentName": current_agent_name,
                                            "conversationId": conversation_id,
                                            "reason": event.text or "Thinking..."
                                        }
                                    })
                                if event.type == "delta":
                                    chunk = event.text or ""
                                    chunks.append(chunk)
                                    await ws_send(
                                        {
                                            "type": "message_chunk",
                                            "conversationId": conversation_id,
                                            "payload": {
                                                "messageId": message_id,
                                                "chunk": chunk,
                                                "agentName": agent_name,
                                            },
                                        }
                                    )
                                if event.type == "done" and event.response is not None:
                                    final_agent = event.response.agent_id
                                    bundle = chat_use_case.loader.load_bundle()
                                    agent = bundle.agents.get(final_agent)
                                    agent_name_final = (
                                        agent.name if agent else final_agent
                                    )
                                    content_text = event.response.reply
                                    duration_ms = int(
                                        (asyncio.get_event_loop().time() - started_at)
                                        * 1000
                                    )
                                    await ws_send(
                                        {
                                            "type": "message_complete",
                                            "conversationId": conversation_id,
                                            "payload": {
                                                "messageId": message_id,
                                                "content": content_text,
                                                "agentName": agent_name_final,
                                                "agentId": final_agent,  # Add agent_id for frontend
                                                "metadata": {
                                                    "tokenCount": len(chunks),
                                                    "durationMs": duration_ms,
                                                },
                                            },
                                        }
                                    )
                                    # Emit workflow step complete for visualization
                                    await ws_send({
                                        "type": "workflow_step_complete",
                                        "conversationId": conversation_id,
                                        "payload": {
                                            "agentId": final_agent,
                                            "agentName": agent_name_final,
                                            "durationMs": duration_ms,
                                            "tokenCount": len(chunks),
                                        },
                                    })
                                    return
                        except asyncio.CancelledError:
                            await ws_error(
                                "Stream cancelled",
                                code="cancelled",
                                conversation_id=conversation_id,
                            )
                            raise
                        except Exception as exc:  # noqa: BLE001
                            await ws_error(
                                str(exc),
                                code="stream_error",
                                conversation_id=conversation_id,
                            )
                        finally:
                            _STREAM_TASKS.pop(task_key, None)

                    _STREAM_TASKS[task_key] = asyncio.create_task(run_stream())
                    continue

                if event_type == "cancel_stream":
                    conversation_id = str(payload.get("conversationId", "")).strip()
                    task_key = f"{id(websocket)}:{conversation_id}"
                    task = _STREAM_TASKS.pop(task_key, None)
                    if task is not None:
                        task.cancel()
                        await ws_error(
                            "Stream cancelled",
                            code="cancelled",
                            conversation_id=conversation_id or None,
                        )
                    else:
                        await ws_error(
                            "No active stream",
                            code="not_found",
                            conversation_id=conversation_id or None,
                        )
                    continue

                if event_type == "approve_tool":
                    if (
                        approve_tool_run_uc is None
                        or reject_tool_run_uc is None
                        or execute_tool_run_uc is None
                    ):
                        await ws_error(
                            "Tool runs not configured", code="not_configured"
                        )
                        continue

                    conversation_id = str(payload.get("conversationId", "")).strip()
                    request_id = str(payload.get("requestId", "")).strip()
                    approved = bool(
                        (payload.get("payload") or {}).get("approved", False)
                    )
                    reason = str(
                        (payload.get("payload") or {}).get("reason", "")
                    ).strip()

                    tool_run = approve_tool_run_uc.repo.get(request_id)
                    if tool_run is None:
                        await ws_error(
                            "Unknown requestId",
                            code="not_found",
                            conversation_id=conversation_id or None,
                        )
                        continue
                    if (
                        tool_run.conversation_id
                        and tool_run.conversation_id != conversation_id
                    ):
                        await ws_error(
                            "Unknown requestId",
                            code="not_found",
                            conversation_id=conversation_id or None,
                        )
                        continue

                    bundle = chat_use_case.loader.load_bundle()
                    tool = bundle.tools.get(tool_run.tool_id)
                    tool_name = tool.name if tool else tool_run.tool_id

                    if approved:
                        try:
                            require_permission_set(perms, Permission.TOOL_APPROVE)
                        except PermissionError as exc:
                            await ws_error(
                                str(exc),
                                code="forbidden",
                                conversation_id=conversation_id,
                            )
                            continue
                        try:
                            approve_tool_run_uc.execute(
                                ApproveToolRunRequest(
                                    run_id=request_id,
                                    approved_by_role=role,
                                    approved_by_permissions=perms,
                                )
                            )
                            exec_resp = execute_tool_run_uc.execute(
                                ExecuteToolRunRequest(
                                    run_id=request_id,
                                    executed_by_role=role,
                                    executed_by_permissions=perms,
                                )
                            )
                            await broadcast(
                                conversation_id,
                                {
                                    "type": "tool_executed",
                                    "conversationId": conversation_id,
                                    "payload": {
                                        "requestId": request_id,
                                        "toolName": tool_name,
                                        "result": exec_resp.result,
                                        "success": True,
                                    },
                                },
                            )
                            await broadcast(
                                conversation_id,
                                {
                                    "type": "message_complete",
                                    "conversationId": conversation_id,
                                    "payload": {
                                        "messageId": str(uuid4()),
                                        "content": json.dumps(
                                            exec_resp.result, ensure_ascii=False
                                        ),
                                        "agentName": tool.domain if tool else "system",
                                        "metadata": {"tokenCount": 0, "durationMs": 0},
                                    },
                                },
                            )
                        except Exception as exc:  # noqa: BLE001
                            await ws_error(
                                str(exc),
                                code="tool_execute_failed",
                                conversation_id=conversation_id,
                            )
                        continue

                    # rejected
                    try:
                        require_permission_set(perms, Permission.TOOL_REJECT)
                    except PermissionError as exc:
                        await ws_error(
                            str(exc), code="forbidden", conversation_id=conversation_id
                        )
                        continue
                    try:
                        reject_tool_run_uc.execute(
                            RejectToolRunRequest(
                                run_id=request_id,
                                rejected_by_role=role,
                                rejected_by_permissions=perms,
                                reason=reason or "rejected",
                            )
                        )
                        await broadcast(
                            conversation_id,
                            {
                                "type": "tool_executed",
                                "conversationId": conversation_id,
                                "payload": {
                                    "requestId": request_id,
                                    "toolName": tool_name,
                                    "result": None,
                                    "success": False,
                                    "errorMessage": reason or "rejected",
                                },
                            },
                        )
                        await ws_error(
                            "Tool rejected",
                            code="rejected",
                            conversation_id=conversation_id,
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_error(
                            str(exc),
                            code="tool_reject_failed",
                            conversation_id=conversation_id,
                        )
                    continue

                if event_type == "tool_run.request":
                    if request_tool_run_uc is None:
                        await ws_send(
                            {"type": "error", "error": "Tool runs not configured"}
                        )
                        continue
                    try:
                        require_permission_set(perms, Permission.TOOL_REQUEST)
                    except PermissionError as exc:
                        await ws_send({"type": "error", "error": str(exc)})
                        continue
                    tool_id = str(payload.get("tool_id", "")).strip()
                    parameters = payload.get("parameters", {}) or {}
                    try:
                        created = request_tool_run_uc.execute(
                            RequestToolRunRequest(
                                tool_id=tool_id,
                                parameters=dict(parameters),
                                requested_by_role=role,
                                requested_by_permissions=perms,
                                requested_by_subject=subject,
                            )
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                        continue

                    tool_run = request_tool_run_uc.repo.get(created.run_id)
                    await ws_send(
                        {
                            "type": "tool_run.created",
                            "run": tool_run.to_dict()
                            if tool_run
                            else {"id": created.run_id},
                        }
                    )
                    continue

                if event_type == "tool_run.approve":
                    if approve_tool_run_uc is None:
                        await ws_send(
                            {"type": "error", "error": "Tool runs not configured"}
                        )
                        continue
                    try:
                        require_permission_set(perms, Permission.TOOL_APPROVE)
                    except PermissionError as exc:
                        await ws_send({"type": "error", "error": str(exc)})
                        continue
                    run_id = str(payload.get("run_id", "")).strip()
                    try:
                        approve_tool_run_uc.execute(
                            ApproveToolRunRequest(
                                run_id=run_id,
                                approved_by_role=role,
                                approved_by_permissions=perms,
                            )
                        )
                        tool_run = approve_tool_run_uc.repo.get(run_id)
                        await ws_send(
                            {
                                "type": "tool_run.approved",
                                "run": tool_run.to_dict()
                                if tool_run
                                else {"id": run_id},
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                    continue

                if event_type == "tool_run.reject":
                    if reject_tool_run_uc is None:
                        await ws_send(
                            {"type": "error", "error": "Tool runs not configured"}
                        )
                        continue
                    try:
                        require_permission_set(perms, Permission.TOOL_REJECT)
                    except PermissionError as exc:
                        await ws_send({"type": "error", "error": str(exc)})
                        continue
                    run_id = str(payload.get("run_id", "")).strip()
                    reason = str(payload.get("reason", "")).strip()
                    try:
                        reject_tool_run_uc.execute(
                            RejectToolRunRequest(
                                run_id=run_id,
                                rejected_by_role=role,
                                rejected_by_permissions=perms,
                                reason=reason,
                            )
                        )
                        tool_run = reject_tool_run_uc.repo.get(run_id)
                        await ws_send(
                            {
                                "type": "tool_run.rejected",
                                "run": tool_run.to_dict()
                                if tool_run
                                else {"id": run_id},
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                    continue

                if event_type == "tool_run.execute":
                    if execute_tool_run_uc is None:
                        await ws_send(
                            {"type": "error", "error": "Tool runs not configured"}
                        )
                        continue
                    try:
                        require_permission_set(perms, Permission.TOOL_EXECUTE)
                    except PermissionError as exc:
                        await ws_send({"type": "error", "error": str(exc)})
                        continue
                    run_id = str(payload.get("run_id", "")).strip()
                    try:
                        execute_tool_run_uc.execute(
                            ExecuteToolRunRequest(
                                run_id=run_id,
                                executed_by_role=role,
                                executed_by_permissions=perms,
                            )
                        )
                        tool_run = execute_tool_run_uc.repo.get(run_id)
                        await ws_send(
                            {
                                "type": "tool_run.executed",
                                "run": tool_run.to_dict()
                                if tool_run
                                else {"id": run_id},
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                    continue

                if event_type == "tool_run.list":
                    if list_tool_runs_uc is None:
                        await ws_send(
                            {"type": "error", "error": "Tool runs not configured"}
                        )
                        continue
                    try:
                        require_permission_set(perms, Permission.TOOL_READ)
                    except PermissionError as exc:
                        await ws_send({"type": "error", "error": str(exc)})
                        continue
                    limit = int(payload.get("limit", 50))
                    status = payload.get("status")
                    tool_id = payload.get("tool_id")
                    cursor = payload.get("cursor")
                    if cursor is not None and not _CURSOR_PATTERN.match(
                        str(cursor).strip()
                    ):
                        await ws_send(
                            {"type": "error", "error": "Invalid cursor format"}
                        )
                        continue
                    try:
                        result = list_tool_runs_uc.execute(
                            ListToolRunsRequest(
                                limit=limit,
                                status=str(status) if status is not None else None,
                                tool_id=str(tool_id) if tool_id is not None else None,
                                requested_by_sub=None
                                if role in {"admin", "developer"}
                                else subject,
                                cursor=str(cursor) if cursor is not None else None,
                            )
                        )
                        await ws_send(
                            {
                                "type": "tool_run.listed",
                                "runs": [run.to_dict() for run in result.runs],
                                "next_cursor": result.next_cursor,
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                    continue

                if event_type == "chat.send":
                    domain_id = str(payload.get("domain_id", "")).strip()
                    message = str(payload.get("message", "")).strip()
                    conversation_id = payload.get("conversation_id")
                    if not domain_id or not message:
                        await ws_send(
                            {
                                "type": "error",
                                "error": "domain_id and message are required",
                            }
                        )
                        continue
                    try:
                        require_permission_set(perms, Permission.CHAT_SEND)
                    except PermissionError as exc:
                        await ws_send({"type": "error", "error": str(exc)})
                        continue
                    try:
                        events = chat_use_case.stream(
                            SendMessageRequest(
                                domain_id=domain_id,
                                message=message,
                                role=role,
                                conversation_id=str(conversation_id)
                                if conversation_id
                                else None,
                                subject=str(claims.get("sub", ""))
                                if auth_mode == "jwt"
                                else "",
                            )
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                        continue

                    done = None
                    for event in events:
                        if event.type == "delta":
                            await ws_send(
                                {"type": "chat.delta", "text": event.text or ""}
                            )
                            await asyncio.sleep(0)
                        if event.type == "done":
                            done = event
                    if done is None or done.response is None:
                        await ws_send(
                            {
                                "type": "error",
                                "error": "Stream terminated without response",
                            }
                        )
                        continue

                    await ws_send(
                        {"type": "chat.done", "message": asdict(done.response)}
                    )
                    continue

                if event_type == "conversation.list":
                    try:
                        require_permission_set(perms, Permission.CHAT_READ)
                    except PermissionError as exc:
                        await websocket.send_json({"type": "error", "error": str(exc)})
                        continue

                    # chat_use_case may have a conversation repo; if not, we cannot list.
                    conversation_repo = getattr(
                        chat_use_case, "conversation_repo", None
                    )
                    if conversation_repo is None:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "Conversation store not configured",
                            }
                        )
                        continue

                    limit = int(payload.get("limit", 50))
                    cursor = payload.get("cursor")
                    domain_id = payload.get("domain_id")
                    if cursor is not None and not _CURSOR_PATTERN.match(
                        str(cursor).strip()
                    ):
                        await ws_send(
                            {"type": "error", "error": "Invalid cursor format"}
                        )
                        continue
                    try:
                        fetched = conversation_repo.list_conversations(
                            limit=limit + 1,
                            cursor=str(cursor) if cursor is not None else None,
                            domain_id=str(domain_id) if domain_id is not None else None,
                            created_by_sub=None
                            if role in {"admin", "developer"}
                            else subject,
                        )
                        has_more = len(fetched) > limit
                        conversations = fetched[:limit]
                        next_cursor = conversation_repo.get_next_cursor(
                            conversations, has_more=has_more
                        )
                        await ws_send(
                            {
                                "type": "conversation.listed",
                                "conversations": [c.to_dict() for c in conversations],
                                "next_cursor": next_cursor,
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                    continue

                if event_type == "conversation.messages":
                    try:
                        require_permission_set(perms, Permission.CHAT_READ)
                    except PermissionError as exc:
                        await websocket.send_json({"type": "error", "error": str(exc)})
                        continue

                    conversation_repo = getattr(
                        chat_use_case, "conversation_repo", None
                    )
                    if conversation_repo is None:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "error": "Conversation store not configured",
                            }
                        )
                        continue

                    conversation_id = str(payload.get("conversation_id", "")).strip()
                    limit = int(payload.get("limit", 200))
                    if not conversation_id:
                        await ws_send(
                            {"type": "error", "error": "conversation_id is required"}
                        )
                        continue
                    try:
                        convo = conversation_repo.get_conversation(conversation_id)
                        if convo is None:
                            await ws_send(
                                {"type": "error", "error": "Unknown conversation_id"}
                            )
                            continue
                        if (
                            role not in {"admin", "developer"}
                            and convo.created_by_sub
                            and convo.created_by_sub != subject
                        ):
                            await ws_send(
                                {"type": "error", "error": "Unknown conversation_id"}
                            )
                            continue
                        messages = conversation_repo.list_messages(
                            conversation_id, limit=limit
                        )
                        await ws_send(
                            {
                                "type": "conversation.messages",
                                "conversation_id": conversation_id,
                                "messages": [m.to_dict() for m in messages],
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        await ws_send({"type": "error", "error": str(exc)})
                    continue

                await ws_send(
                    {"type": "error", "error": f"Unknown event type: {event_type}"}
                )

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            # Cancel any in-flight streams for this connection.
            prefix = f"{id(websocket)}:"
            for key, task in list(_STREAM_TASKS.items()):
                if key.startswith(prefix):
                    _STREAM_TASKS.pop(key, None)
                    task.cancel()
            # Remove from conversation socket registries
            for convo_id, sockets in list(_CONVERSATION_SOCKETS.items()):
                sockets.discard(socket_key)
                if not sockets:
                    _CONVERSATION_SOCKETS.pop(convo_id, None)
            _SOCKET_SENDERS.pop(socket_key, None)
            return
        except Exception as exc:
            logger.error(f"WebSocket handler exception: {exc}", exc_info=True)
            _SOCKET_SENDERS.pop(socket_key, None)
            return
