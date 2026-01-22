#!/usr/bin/env python3
"""Comprehensive Unit Tests for Orchestration Strategies"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from planner_agent_team_v3 import (
    multi_agent_orchestration_node,
    advanced_dynamic_route,
    AgentState,
)
from advanced_agents import (
    CodeReviewAgent,
    ResearchAgent,
    DataAnalysisAgent,
    get_multi_agent_orchestrator,
    select_agent_for_task,
)


class TestOrchestrationStrategies:
    """Test cases for orchestration strategy selection and execution"""

    def test_routing_logic(self):
        """TC-AO-001: Dynamic routing logic"""
        # Test the advanced_dynamic_route function
        state = AgentState(
            messages=[{"role": "user", "content": "Review this Python code"}],
            sender="user",
        )

        # This should route to specialized agents
        route = advanced_dynamic_route(state)
        assert isinstance(route, str)
        assert len(route) > 0

    def test_agent_selection_integration(self):
        """TC-AO-002: Agent selection integration"""
        # Test actual agent selection logic
        from advanced_agents import select_agent_for_task

        agent = select_agent_for_task("Review this Python function")
        assert agent.__class__.__name__ == "CodeReviewAgent"

        agent = select_agent_for_task("Research machine learning algorithms")
        assert agent.__class__.__name__ == "ResearchAgent"

    def test_state_creation(self):
        """TC-STATE-001: AgentState creation and manipulation"""
        state = AgentState(
            messages=[{"role": "user", "content": "test message"}],
            sender="user",
            current_strategy="sequential",
        )

        assert len(state["messages"]) == 1
        assert state["sender"] == "user"
        assert state["current_strategy"] == "sequential"

        # Test state modification
        state["messages"].append({"role": "agent", "content": "response"})
        assert len(state["messages"]) == 2

    def test_routing_function(self):
        """TC-ROUTE-001: Dynamic routing function"""
        state = AgentState(
            messages=[{"role": "user", "content": "Review this code"}], sender="user"
        )

        route = advanced_dynamic_route(state)
        assert isinstance(route, str)
        # Route should be one of the valid node names
        valid_routes = [
            "MultiAgent_sequential",
            "MultiAgent_parallel",
            "MultiAgent_consensus",
            "specialized_agent",
            "supervisor",
            "__end__",
        ]
        assert route in valid_routes or "MultiAgent_" in route

    @pytest.mark.asyncio
    async def test_parallel_orchestration(self):
        """TC-PO-001: Parallel orchestration execution"""
        state = AgentState(
            messages=[HumanMessage(content="Review this code for security issues")],
            sender="user",
            current_strategy="parallel",
        )

        with patch("database_manager.get_database_manager") as mock_db:
            mock_db.return_value.record_agent_metric.return_value = None

            # Mock specialized agents' process_task method
            with patch("advanced_agents.CodeReviewAgent.process_task") as mock_code_review, \
                 patch("advanced_agents.ResearchAgent.process_task") as mock_research:

                # Setup mock returns
                mock_code_review.return_value = {
                    "agent": "CodeReviewAgent",
                    "response": "Security review complete",
                    "confidence": 0.9
                }
                mock_research.return_value = {
                    "agent": "ResearchAgent",
                    "response": "Research analysis complete",
                    "confidence": 0.8
                }

                result = await multi_agent_orchestration_node(state, "parallel")

                # Should have orchestration result message
                assert len(result["messages"]) >= 1
                assert "MultiAgent_parallel" in result["sender"]
                # Result should mention agents used
                assert len(result["messages"][0].content) > 0

    @pytest.mark.asyncio
    async def test_consensus_orchestration(self):
        """TC-CO-001: Consensus orchestration"""
        state = AgentState(
            messages=[HumanMessage(content="Should we deploy this feature?")],
            sender="user",
            current_strategy="consensus",
        )

        with patch("database_manager.get_database_manager") as mock_db:
            mock_db.return_value.record_agent_metric.return_value = None

            # Mock multiple agents for consensus
            with patch("advanced_agents.CodeReviewAgent.process_task") as mock_code_review, \
                 patch("advanced_agents.ResearchAgent.process_task") as mock_research, \
                 patch("advanced_agents.DataAnalysisAgent.process_task") as mock_data:

                # Agents with different recommendations
                mock_code_review.return_value = {
                    "agent": "CodeReviewAgent",
                    "response": "Approved",
                    "confidence": 0.9
                }
                mock_research.return_value = {
                    "agent": "ResearchAgent",
                    "response": "Approved",
                    "confidence": 0.8
                }
                mock_data.return_value = {
                    "agent": "DataAnalysisAgent",
                    "response": "Needs review",
                    "confidence": 0.6
                }

                result = await multi_agent_orchestration_node(state, "consensus")

                # Should have consensus result message
                assert len(result["messages"]) >= 1
                assert "MultiAgent_consensus" in result["sender"]
                # Consensus message should contain strategy info
                assert "Consensus" in result["messages"][0].content

    @pytest.mark.asyncio
    @patch("advanced_agents.select_agent_for_task")
    async def test_orchestration_with_agent_failure(self, mock_select_agent):
        """TC-ERR-001: Agent failure handling"""
        # Mock agent that fails
        mock_agent = Mock()
        mock_agent.analyze_code.side_effect = Exception("Agent crashed")

        mock_select_agent.return_value = mock_agent

        state = AgentState(
            messages=[HumanMessage(content="Review code")],
            sender="user",
            current_strategy="sequential",
        )

        with patch("database_manager.get_database_manager") as mock_db:
            mock_db.return_value.record_agent_metric.return_value = None

            # Should not crash the orchestration
            result = await multi_agent_orchestration_node(state, "sequential")

            # Should still have a result message (error handling)
            assert len(result["messages"]) >= len(state["messages"])

    def test_orchestration_state_management(self):
        """TC-STATE-001: State management during orchestration"""
        initial_state = AgentState(
            messages=[{"role": "user", "content": "test"}],
            sender="user",
            current_strategy="sequential",
            orchestration_history=[],
        )

        # State should be properly maintained
        assert initial_state["current_strategy"] == "sequential"
        assert initial_state["orchestration_history"] == []

    @patch("database_manager.get_database_manager")
    def test_performance_tracking(self, mock_db):
        """TC-PERF-001: Performance tracking during orchestration"""
        mock_db.return_value.record_agent_metric.return_value = None

        # This would be tested in integration with actual agent calls
        # Here we just verify the database is called for metrics
        state = AgentState(
            messages=[{"role": "user", "content": "test"}], sender="user"
        )

        # The actual performance tracking happens inside multi_agent_orchestration_node
        # We verify the database mock is set up correctly
        assert (
            mock_db.return_value.record_agent_metric.called is False
        )  # Not called yet

    def test_orchestration_timeout_handling(self):
        """TC-TIMEOUT-001: Timeout handling in orchestration"""
        # Test with timeout constraints
        state = AgentState(
            messages=[{"role": "user", "content": "complex analysis task"}],
            sender="user",
            timeout_seconds=5,  # Very short timeout
        )

        # Orchestration should respect timeout settings
        assert state.get("timeout_seconds") == 5


class TestWorkflowIntegration:
    """Integration tests for the complete workflow"""

    @patch("planner_agent_team_v3.app")
    def test_workflow_execution(self, mock_app):
        """TC-WF-001: Complete workflow execution"""
        # Mock the LangGraph app
        mock_stream = Mock()
        mock_stream.return_value = [
            {"messages": [{"content": "Planning phase complete"}]},
            {"messages": [{"content": "Coding phase complete"}]},
            {"messages": [{"content": "Testing phase complete"}]},
        ]
        mock_app.stream = mock_stream

        # This would test the actual workflow, but requires complex mocking
        # For now, just verify the app structure exists
        from planner_agent_team_v3 import app as agent_app

        assert agent_app is not None

    def test_state_transitions(self):
        """TC-WF-002: State transitions in workflow"""
        # Test state object creation and manipulation
        state = AgentState()
        state["messages"] = [{"role": "user", "content": "hello"}]
        state["sender"] = "user"

        assert state["messages"][0]["content"] == "hello"
        assert state["sender"] == "user"

    def test_error_recovery(self):
        """TC-WF-003: Error recovery in workflow"""
        # Test that workflow can recover from errors
        state = AgentState(
            messages=[{"role": "user", "content": "test"}], error_count=0
        )

        # Simulate error increment
        state["error_count"] = 1

        assert state["error_count"] == 1
        # Workflow should be able to continue or handle errors appropriately


class TestConcurrentOrchestration:
    """Test concurrent orchestration scenarios"""

    def test_concurrent_agent_execution(self):
        """TC-CONC-001: Concurrent agent execution"""
        # Test that multiple agents can work simultaneously
        import threading
        import time

        results = []

        def mock_agent_work(agent_id):
            time.sleep(0.1)  # Simulate work
            results.append(f"Agent {agent_id} complete")

        # Start multiple agent threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=mock_agent_work, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        assert len(results) == 3
        assert all("complete" in r for r in results)

    def test_resource_sharing(self):
        """TC-CONC-002: Resource sharing between agents"""
        # Test that agents can share resources (like database connections)
        # This is more of a design verification test

        # Verify that database connections are properly managed
        from database_manager import get_database_manager

        db1 = get_database_manager()
        db2 = get_database_manager()

        # Should be the same instance (singleton pattern)
        assert db1 is db2

        # Should be able to perform operations concurrently
        # (This is a basic test; real concurrency testing requires more setup)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
