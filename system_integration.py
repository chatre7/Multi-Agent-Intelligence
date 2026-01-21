"""Integration module for multi-agent system components.

Coordinates all architectural components following Microsoft's multi-agent patterns.
"""

import asyncio
from typing import Optional, Dict, Any, List

from intent_classifier import IntentClassifierConfig, get_classifier
from health_monitor import HealthConfig, get_health_monitor
from metrics import get_metrics
from token_tracker import get_token_tracker
from mcp_server import get_mcp_server
from mcp_client import get_mcp_client
from agent_versioning import get_version_manager, TransitionAction
from auth_system import get_auth_manager, get_rbac_manager, UserRole

# Import planner_agent_team_v3 to register MCP tools


class MultiAgentSystem:
    """Main integration class for multi-agent system.

    Orchestrates:
    - Intent classification
    - Health monitoring
    - Metrics collection
    - Token tracking
    - MCP (Model Context Protocol) tool management
    - Agent versioning and lifecycle management
    """

    def __init__(
        self,
        classifier_config: Optional[IntentClassifierConfig] = None,
        health_config: Optional[HealthConfig] = None,
    ):
        self.classifier = get_classifier(classifier_config)
        self.health_monitor = get_health_monitor(health_config)
        self.metrics = get_metrics()
        self.token_tracker = get_token_tracker(daily_cost_limit=10.0)
        self.mcp_server = get_mcp_server()
        self.mcp_client = get_mcp_client()
        self.version_manager = get_version_manager()
        self.auth_manager = get_auth_manager()
        self.rbac_manager = get_rbac_manager()

        print("  ✓ Agent Version Manager ready")
        print("  ✓ Authentication & RBAC ready")

        self._agents: Dict[str, Any] = {}
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize all system components."""
        if self._is_initialized:
            return

        print("🚀 Initializing Multi-Agent System...")

        print("  ✓ Intent Classifier ready")
        print("  ✓ Health Monitor ready")
        print("  ✓ Metrics System ready")
        print("  ✓ Token Tracker ready")
        print("  ✓ MCP Server ready")
        print("  ✓ MCP Client ready")

        self._is_initialized = True
        print("\n✅ System initialized successfully!")

    def register_agent(
        self,
        name: str,
        agent_instance: Any,
        check_function: Optional[callable] = None,
        capabilities: Optional[str] = None,
    ) -> None:
        """Register an agent with all system components.

        Parameters
        ----------
        name : str
            Name of the agent.
        agent_instance : Any
            The agent instance.
        check_function : Optional[callable]
            Async health check function.
        capabilities : Optional[str]
            Description of agent capabilities.
        """
        self._agents[name] = agent_instance

        if check_function:
            self.health_monitor.register_agent(name, check_function, {"type": "agent"})

        if capabilities:
            self.classifier.update_capabilities(name, capabilities)

        self.metrics.set_queue_size(name, 0)

        print(f"  ✓ Agent '{name}' registered")

    def classify_and_route(
        self, user_input: str, conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Classify user intent and determine routing.

        Parameters
        ----------
        user_input : str
            User's input message.
        conversation_history : Optional[List[str]]
            Optional conversation context.

        Returns
        -------
        Dict[str, Any]
            Classification result with routing information.
        """
        intent_result = self.classifier.classify(user_input, conversation_history)

        with self.metrics.track_agent_latency(
            "intent_classifier", self.classifier.config.model_name
        ):
            self.metrics.record_agent_call("intent_classifier", "success")

        return {
            "user_input": user_input,
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "reasoning": intent_result["reasoning"],
            "target_agent": self.classifier.get_agent_for_intent(
                user_input, conversation_history
            ),
            "timestamp": self.metrics.get_token_usage_history(limit=1)[0]["timestamp"]
            if self.metrics.get_token_usage_history(limit=1)
            else None,
        }

    async def check_system_health(self) -> Dict[str, Any]:
        """Perform full system health check.

        Returns
        -------
        Dict[str, Any]
            Comprehensive health status.
        """
        return await self.health_monitor.check_all_agents()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns
        -------
        Dict[str, Any]
            System metrics overview.
        """
        return {
            "token_usage": self.token_tracker.get_session_summary(),
            "daily_tokens": self.token_tracker.get_daily_tokens(),
            "daily_cost": self.token_tracker.get_daily_cost(),
            "metrics": {
                "total_agents": len(self._agents),
                "token_history": self.metrics.get_token_usage_history(limit=10),
            },
        }

    async def start_health_monitoring(self) -> None:
        """Start background health monitoring."""
        self.health_monitor.start_monitoring()
        print("  ✓ Health monitoring started")

    def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        self.health_monitor.stop_monitoring()
        print("  ✓ Health monitoring stopped")

    def create_health_api(self):
        """Create FastAPI application for health endpoints.

        Returns
        -------
        FastAPI
            Health monitoring API.
        """
        return self.health_monitor.create_fastapi_app()

    def create_system_api(self):
        """Create FastAPI application for full system endpoints (health + MCP).

        Returns
        -------
        FastAPI
            Full system API with health and MCP endpoints.
        """
        from fastapi import HTTPException

        # Start with health monitor app
        app = self.health_monitor.create_fastapi_app()

        # Add MCP endpoints
        @app.get("/mcp/tools")
        async def list_mcp_tools():
            """List all MCP tools."""
            return {"tools": self.get_mcp_tools()}

        @app.get("/mcp/tools/{tool_name}")
        async def get_mcp_tool(tool_name: str):
            """Get MCP tool information."""
            tool_info = self.mcp_client.get_tool_info(tool_name)
            if not tool_info:
                raise HTTPException(
                    status_code=404, detail=f"Tool '{tool_name}' not found"
                )
            return tool_info.__dict__

        @app.post("/mcp/tools/{tool_name}/invoke")
        async def invoke_mcp_tool_endpoint(
            tool_name: str, args: Optional[Dict[str, Any]] = None
        ):
            """Invoke an MCP tool."""
            result = await self.invoke_mcp_tool(tool_name, args)
            return {"result": result}

        @app.get("/system/status")
        async def system_status():
            """Get full system status."""
            return self.get_system_status()

        @app.get("/system/components")
        async def system_components():
            """Get system components information."""
            from architecture import get_component_map

            return {"components": get_component_map()}

        return app

    def export_usage_data(self, filepath: Optional[str] = None) -> str:
        """Export token usage data.

        Parameters
        ----------
        filepath : Optional[str]
            Path to export file.

        Returns
        -------
        str
            Path to exported file.
        """
        return self.token_tracker.export_to_json(filepath)

    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get all MCP tools information.

        Returns
        -------
        List[Dict[str, Any]]
            List of MCP tools.
        """
        return self.mcp_server.list_tools()

    def create_agent_version(
        self,
        agent_name: str,
        version: str,
        author: str,
        description: str = "",
        dependencies: Optional[List[str]] = None,
    ):
        """Create a new agent version."""
        return self.version_manager.create_version(
            agent_name, version, author, description, dependencies
        )

    def promote_agent_version(
        self, agent_name: str, version: str, target_env: str, user: str = "system"
    ):
        """Promote agent version through environments."""
        if target_env == "test":
            return self.version_manager.transition_version(
                agent_name, version, TransitionAction.PROMOTE, user
            )
        elif target_env == "prod":
            # Ensure it's in testing first
            current_test = self.version_manager.get_current_version(agent_name, "test")
            if not current_test or current_test.version != version:
                self.version_manager.transition_version(
                    agent_name, version, TransitionAction.PROMOTE, user
                )
            return self.version_manager.transition_version(
                agent_name, version, TransitionAction.PROMOTE, user
            )

    def get_agent_version(self, agent_name: str, environment: str = "prod"):
        """Get current agent version for environment."""
        return self.version_manager.get_current_version(agent_name, environment)

    def list_agent_versions(self, agent_name: Optional[str] = None):
        """List agent versions."""
        return self.version_manager.list_versions(agent_name)

    def update_agent_metadata(self, agent_name: str, version: str, **metadata):
        """Update agent version metadata."""
        return self.version_manager.update_version_metadata(
            agent_name, version, **metadata
        )

    def create_user(
        self,
        username: str,
        email: str,
        full_name: str,
        password: str,
        role: str = "user",
    ):
        """Create a new user."""

        role_enum = UserRole(role)
        return self.auth_manager.create_user(
            username, email, full_name, password, role_enum
        )

    def authenticate_user(self, username: str, password: str):
        """Authenticate a user."""
        return self.auth_manager.authenticate_user(username, password)

    def get_user(self, user_id: str):
        """Get user by ID."""
        return self.auth_manager.get_user(user_id)

    def list_users(self):
        """List all users."""
        return self.auth_manager.list_users()

    def get_user_permissions(self, user):
        """Get permissions for a user."""
        return self.rbac_manager.get_user_permissions(user)

    def check_user_permission(self, user, permission: str) -> bool:
        """Check if user has permission."""
        return self.rbac_manager.check_permission(user, permission)

    async def invoke_mcp_tool(
        self, name: str, args: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Invoke an MCP tool.

        Parameters
        ----------
        name : str
            Tool name
        args : Optional[Dict[str, Any]]
            Tool arguments

        Returns
        -------
        Any
            Tool execution result
        """
        result = await self.mcp_client.invoke_tool(name, args)
        return (
            result.result if result.status.name == "SUCCESS" else result.error_message
        )

    def register_mcp_tool(
        self,
        name: str,
        tool_function: callable,
        description: str,
        schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Register a tool with MCP server.

        Parameters
        ----------
        name : str
            Tool name
        tool_function : callable
            Tool function
        description : str
            Tool description
        schema : Optional[Dict[str, Any]]
            Tool parameter schema
        tags : Optional[List[str]]
            Tool tags

        Returns
        -------
        bool
            Registration success
        """
        return self.mcp_server.register_tool(
            name=name,
            tool_function=tool_function,
            description=description,
            schema=schema,
            tags=tags,
        )

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status.

        Returns
        -------
        Dict[str, Any]
            System status overview.
        """
        # Count agents by environment
        dev_agents = sum(
            1 for agent in self._agents.keys() if self.get_agent_version(agent, "dev")
        )
        test_agents = sum(
            1 for agent in self._agents.keys() if self.get_agent_version(agent, "test")
        )
        prod_agents = sum(
            1 for agent in self._agents.keys() if self.get_agent_version(agent, "prod")
        )

        return {
            "status": "running" if self._is_initialized else "stopped",
            "agents_registered": len(self._agents),
            "agents": list(self._agents.keys()),
            "versioning": {
                "dev_agents": dev_agents,
                "test_agents": test_agents,
                "prod_agents": prod_agents,
                "total_versions": len(self.list_agent_versions()),
            },
            "authentication": {
                "enabled": True,
                "total_users": len(self.list_users()),
                "roles": [role["role"] for role in self.rbac_manager.get_all_roles()],
            },
            "metrics_enabled": True,
            "health_monitoring_enabled": self.health_monitor._is_running,
            "token_tracking_enabled": True,
            "classifier_enabled": True,
            "mcp_enabled": True,
            "mcp_tools_count": len(self.mcp_server.list_tools()),
            "versioning_enabled": True,
            "rbac_enabled": True,
        }


# Singleton instance
_system: Optional[MultiAgentSystem] = None


def get_system(
    classifier_config: Optional[IntentClassifierConfig] = None,
    health_config: Optional[HealthConfig] = None,
) -> MultiAgentSystem:
    """Get or create singleton system instance.

    Parameters
    ----------
    classifier_config : Optional[IntentClassifierConfig]
        Configuration for intent classifier.
    health_config : Optional[HealthConfig]
        Configuration for health monitor.

    Returns
    -------
    MultiAgentSystem
        The system instance.
    """
    global _system
    if _system is None:
        _system = MultiAgentSystem(classifier_config, health_config)
    return _system


if __name__ == "__main__":
    import uvicorn

    system = MultiAgentSystem()
    system.initialize()

    async def mock_agent_check():
        await asyncio.sleep(0.1)
        return True

    system.register_agent("planner", None, mock_agent_check, "Complex task planning")
    system.register_agent(
        "coder", None, mock_agent_check, "Code writing and file creation"
    )
    system.register_agent(
        "tester", None, mock_agent_check, "Running tests and validation"
    )

    print("\n" + "=" * 60)
    print("Testing Intent Classification")
    print("=" * 60)

    test_queries = [
        "Write a Python function to calculate factorial",
        "Create a plan for building a web app",
        "Review this code for security issues",
        "Run the tests for the calculator module",
    ]

    for query in test_queries:
        result = system.classify_and_route(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result['intent']}")
        print(f"Target Agent: {result['target_agent']}")
        print(f"Confidence: {result['confidence']}")

    print("\n" + "=" * 60)
    print("Starting Health API")
    print("=" * 60)

    system.start_health_monitoring()
    app = system.create_health_api()

    uvicorn.run(app, host="0.0.0.0", port=8001)
