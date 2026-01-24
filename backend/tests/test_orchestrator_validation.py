
import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.langgraph.workflow_strategies import OrchestratorStrategy, WorkflowStep
from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig

class TestOrchestratorValidation(unittest.TestCase):
    def setUp(self):
        self.strategy = OrchestratorStrategy()
        self.mock_agent = MagicMock(spec=Agent)
        self.mock_agent.id = "test_agent"
        self.mock_agent.model_name = "test_model"
        self.mock_agent.system_prompt = "system"
        
        self.mock_domain = MagicMock(spec=DomainConfig)
        self.mock_domain.metadata = {"orchestration": {"pipeline": ["test_agent"]}}
        
        self.agents = {"test_agent": self.mock_agent}

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_validation_retry_success(self, mock_llm_factory):
        # Mock LLM to fail once then succeed
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        
        # First call returns empty (invalid), Second returns good content
        scan_side_effect = [
            [""], # First stream yields empty
            ["Valid Content"] # Second stream yields valid
        ]
        mock_llm.stream_chat.side_effect = scan_side_effect
        
        result = self.strategy.execute(self.mock_domain, self.agents, "Task")
        
        self.assertEqual(result.final_response, "Valid Content")
        # Should have called stream_chat twice
        self.assertEqual(mock_llm.stream_chat.call_count, 2)

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_validation_failure_max_retries(self, mock_llm_factory):
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        
        # Always return error
        mock_llm.stream_chat.return_value = ["[ERROR] Internal Error"]
        
        result = self.strategy.execute(self.mock_domain, self.agents, "Task")
        
        self.assertIn("[FATAL]", result.final_response)
        # Should have called max_retries (3) times
        self.assertEqual(mock_llm.stream_chat.call_count, 3)

if __name__ == "__main__":
    unittest.main()
