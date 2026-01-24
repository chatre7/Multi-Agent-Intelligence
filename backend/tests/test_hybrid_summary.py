
import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.langgraph.workflow_strategies import HybridStrategy, DomainConfig
import os

class TestHybridSummarization(unittest.TestCase):
    def setUp(self):
        self.strategy = HybridStrategy()
        
    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_short_context_no_summary(self, mock_llm_factory):
        # Short context (< 1000 chars) should not trigger LLM summary
        short_context = "Short context."
        result = self.strategy._summarize_context(short_context, "Test")
        self.assertEqual(result, short_context)
        mock_llm_factory.assert_not_called()

    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_long_context_summary(self, mock_llm_factory):
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        mock_llm.stream_chat.return_value = ["Key points summary."]
        
        # Long context simulation
        long_context = "A" * 2000 
        
        result = self.strategy._summarize_context(long_context, "Planning")
        
        self.assertIn("--- Planning Phase Summary ---", result)
        self.assertIn("Key points summary.", result)
        
    @patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env")
    def test_summary_failure_fallback(self, mock_llm_factory):
        # Even if long, if LLM fails, return original
        mock_llm_factory.return_value = None # No LLM
        
        long_context = "B" * 2000
        result = self.strategy._summarize_context(long_context, "Execution")
        
        self.assertEqual(result, long_context)

if __name__ == "__main__":
    unittest.main()
