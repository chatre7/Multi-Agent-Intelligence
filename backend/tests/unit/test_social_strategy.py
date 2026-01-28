
import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.langgraph.social_strategy import SocialSimulationStrategy
from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig
from src.infrastructure.langgraph.workflow_strategies import WorkflowResult

class TestSocialSimulationStrategy(unittest.TestCase):
    @patch("src.infrastructure.langgraph.social_strategy.llm_from_env")
    def setUp(self, mock_llm_factory):
        self.mock_llm = MagicMock()
        mock_llm_factory.return_value = self.mock_llm
        self.strategy = SocialSimulationStrategy()
        
        # Setup mock agents using MagicMock to avoid constructor issues
        self.agent1 = MagicMock(spec=Agent)
        self.agent1.id = "agent1"
        self.agent1.name = "Agent One"
        self.agent1.system_prompt = "Be nice"
        self.agent1.role = "assistant"
        self.agent1.metadata = {"handle": "@agent1"}
        
        self.agent2 = MagicMock(spec=Agent)
        self.agent2.id = "agent2"
        self.agent2.name = "Agent Two"
        self.agent2.system_prompt = "Be mean"
        self.agent2.role = "assistant"
        self.agent2.metadata = {"handle": "@agent2"}
        
        self.agents = {"agent1": self.agent1, "agent2": self.agent2}
        
        # Setup mock domain
        self.domain = MagicMock(spec=DomainConfig)
        self.domain.metadata = {"social_simulation": {"max_turns": 3}}

    def test_execute_simulation_flow(self):
        """Test the main execution loop."""
        # Mock LLM response
        self.mock_llm.invoke.return_value.content = "This is a reply <likes>10</likes>"
        
        result = self.strategy.execute(
            domain=self.domain,
            agents=self.agents,
            user_request="Let's talk about AI."
        )
        
        # Validation
        self.assertIsInstance(result, WorkflowResult)
        self.assertEqual(len(result.steps), 3) # Max turns is 3
        
        # Check step content
        first_step = result.steps[0]
        # output is not a field in WorkflowStep, content is in metadata['result']
        self.assertEqual(first_step.metadata['result'], "This is a reply")
        self.assertEqual(first_step.metadata['likes'], 10)
        
        # Verify LLM was called 3 times
        self.assertEqual(self.mock_llm.invoke.call_count, 3)

    @patch("src.infrastructure.langgraph.social_strategy.random.choice")
    def test_next_speaker_selection(self, mock_choice):
        """Test speaker selection logic."""
        # We manually call internal method for specific logic test
        mock_choice.side_effect = lambda x: x[0] # Deterministic pick
        
        selected = self.strategy._select_next_speaker(list(self.agents.values()), last_speaker_id="agent1")
        self.assertEqual(selected.id, "agent2")
        
    def test_parse_likes(self):
        content = "Great post! <likes>99</likes>"
        likes = self.strategy._parse_likes(content)
        self.assertEqual(likes, 99)

if __name__ == '__main__':
    unittest.main()
