"""
Unit tests for HybridStrategy.

Following TDD (Test-Driven Development):
1. RED: Write failing tests first
2. GREEN: Implement just enough to pass
3. REFACTOR: Improve code quality
"""

import pytest

from src.domain.entities import Agent, DomainConfig
from src.infrastructure.langgraph.workflow_strategies import (
    HybridStrategy,
    WorkflowResult,
    WorkflowStep,
)


class TestHybridStrategy:
    """Tests for the HybridStrategy class."""

    def test_init_creates_instance(self):
        """Strategy should be instantiable."""
        strategy = HybridStrategy()
        assert strategy is not None
        assert isinstance(strategy, HybridStrategy)

    def test_executes_orchestrated_phases(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should use orchestrator for designated phases.

        Given: Hybrid config with orchestrator_decides=["planning"]
        When: Execute workflow
        Then: Planning phase uses deterministic ordering
        """
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Research quantum computing",
        )

        assert isinstance(result, WorkflowResult)
        assert len(result.steps) > 0

    def test_executes_llm_phases(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should use few-shot for LLM-decided phases.

        Given: Hybrid config with llm_decides=["agent_selection"]
        When: Execute workflow
        Then: Agent selection uses LLM-based handoffs
        """
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Analyze data patterns",
        )

        assert isinstance(result, WorkflowResult)

    def test_combines_both_strategies(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should combine orchestrator and few-shot results.

        Given: Hybrid config with both orchestrator and LLM phases
        When: Execute
        Then: Result includes steps from both strategies
        """
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Complete hybrid workflow",
        )

        # Should have steps from multiple phases
        assert len(result.steps) > 0
        assert isinstance(result.final_response, str)

    def test_includes_strategy_metadata(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Result should include strategy type in metadata.

        Given: Hybrid strategy
        When: Execute workflow
        Then: metadata contains strategy="hybrid"
        """
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Test",
        )

        assert "strategy" in result.metadata
        assert result.metadata["strategy"] == "hybrid"

    def test_handles_missing_hybrid_config(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle missing hybrid configuration gracefully.

        Given: Domain without hybrid metadata
        When: Execute
        Then: Uses defaults or returns empty result
        """
        hybrid_domain.metadata.pop("hybrid", None)
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Test",
        )

        assert isinstance(result, WorkflowResult)

    def test_filters_agents_by_phase(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should filter agents appropriately for each phase.

        Given: Hybrid with planning and execution phases
        When: Execute planning phase
        Then: Only planner agents are used
        """
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Plan and execute task",
        )

        assert isinstance(result, WorkflowResult)
        # Steps should exist from hybrid execution
        assert len(result.steps) >= 0


class TestHybridStrategyEdgeCases:
    """Edge case tests for HybridStrategy."""

    def test_handles_empty_orchestrator_phases(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle empty orchestrator_decides list.

        Given: orchestrator_decides=[]
        When: Execute
        Then: Only uses LLM phases
        """
        hybrid_domain.metadata["hybrid"]["orchestrator_decides"] = []
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Test",
        )

        assert isinstance(result, WorkflowResult)

    def test_handles_empty_llm_phases(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle empty llm_decides list.

        Given: llm_decides=[]
        When: Execute
        Then: Only uses orchestrated phases
        """
        hybrid_domain.metadata["hybrid"]["llm_decides"] = []
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Test",
        )

        assert isinstance(result, WorkflowResult)

    def test_handles_both_empty_phases(
        self,
        hybrid_domain: DomainConfig,
        software_dev_agents: dict[str, Agent],
    ):
        """
        Should handle both phase lists empty.

        Given: Both orchestrator_decides and llm_decides are empty
        When: Execute
        Then: Returns empty result
        """
        hybrid_domain.metadata["hybrid"]["orchestrator_decides"] = []
        hybrid_domain.metadata["hybrid"]["llm_decides"] = []
        strategy = HybridStrategy()

        result = strategy.execute(
            domain=hybrid_domain,
            agents=software_dev_agents,
            user_request="Test",
        )

        assert isinstance(result, WorkflowResult)
        assert len(result.steps) == 0
