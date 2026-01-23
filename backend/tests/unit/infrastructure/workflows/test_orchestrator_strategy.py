"""
Unit tests for OrchestratorStrategy.

Following TDD (Test-Driven Development):
1. RED: Write failing tests first
2. GREEN: Implement just enough to pass
3. REFACTOR: Improve code quality
"""

import pytest

from src.domain.entities import Agent, DomainConfig
from src.infrastructure.langgraph.workflow_strategies import (
    OrchestratorStrategy,
    WorkflowResult,
    WorkflowStep,
)


class TestOrchestratorStrategy:
    """Tests for the OrchestratorStrategy class."""

    def test_init_creates_instance(self):
        """Strategy should be instantiable."""
        strategy = OrchestratorStrategy()
        assert strategy is not None
        assert isinstance(strategy, OrchestratorStrategy)

    def test_executes_pipeline_in_order(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Orchestrator should execute agents in pipeline order.

        Given: Domain with pipeline [planner, coder, tester, reviewer]
        When: Execute with user request
        Then: Steps executed in exact order
        """
        strategy = OrchestratorStrategy()
        user_request = "Build a REST API for user management"

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request=user_request,
        )

        # Verify result structure
        assert isinstance(result, WorkflowResult)
        assert len(result.steps) == 4

        # Verify execution order
        expected_order = ["planner", "coder", "tester", "reviewer"]
        actual_order = [step.agent_id for step in result.steps]
        assert actual_order == expected_order

    def test_executes_empty_pipeline_gracefully(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle empty pipeline without errors.

        Given: Domain with empty pipeline
        When: Execute
        Then: Returns empty result without errors
        """
        # Modify domain to have empty pipeline
        orchestrator_domain.metadata["orchestration"]["pipeline"] = []
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Test request",
        )

        assert isinstance(result, WorkflowResult)
        assert len(result.steps) == 0
        assert result.final_response == ""

    def test_raises_error_for_unknown_agent_in_pipeline(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should raise ValueError for unknown agent in pipeline.

        Given: Pipeline with unknown agent ID
        When: Execute
        Then: Raises ValueError with clear message
        """
        # Add unknown agent to pipeline
        orchestrator_domain.metadata["orchestration"]["pipeline"] = [
            "planner",
            "unknown_agent",
            "coder",
        ]
        strategy = OrchestratorStrategy()

        with pytest.raises(ValueError, match="Unknown agent_id: unknown_agent"):
            strategy.execute(
                domain=orchestrator_domain,
                agents=software_dev_agents,
                user_request="Test request",
            )

    def test_passes_context_between_agents(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Each agent should receive previous agent's output in context.

        Given: Pipeline with multiple agents
        When: Execute workflow
        Then: Each agent receives accumulated context from previous steps
        """
        strategy = OrchestratorStrategy()
        user_request = "Create a login API"

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request=user_request,
        )

        # First agent gets original request
        assert result.steps[0].task == user_request

        # Subsequent agents get accumulated context
        for i in range(1, len(result.steps)):
            step = result.steps[i]
            # Task should contain previous outputs
            assert "Previous output:" in step.task
            # Should include original request
            assert user_request in step.task

    def test_final_response_is_last_agent_output(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Final response should be the output from the last agent.

        Given: Pipeline with multiple agents
        When: Execute workflow
        Then: final_response equals last step's result
        """
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Test request",
        )

        last_step_result = result.steps[-1].metadata["result"]
        assert result.final_response == last_step_result

    def test_includes_strategy_metadata(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Result should include strategy type in metadata.

        Given: Orchestrator strategy
        When: Execute workflow
        Then: metadata contains strategy="orchestrator"
        """
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Test request",
        )

        assert "strategy" in result.metadata
        assert result.metadata["strategy"] == "orchestrator"

    def test_each_step_includes_agent_metadata(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Each step should include agent_id, task, and result metadata.

        Given: Pipeline execution
        When: Workflow completes
        Then: Each step has required fields
        """
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Test request",
        )

        for step in result.steps:
            assert isinstance(step, WorkflowStep)
            assert isinstance(step.agent_id, str)
            assert len(step.agent_id) > 0
            assert isinstance(step.task, str)
            assert isinstance(step.metadata, dict)
            assert "result" in step.metadata

    def test_handles_single_agent_pipeline(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should work correctly with single-agent pipeline.

        Given: Pipeline with only one agent
        When: Execute
        Then: Single step executed, final_response set correctly
        """
        orchestrator_domain.metadata["orchestration"]["pipeline"] = ["coder"]
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Write a function",
        )

        assert len(result.steps) == 1
        assert result.steps[0].agent_id == "coder"
        assert result.final_response == result.steps[0].metadata["result"]

    def test_workflow_result_is_serializable(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        WorkflowResult should be serializable for logging/storage.

        Given: Completed workflow
        When: Access result fields
        Then: All fields are JSON-serializable types
        """
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Test request",
        )

        # Check all fields are basic types
        assert isinstance(result.steps, list)
        assert isinstance(result.final_response, str)
        assert isinstance(result.metadata, dict)

        # Steps should have basic types
        for step in result.steps:
            assert isinstance(step.agent_id, str)
            assert isinstance(step.task, str)
            assert isinstance(step.metadata, dict)


class TestOrchestratorStrategyEdgeCases:
    """Edge case tests for OrchestratorStrategy."""

    def test_handles_missing_orchestration_config(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle missing orchestration config gracefully.

        Given: Domain without orchestration metadata
        When: Execute
        Then: Uses empty pipeline, returns empty result
        """
        orchestrator_domain.metadata.pop("orchestration", None)
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="Test",
        )

        assert len(result.steps) == 0

    def test_handles_malformed_pipeline_config(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle malformed pipeline config.

        Given: orchestration.pipeline is not a list
        When: Execute
        Then: Handles gracefully or raises clear error
        """
        orchestrator_domain.metadata["orchestration"]["pipeline"] = "not-a-list"
        strategy = OrchestratorStrategy()

        # Should either handle gracefully or raise TypeError
        try:
            result = strategy.execute(
                domain=orchestrator_domain,
                agents=software_dev_agents,
                user_request="Test",
            )
            # If it doesn't raise, should return empty result
            assert len(result.steps) == 0
        except TypeError as e:
            # If it raises, should be clear error message
            assert "pipeline" in str(e).lower()

    def test_handles_empty_agents_dict(
        self,
        orchestrator_domain: DomainConfig,
    ):
        """
        Should handle empty agents dictionary.

        Given: Empty agents dict
        When: Execute with pipeline
        Then: Raises ValueError for each unknown agent
        """
        strategy = OrchestratorStrategy()

        with pytest.raises(ValueError, match="Unknown agent_id"):
            strategy.execute(
                domain=orchestrator_domain,
                agents={},  # Empty agents
                user_request="Test",
            )

    def test_handles_empty_user_request(
        self,
        orchestrator_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle empty user request.

        Given: Empty string user request
        When: Execute
        Then: Workflow completes with empty input
        """
        strategy = OrchestratorStrategy()

        result = strategy.execute(
            domain=orchestrator_domain,
            agents=software_dev_agents,
            user_request="",
        )

        assert isinstance(result, WorkflowResult)
        assert len(result.steps) > 0
        assert result.steps[0].task == ""
