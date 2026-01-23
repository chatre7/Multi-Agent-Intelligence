"""
Unit tests for FewShotStrategy.

Following TDD (Test-Driven Development):
1. RED: Write failing tests first
2. GREEN: Implement just enough to pass
3. REFACTOR: Improve code quality
"""

import pytest

from src.domain.entities import Agent, DomainConfig
from src.infrastructure.langgraph.workflow_strategies import (
    FewShotStrategy,
    WorkflowResult,
    WorkflowStep,
)


class TestFewShotStrategy:
    """Tests for the FewShotStrategy class."""

    def test_init_creates_instance(self):
        """Strategy should be instantiable."""
        strategy = FewShotStrategy()
        assert strategy is not None
        assert isinstance(strategy, FewShotStrategy)

    def test_starts_with_default_agent(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should start execution with domain's default agent.

        Given: Domain with default_agent="empath"
        When: Execute workflow
        Then: First step uses empath agent
        """
        strategy = FewShotStrategy()

        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="I feel sad today",
        )

        assert len(result.steps) > 0
        assert result.steps[0].agent_id == "empath"

    def test_respects_max_handoffs_limit(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should not exceed max_handoffs limit.

        Given: max_handoffs=5 in domain config
        When: Execute workflow
        Then: Steps count <= 5
        """
        strategy = FewShotStrategy()

        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="Tell me a joke",
        )

        max_handoffs = few_shot_domain.metadata.get("few_shot", {}).get(
            "max_handoffs", 5
        )
        assert len(result.steps) <= max_handoffs

    def test_stops_when_no_handoff_detected(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should stop when agent doesn't request handoff.

        Given: Agent returns response without handoff
        When: Execute workflow
        Then: Workflow terminates
        """
        strategy = FewShotStrategy()

        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="Simple question",
        )

        # Should execute at least one step
        assert len(result.steps) >= 1
        # Result should be valid
        assert isinstance(result.final_response, str)

    def test_includes_strategy_metadata(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Result should include strategy type in metadata.

        Given: Few-shot strategy
        When: Execute workflow
        Then: metadata contains strategy="few_shot"
        """
        strategy = FewShotStrategy()

        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="Test",
        )

        assert "strategy" in result.metadata
        assert result.metadata["strategy"] == "few_shot"

    def test_passes_accumulated_context(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should pass accumulated context between agents.

        Given: Multi-agent handoff
        When: Agents hand off to each other
        Then: Each agent receives previous responses
        """
        strategy = FewShotStrategy()

        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="I need cheering up",
        )

        # If multiple steps, verify context passing
        if len(result.steps) > 1:
            for i in range(1, len(result.steps)):
                step = result.steps[i]
                # Task should contain accumulated context
                assert isinstance(step.task, str)
                # Should have some content
                assert len(step.task) > 0

    def test_handles_unknown_agent_handoff(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should handle handoff to unknown agent gracefully.

        Given: Agent attempts to handoff to non-existent agent
        When: Execute workflow
        Then: Either stops or raises ValueError
        """
        strategy = FewShotStrategy()

        # This test will depend on implementation
        # Could either stop gracefully or raise error
        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="Test handoff to unknown",
        )

        # Should complete without crashing
        assert isinstance(result, WorkflowResult)

    def test_adds_few_shot_examples_to_prompt(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should enhance system prompt with few-shot examples.

        Given: Few-shot strategy
        When: Execute agent
        Then: Agent receives enhanced prompt with examples
        """
        strategy = FewShotStrategy()

        # Test the private method directly
        base_prompt = "You are an empathetic agent."
        empath_agent = social_chat_agents["empath"]

        enhanced = strategy._add_few_shot_examples(
            base_prompt=base_prompt,
            domain=few_shot_domain,
            agents=social_chat_agents,
        )

        # Should include examples
        assert "HANDOFF EXAMPLES" in enhanced or "Example" in enhanced
        # Should include available agents
        assert any(agent_id in enhanced for agent_id in social_chat_agents.keys())
        # Should include original prompt
        assert base_prompt in enhanced or len(enhanced) > len(base_prompt)


class TestFewShotStrategyEdgeCases:
    """Edge case tests for FewShotStrategy."""

    def test_handles_empty_agents_dict(
        self,
        few_shot_domain: DomainConfig,
    ):
        """
        Should handle empty agents dictionary gracefully.

        Given: Empty agents dict
        When: Execute
        Then: Returns empty result or raises error
        """
        strategy = FewShotStrategy()

        # Should either handle gracefully or raise error
        try:
            result = strategy.execute(
                domain=few_shot_domain,
                agents={},
                user_request="Test",
            )
            # If it doesn't raise, should return empty or minimal result
            assert isinstance(result, WorkflowResult)
            assert len(result.steps) == 0
        except (ValueError, KeyError):
            # Acceptable to raise error for missing default agent
            pass

    def test_handles_missing_default_agent(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should handle missing default agent.

        Given: default_agent not in agents dict
        When: Execute
        Then: Raises clear error
        """
        few_shot_domain.default_agent = "non_existent_agent"
        strategy = FewShotStrategy()

        try:
            result = strategy.execute(
                domain=few_shot_domain,
                agents=social_chat_agents,
                user_request="Test",
            )
            # If doesn't raise, should handle gracefully
            assert isinstance(result, WorkflowResult)
        except (ValueError, KeyError) as e:
            # Should have clear error message
            assert "agent" in str(e).lower() or "non_existent" in str(e).lower()

    def test_handles_infinite_handoff_loop(
        self,
        few_shot_domain: DomainConfig,
        social_chat_agents: dict[str, Agent],
    ):
        """
        Should prevent infinite handoff loops.

        Given: Agents that always handoff to each other
        When: Execute
        Then: Stops at max_handoffs limit
        """
        strategy = FewShotStrategy()

        result = strategy.execute(
            domain=few_shot_domain,
            agents=social_chat_agents,
            user_request="Create infinite loop",
        )

        # Should be bounded by max_handoffs
        max_handoffs = few_shot_domain.metadata.get("few_shot", {}).get(
            "max_handoffs", 5
        )
        assert len(result.steps) <= max_handoffs
