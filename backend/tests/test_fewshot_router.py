
import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.langgraph.workflow_strategies import FewShotStrategy, WorkflowStep, WorkflowResult
from src.domain.entities.agent import Agent
from src.domain.entities.domain_config import DomainConfig
import json

class TestFewShotRouter(unittest.TestCase):
    def setUp(self):
        self.strategy = FewShotStrategy()
        
        # Mock Agents
        self.agent1 = MagicMock(spec=Agent)
        self.agent1.id = "agent1"
        self.agent1.system_prompt = "Prompt 1"
        self.agent1.model_name = "model1"
        
        self.agent2 = MagicMock(spec=Agent)
        self.agent2.id = "agent2"
        self.agent2.system_prompt = "Prompt 2"
        self.agent2.model_name = "model2"
        
        self.agents = {"agent1": self.agent1, "agent2": self.agent2}
        
        # Mock Domain
        self.domain = MagicMock(spec=DomainConfig)
        self.domain.default_agent = "agent1"
        self.domain.metadata = {
            "few_shot": {
                "max_handoffs": 3,
                "routing_examples": [
                    {
                        "situation": "Test Situation", 
                        "decision": {"action": "finish", "reason": "Test"}
                    }
                ]
            }
        }

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_router_handoff_flow(self, mock_llm_factory):
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        
        # Simulation:
        # 1. Agent1 executes -> "I did part 1"
        # 2. Router decides -> Handoff to Agent2
        # 3. Agent2 executes -> "I finished part 2"
        # 4. Router decides -> Finish
        
        # Stream chat returns:
        # Call 1 (Agent1): "Task Result 1"
        # Call 2 (Router): JSON Handoff
        # Call 3 (Agent2): "Task Result 2"
        # Call 4 (Router): JSON Finish
        
        mock_llm.stream_chat.side_effect = [
            ["Task Result 1"],
            [json.dumps({"action": "handoff", "target_agent": "agent2", "reason": "Next step"})],
            ["Task Result 2"],
            [json.dumps({"action": "finish", "reason": "Done"})]
        ]
        
        result = self.strategy.execute(self.domain, self.agents, "Start Task")

        # Check flow - includes both agent steps and router decision steps
        # Flow: agent1 -> router -> agent2 -> router
        self.assertEqual(len(result.steps), 4)

        # Filter out router steps to check agent execution
        agent_steps = [s for s in result.steps if s.agent_id != "router"]
        self.assertEqual(len(agent_steps), 2)
        self.assertEqual(agent_steps[0].agent_id, "agent1")
        self.assertEqual(agent_steps[1].agent_id, "agent2")
        self.assertEqual(result.final_response, "Task Result 2")
        
        # specific assertions on router prompt containment
        # (This is harder to test without inspecting call args deeply, but logic holds)

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_router_max_handoffs(self, mock_llm_factory):
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        
        # Infinite handoff loop simulation
        # Agent -> Router (Handoff) -> Agent -> Router (Handoff) ...
        
        def infinite_generator(*args, **kwargs):
            # If system prompt contains "Router", return handoff
            if "Router" in kwargs.get("system_prompt", ""):
                 yield json.dumps({"action": "handoff", "target_agent": "agent2"})
            else:
                 yield "Work done"
                 
        mock_llm.stream_chat.side_effect = infinite_generator
        
        # Limit to 2 handoffs to text quick termination
        self.domain.metadata["few_shot"]["max_handoffs"] = 2
        
        result = self.strategy.execute(self.domain, self.agents, "Start")

        # Should stop after max_handoffs iterations (2 in this case)
        # Each iteration creates: agent step + router decision step
        # So we expect up to 4 total steps (2 iterations * 2 steps each)
        # But it might be less if router decides to finish early
        self.assertLessEqual(len(result.steps), 4)

        # Check that we have at most max_handoffs agent executions
        agent_steps = [s for s in result.steps if s.agent_id != "router"]
        self.assertLessEqual(len(agent_steps), 2) 

if __name__ == "__main__":
    unittest.main()
