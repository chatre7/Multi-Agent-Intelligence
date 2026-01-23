"""
Integration tests for workflow strategy system with graph_builder.

Tests the full integration from domain config -> strategy selection -> graph execution.
"""

import pytest

from src.domain.entities import Agent, DomainConfig
from src.domain.value_objects import AgentState, SemanticVersion
from src.infrastructure.langgraph.graph_builder import ConversationGraphBuilder


class TestWorkflowIntegration:
    """Integration tests for workflow strategies."""

    def test_orchestrator_workflow_integration(self):
        """
        Test orchestrator workflow end-to-end.
        
        Given: Domain with orchestrator workflow_type
        When: Build graph and execute
        Then: Agents execute in pipeline order
        """
        # Create domain with orchestrator config
        domain = DomainConfig(
            id="test_software_dev",
            name="Test Software Development",
            description="Test domain for orchestrator",
            agents=["planner", "coder"],
            default_agent="planner",
            workflow_type="supervisor",
            metadata={
                "workflow_type": "orchestrator",
                "orchestration": {
                    "pipeline": ["planner", "coder"]
                }
            }
        )
        
        # Create test agents
        agents = {
            "planner": Agent(
                id="planner",
                name="Planner",
                domain_id="test_software_dev",
                description="Test planner",
                version=SemanticVersion(1, 0, 0),
                state=AgentState.PRODUCTION,
                system_prompt="You are a planner.",
                capabilities=["planning"],
                tools=[],
                model_name="test-model",
            ),
            "coder": Agent(
                id="coder",
                name="Coder",
                domain_id="test_software_dev",
                description="Test coder",
                version=SemanticVersion(1, 0, 0),
                state=AgentState.PRODUCTION,
                system_prompt="You are a coder.",
                capabilities=["coding"],
                tools=[],
                model_name="test-model",
            ),
        }
        
        # Build graph
        builder = ConversationGraphBuilder()
        graph = builder.build(domain, agents)
        
        # Execute graph
        initial_state = {
            "domain_id": "test_software_dev",
            "messages": [
                {"role": "user", "content": "Build a REST API"}
            ],
            "selected_agent": "planner",
            "pending_tool_calls": [],
        }
        
        result = graph.invoke(initial_state)
        
        # Verify results
        assert "messages" in result
        assert len(result["messages"]) > 1  # User message + agent responses
        
        # Should have messages from both agents
        agent_ids = [
            msg.get("agent_id") 
            for msg in result["messages"] 
            if msg.get("role") == "assistant"
        ]
        assert "planner" in agent_ids
        assert "coder" in agent_ids

    def test_few_shot_workflow_integration(self):
        """
        Test few-shot workflow end-to-end.
        
        Given: Domain with few_shot workflow_type
        When: Build graph and execute
        Then: Workflow starts with default agent
        """
        # Create domain with few-shot config
        domain = DomainConfig(
            id="test_social_chat",
            name="Test Social Chat",
            description="Test domain for few-shot",
            agents=["empath", "comedian"],
            default_agent="empath",
            workflow_type="supervisor",
            metadata={
                "workflow_type": "few_shot",
                "few_shot": {
                    "max_handoffs": 3
                }
            }
        )
        
        # Create test agents
        agents = {
            "empath": Agent(
                id="empath",
                name="Empath",
                domain_id="test_social_chat",
                description="Test empath",
                version=SemanticVersion(1, 0, 0),
                state=AgentState.PRODUCTION,
                system_prompt="You are empathetic.",
                capabilities=["empathy"],
                tools=[],
                model_name="test-model",
            ),
            "comedian": Agent(
                id="comedian",
                name="Comedian",
                domain_id="test_social_chat",
                description="Test comedian",
                version=SemanticVersion(1, 0, 0),
                state=AgentState.PRODUCTION,
                system_prompt="You are funny.",
                capabilities=["humor"],
                tools=[],
                model_name="test-model",
            ),
        }
        
        # Build graph
        builder = ConversationGraphBuilder()
        graph = builder.build(domain, agents)
        
        # Execute graph
        initial_state = {
            "domain_id": "test_social_chat",
            "messages": [
                {"role": "user", "content": "I feel sad"}
            ],
            "selected_agent": "empath",
            "pending_tool_calls": [],
        }
        
        result = graph.invoke(initial_state)
        
        # Verify results
        assert "messages" in result
        assert len(result["messages"]) > 1
        
        # Should start with empath (default agent)
        first_agent_message = next(
            (msg for msg in result["messages"] if msg.get("role") == "assistant"),
            None
        )
        assert first_agent_message is not None
        assert first_agent_message.get("agent_id") == "empath"

    def test_supervisor_workflow_backward_compatibility(self):
        """
        Test that supervisor workflow still works (backward compatibility).
        
        Given: Domain without workflow_type metadata or workflow_type="supervisor"
        When: Build graph
        Then: Uses legacy supervisor workflow
        """
        # Create domain without workflow_type (should default to supervisor)
        domain = DomainConfig(
            id="test_legacy",
            name="Test Legacy",
            description="Test domain for backward compatibility",
            agents=["agent1"],
            default_agent="agent1",
            workflow_type="supervisor",  # Explicit supervisor
        )
        
        agents = {
            "agent1": Agent(
                id="agent1",
                name="Agent 1",
                domain_id="test_legacy",
                description="Test agent",
                version=SemanticVersion(1, 0, 0),
                state=AgentState.PRODUCTION,
                system_prompt="You are helpful.",
                capabilities=["general"],
                tools=[],
                model_name="test-model",
            ),
        }
        
        # Build graph - should use supervisor workflow
        builder = ConversationGraphBuilder()
        graph = builder.build(domain, agents)
        
        # Should build successfully
        assert graph is not None

    def test_strategy_executor_handles_errors_gracefully(self):
        """
        Test that strategy executor handles errors without crashing.
        
        Given: Domain with invalid agent configuration
        When: Execute strategy
        Then: Returns state unchanged with error logged
        """
        # Create domain with orchestrator but invalid pipeline
        domain = DomainConfig(
            id="test_error",
            name="Test Error Handling",
            description="Test error handling",
            agents=["agent1"],
            default_agent="agent1",
            metadata={
                "workflow_type": "orchestrator",
                "orchestration": {
                    "pipeline": ["nonexistent_agent"]  # Agent doesn't exist
                }
            }
        )
        
        agents = {
            "agent1": Agent(
                id="agent1",
                name="Agent 1",
                domain_id="test_error",
                description="Test agent",
                version=SemanticVersion(1, 0, 0),
                state=AgentState.PRODUCTION,
                system_prompt="You are helpful.",
                capabilities=["general"],
                tools=[],
                model_name="test-model",
            ),
        }
        
        # Build graph
        builder = ConversationGraphBuilder()
        graph = builder.build(domain, agents)
        
        initial_state = {
            "domain_id": "test_error",
            "messages": [
                {"role": "user", "content": "Test"}
            ],
            "selected_agent": "agent1",
            "pending_tool_calls": [],
        }
        
        # Should not crash, returns state unchanged
        result = graph.invoke(initial_state)
        assert "messages" in result
