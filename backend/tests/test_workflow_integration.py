"""
Integration tests for workflow strategies with graph builder.

These tests verify that workflow strategies integrate correctly with the
LangGraph builder and execute end-to-end workflows properly.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.infrastructure.langgraph.graph_builder import ConversationGraphBuilder
from src.domain.entities.domain_config import DomainConfig
from src.domain.entities.agent import Agent


class TestOrchestratorIntegration(unittest.TestCase):
    """Integration tests for orchestrator workflow strategy."""

    def setUp(self):
        """Set up test agents and domain."""
        self.agent1 = Agent(
            id="planner",
            name="Planner",
            domain_id="test",
            description="Plans tasks",
            version="1.0.0",
            state="development",
            system_prompt="Plan stuff",
            capabilities=[],
            tools=[],
            model_name="mock",
        )
        self.agent2 = Agent(
            id="coder",
            name="Coder",
            domain_id="test",
            description="Codes solutions",
            version="1.0.0",
            state="development",
            system_prompt="Code stuff",
            capabilities=[],
            tools=[],
            model_name="mock",
        )

        self.agents = {"planner": self.agent1, "coder": self.agent2}

        self.domain = DomainConfig(
            id="test_domain",
            name="Test Domain",
            description="Test domain",
            agents=["planner", "coder"],
            default_agent="planner",
            workflow_type="orchestrator",
            metadata={"orchestration": {"pipeline": ["planner", "coder"]}},
        )

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    @patch("src.infrastructure.langgraph.graph_builder.ChromaMemoryRepository")
    def test_orchestrator_pipeline_execution(
        self, mock_chroma_class, mock_llm_factory
    ):
        """Test that orchestrator executes pipeline in correct order."""
        # Mock LLM
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm

        # Mock ChromaDB
        mock_chroma_instance = MagicMock()
        mock_chroma_class.return_value = mock_chroma_instance
        mock_chroma_instance.search_memories.return_value = []

        # Sequence: Planner runs -> Coder runs
        mock_llm.stream_chat.side_effect = [
            ["Step 1: Create Plan"],  # Planner output
            ["Step 2: Write Code"],  # Coder output
        ]

        # Build graph
        builder = ConversationGraphBuilder()
        graph = builder.build(self.domain, self.agents)

        # Invoke
        initial_state = {
            "messages": [{"role": "user", "content": "Build an app"}],
            "domain_id": "test_domain",
        }

        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "1"}})

        # Assertions
        messages = result.get("messages", [])
        self.assertGreater(len(messages), 1, "Should have multiple messages")

        # Check that both agents executed
        has_plan = any("Step 1" in m.get("content", "") for m in messages)
        has_code = any("Step 2" in m.get("content", "") for m in messages)

        self.assertTrue(has_plan, "Should contain planning output")
        self.assertTrue(has_code, "Should contain coding output")

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    @patch("src.infrastructure.langgraph.graph_builder.ChromaMemoryRepository")
    def test_orchestrator_with_validation_retry(
        self, mock_chroma_class, mock_llm_factory
    ):
        """Test that orchestrator retries on validation failure."""
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm

        mock_chroma_class.return_value.search_memories.return_value = []

        # First call fails (empty), second succeeds
        mock_llm.stream_chat.side_effect = [
            [""],  # Planner fails
            ["Valid Plan"],  # Planner succeeds on retry
            ["Code Output"],  # Coder output
        ]

        builder = ConversationGraphBuilder()
        graph = builder.build(self.domain, self.agents)

        initial_state = {
            "messages": [{"role": "user", "content": "Build app"}],
            "domain_id": "test_domain",
        }

        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "2"}})

        # Should have retried and succeeded
        messages = result.get("messages", [])
        has_valid_plan = any("Valid Plan" in m.get("content", "") for m in messages)

        self.assertTrue(has_valid_plan, "Should contain valid plan after retry")


class TestFewShotIntegration(unittest.TestCase):
    """Integration tests for few-shot workflow strategy."""

    def setUp(self):
        """Set up test agents and domain."""
        self.agent1 = Agent(
            id="router",
            name="Router",
            domain_id="test",
            description="Routes requests",
            version="1.0.0",
            state="development",
            system_prompt="Route",
            model_name="mock",
            capabilities=[],
            tools=[],
        )
        self.agent2 = Agent(
            id="worker",
            name="Worker",
            domain_id="test",
            description="Does work",
            version="1.0.0",
            state="development",
            system_prompt="Work",
            model_name="mock",
            capabilities=[],
            tools=[],
        )

        self.agents = {"router": self.agent1, "worker": self.agent2}

        self.domain = DomainConfig(
            id="test_fewshot",
            name="Test FewShot",
            description="Test few-shot domain",
            agents=["router", "worker"],
            default_agent="router",
            workflow_type="few_shot",
            metadata={"few_shot": {"max_handoffs": 2}},
        )

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    @patch("src.infrastructure.langgraph.graph_builder.ChromaMemoryRepository")
    def test_fewshot_handoff_flow(self, mock_chroma_class, mock_llm_factory):
        """Test that few-shot strategy handles agent handoffs correctly."""
        import json

        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm

        mock_chroma_class.return_value.search_memories.return_value = []

        # Flow:
        # 1. Router Agent runs -> "I analyze request, need worker."
        # 2. Router Decision -> handoff to "worker"
        # 3. Worker Agent runs -> "Task executed successfully."
        # 4. Router Decision -> finish

        mock_llm.stream_chat.side_effect = [
            ["I analyze request, need worker."],  # Agent Execution 1
            [
                json.dumps(
                    {
                        "action": "handoff",
                        "target_agent": "worker",
                        "reason": "Worker needed",
                    }
                )
            ],  # Router Decision 1
            ["Task executed successfully."],  # Agent Execution 2
            [json.dumps({"action": "finish", "reason": "Complete"})],  # Router Decision 2
        ]

        builder = ConversationGraphBuilder()
        graph = builder.build(self.domain, self.agents)

        initial_state = {
            "messages": [{"role": "user", "content": "Do work"}],
            "domain_id": "test_fewshot",
        }

        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "3"}})
        messages = result.get("messages", [])

        # Check that worker was invoked
        has_worker_output = any(
            "Task executed successfully" in m.get("content", "") for m in messages
        )
        self.assertTrue(has_worker_output, "Should contain worker output after handoff")


if __name__ == "__main__":
    unittest.main()
