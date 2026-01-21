"""Health Monitor System with FastAPI.

Implements agent health checks following Microsoft's operational resilience guidelines.
Monitors agent status, connection health, and system metrics.
"""

import time
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

# Auth integration
from auth_middleware import (
    AuthMiddleware,
    get_current_user,
    get_admin_user,
    get_monitor_user,
    create_user,
    authenticate_user,
    create_access_token,
)


@dataclass
class AgentHealth:
    """Health status information for an agent."""

    name: str
    status: str  # healthy, degraded, unhealthy, unknown
    last_check: str
    response_time_ms: float
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HealthConfig(BaseModel):
    """Configuration for health monitoring system."""

    check_interval_seconds: int = Field(default=30, ge=5, le=300)
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    unhealthy_threshold: int = Field(default=3, ge=1, le=10)
    response_time_threshold_ms: float = Field(default=5000.0, ge=100.0, le=30000.0)
    enable_auto_recovery: bool = True


class HealthMonitor:
    """Health monitoring system for multi-agent architecture.

    Tracks agent health, performs periodic health checks, and provides
    REST API endpoints for system monitoring.
    """

    def __init__(self, config: Optional[HealthConfig] = None):
        self.config = config or HealthConfig()
        self._agents: Dict[str, AgentHealth] = {}
        self._check_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._app: Optional[FastAPI] = None
        self._system_start_time = time.time()

    def register_agent(
        self,
        name: str,
        check_function: callable,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an agent for health monitoring.

        Parameters
        ----------
        name : str
            Name of the agent.
        check_function : callable
            Async function that returns True if agent is healthy.
        metadata : Optional[Dict[str, Any]]
            Additional metadata about the agent.
        """
        self._agents[name] = AgentHealth(
            name=name,
            status="unknown",
            last_check=datetime.utcnow().isoformat(),
            response_time_ms=0.0,
            metadata=metadata or {},
        )
        self._agents[name].check_function = check_function

    async def check_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Perform health check on a single agent.

        Parameters
        ----------
        agent_name : str
            Name of the agent to check.

        Returns
        -------
        Dict[str, Any]
            Health check result.
        """
        if agent_name not in self._agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        agent = self._agents[agent_name]
        start_time = time.time()

        try:
            is_healthy = await agent.check_function()
            response_time = (time.time() - start_time) * 1000

            if is_healthy and response_time < self.config.response_time_threshold_ms:
                agent.status = "healthy"
                agent.error_count = 0
                agent.last_error = None
            elif is_healthy:
                agent.status = "degraded"
                agent.error_count = 0
            else:
                agent.status = "unhealthy"
                agent.error_count += 1

            agent.last_check = datetime.utcnow().isoformat()
            agent.response_time_ms = round(response_time, 2)

            return asdict(agent)
        except Exception as e:
            agent.status = "unhealthy"
            agent.error_count += 1
            agent.last_error = str(e)
            agent.last_check = datetime.utcnow().isoformat()

            return asdict(agent)

    async def check_all_agents(self) -> Dict[str, Any]:
        """Perform health checks on all registered agents.

        Returns
        -------
        Dict[str, Any]
            Overall system health status.
        """
        results = {}
        overall_status = "healthy"
        unhealthy_count = 0

        for agent_name in self._agents:
            results[agent_name] = await self.check_agent_health(agent_name)
            if results[agent_name]["status"] == "unhealthy":
                unhealthy_count += 1
                overall_status = (
                    "degraded" if unhealthy_count < len(self._agents) else "unhealthy"
                )
            elif (
                results[agent_name]["status"] == "degraded"
                and overall_status == "healthy"
            ):
                overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - self._system_start_time,
            "agents": results,
        }

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get current status of a specific agent without performing check.

        Parameters
        ----------
        agent_name : str
            Name of the agent.

        Returns
        -------
        Dict[str, Any]
            Agent health status.
        """
        if agent_name not in self._agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

        return asdict(self._agents[agent_name])

    def get_all_statuses(self) -> Dict[str, Any]:
        """Get current status of all agents without performing checks.

        Returns
        -------
        Dict[str, Any]
            All agent health statuses.
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - self._system_start_time,
            "agents": {name: asdict(agent) for name, agent in self._agents.items()},
        }

    async def _periodic_health_checks(self):
        """Background task for periodic health checks."""
        while self._is_running:
            try:
                await self.check_all_agents()
            except Exception as e:
                print(f"Health check error: {e}")

            await asyncio.sleep(self.config.check_interval_seconds)

    def start_monitoring(self):
        """Start background health monitoring."""
        if not self._is_running:
            self._is_running = True
            self._check_task = asyncio.create_task(self._periodic_health_checks())

    def stop_monitoring(self):
        """Stop background health monitoring."""
        self._is_running = False
        if self._check_task:
            self._check_task.cancel()

    def create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application with health check endpoints.

        Returns
        -------
        FastAPI
            Configured FastAPI application.
        """
        app = FastAPI(
            title="Agent Health Monitor",
            description="Health monitoring for multi-agent system with authentication",
            version="1.0.0",
        )

        # Add authentication middleware
        auth_middleware = AuthMiddleware()
        app.middleware("http")(auth_middleware)

        # Authentication endpoints (public)
        @app.post("/auth/login")
        async def login(username: str, password: str):
            """Login and get access token."""
            try:
                user = authenticate_user(username, password)
                token = create_access_token(user)
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role.value,
                    },
                }
            except Exception as e:
                raise HTTPException(status_code=401, detail=str(e))

        @app.post("/auth/register")
        async def register(
            username: str, email: str, full_name: str, password: str, role: str = "user"
        ):
            """Register new user (admin only in production)."""
            try:
                user = create_user(username, email, full_name, password, role)
                return {
                    "message": "User created successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role.value,
                    },
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/")
        async def root():
            return {"message": "Agent Health Monitor API", "status": "running"}

        @app.get("/health")
        async def system_health(user=Depends(get_monitor_user)):
            """Get system health status (requires monitor permission)."""
            return await self.check_all_agents()

        @app.get("/health/agents/{agent_name}")
        async def agent_health(agent_name: str, user=Depends(get_monitor_user)):
            """Get specific agent health (requires monitor permission)."""
            return await self.check_agent_health(agent_name)

        @app.get("/status/agents/{agent_name}")
        async def agent_status(agent_name: str, user=Depends(get_monitor_user)):
            """Get agent status (requires monitor permission)."""
            return self.get_agent_status(agent_name)

        @app.get("/status/all")
        async def all_status(user=Depends(get_monitor_user)):
            """Get all agent statuses (requires monitor permission)."""
            return self.get_all_statuses()

        @app.post("/health/refresh")
        async def refresh_health(user=Depends(get_monitor_user)):
            """Refresh health checks (requires monitor permission)."""
            return await self.check_all_agents()

        @app.get("/metrics")
        async def metrics(user=Depends(get_monitor_user)):
            """Get health metrics (requires monitor permission)."""
            return {
                "total_agents": len(self._agents),
                "healthy_agents": sum(
                    1 for a in self._agents.values() if a.status == "healthy"
                ),
                "degraded_agents": sum(
                    1 for a in self._agents.values() if a.status == "degraded"
                ),
                "unhealthy_agents": sum(
                    1 for a in self._agents.values() if a.status == "unhealthy"
                ),
                "uptime_seconds": time.time() - self._system_start_time,
            }

        # User management endpoints (admin only)
        @app.get("/users")
        async def list_users(user=Depends(get_admin_user)):
            """List all users (admin only)."""
            from auth_system import get_auth_manager

            auth_manager = get_auth_manager()
            return {"users": auth_manager.list_users()}

        @app.get("/users/{user_id}")
        async def get_user_details(user_id: str, user=Depends(get_admin_user)):
            """Get user details (admin only)."""
            from auth_system import get_auth_manager

            auth_manager = get_auth_manager()
            user_obj = auth_manager.get_user(user_id)
            if not user_obj:
                raise HTTPException(status_code=404, detail="User not found")
            return user_obj.to_dict()

        @app.put("/users/{user_id}")
        async def update_user(
            user_id: str, updates: dict, user=Depends(get_admin_user)
        ):
            """Update user (admin only)."""
            from auth_system import get_auth_manager

            auth_manager = get_auth_manager()
            try:
                updated_user = auth_manager.update_user(user_id, **updates)
                return {"message": "User updated", "user": updated_user.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.delete("/users/{user_id}")
        async def delete_user(user_id: str, user=Depends(get_admin_user)):
            """Delete user (admin only)."""
            from auth_system import get_auth_manager

            auth_manager = get_auth_manager()
            auth_manager.delete_user(user_id)
            return {"message": "User deleted"}

        @app.get("/roles")
        async def get_roles(user=Depends(get_current_user)):
            """Get all roles and permissions."""
            from auth_system import get_rbac_manager

            rbac_manager = get_rbac_manager()
            return {"roles": rbac_manager.get_all_roles()}

        self._app = app
        return app


# Singleton instance
_monitor: Optional[HealthMonitor] = None


def get_health_monitor(config: Optional[HealthConfig] = None) -> HealthMonitor:
    """Get or create singleton health monitor instance.

    Parameters
    ----------
    config : Optional[HealthConfig]
        Configuration for health monitor.

    Returns
    -------
    HealthMonitor
        The health monitor instance.
    """
    global _monitor
    if _monitor is None:
        _monitor = HealthMonitor(config)
    return _monitor


if __name__ == "__main__":
    import uvicorn

    monitor = HealthMonitor()

    async def mock_planner_check():
        await asyncio.sleep(0.1)
        return True

    async def mock_coder_check():
        await asyncio.sleep(0.2)
        return True

    monitor.register_agent(
        "planner", mock_planner_check, {"type": "planning", "model": "gpt-4"}
    )
    monitor.register_agent(
        "coder", mock_coder_check, {"type": "coding", "model": "gpt-4"}
    )

    app = monitor.create_fastapi_app()
    monitor.start_monitoring()

    uvicorn.run(app, host="0.0.0.0", port=8001)
