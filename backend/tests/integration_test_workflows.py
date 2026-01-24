
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.langgraph.graph_builder import ConversationGraphBuilder
from src.domain.entities.domain_config import DomainConfig
from src.domain.entities.agent import Agent

def run_orchestrator_integration():
    print("--- Starting Orchestrator Integration Test ---")
    
    # 1. Setup Data
    agent1 = Agent(id="planner", name="Planner", domain_id="test", description="Plans", 
                   version="1.0.0", state="development", system_prompt="Plan stuff", 
                   capabilities=[], tools=[], model_name="mock")
    agent2 = Agent(id="coder", name="Coder", domain_id="test", description="Codes", 
                   version="1.0.0", state="development", system_prompt="Code stuff", 
                   capabilities=[], tools=[], model_name="mock")
    
    agents = {"planner": agent1, "coder": agent2}
    
    domain = DomainConfig(
        id="test_domain", name="Test Domain", description="Test",
        agents=["planner", "coder"], default_agent="planner",
        workflow_type="orchestrator",
        metadata={
            "orchestration": {"pipeline": ["planner", "coder"]}
        }
    )

    
    # 2. Mock LLM & Chroma
    with patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env") as mock_llm_factory, \
         patch("src.infrastructure.langgraph.graph_builder.ChromaMemoryRepository") as mock_chroma_class:
        
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        
        mock_chroma_instance = MagicMock()
        mock_chroma_class.return_value = mock_chroma_instance
        mock_chroma_instance.search_memories.return_value = [] # Return empty memories
        
        # Determine responses based on who is calling (system prompt check or simplistic sequence)
        # Sequence: Planner runs -> Coder runs
        mock_llm.stream_chat.side_effect = [
            ["Step 1: Create Plan"], # Planner output
            ["Step 2: Write Code"]   # Coder output
        ]
        
        # 3. Build Graph
        builder = ConversationGraphBuilder()
        graph = builder.build(domain, agents)
        
        # 4. Invoke
        print("Invoking graph...")
        initial_state = {
            "messages": [{"role": "user", "content": "Build an app"}],
            "domain_id": "test_domain"
        }
        
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "1"}})
        
        # 5. Assertions
        messages = result.get("messages", [])
        print(f"Result Messages Count: {len(messages)}")
        
        # Expect: User msg + Planner msg + Coder msg
        # Note: The strategy returns all steps. The graph builder appends them.
        
        has_plan = any("Step 1" in m["content"] for m in messages)
        has_code = any("Step 2" in m["content"] for m in messages)
        
        if has_plan and has_code:
            print("[PASS] Orchestrator executed pipeline correctly.")
        else:
            print(f"[FAIL] Missing steps. Messages: {messages}")

def run_fewshot_integration():
    print("\n--- Starting Few-Shot Integration Test ---")
    
    # Setup
    agent1 = Agent(id="router", name="Router", domain_id="test", description="Routes", 
                   version="1.0.0", state="development", system_prompt="Route", model_name="mock", capabilities=[], tools=[])
    agent2 = Agent(id="worker", name="Worker", domain_id="test", description="Works", 
                   version="1.0.0", state="development", system_prompt="Work", model_name="mock", capabilities=[], tools=[])
    
    agents = {"router": agent1, "worker": agent2}
    
    domain = DomainConfig(
        id="test_fewshot", name="Test FewShot", description="Test",
        agents=["router", "worker"], default_agent="router",
        workflow_type="few_shot",
        metadata={
            "few_shot": {"max_handoffs": 2} # Limit to prevent infinite loop if mock fails
        }
    )
    
    with patch("src.infrastructure.langgraph.workflow_strategies.llm_from_env") as mock_llm_factory, \
         patch("src.infrastructure.langgraph.graph_builder.ChromaMemoryRepository") as mock_chroma_class:
        
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm
        
        mock_chroma_class.return_value.search_memories.return_value = []
        
        # Flow:
        # 1. Router Agent runs (initial) -> "I need help"
        # 2. Router Decision -> "handoff" to "worker"
        # 3. Worker Agent runs -> "Job Done"
        # 4. Router Decision -> "finish"
        
        import json
        mock_llm.stream_chat.side_effect = [
            ["I analyze request, need worker."], # Agent Execution 1
            [json.dumps({"action": "handoff", "target_agent": "worker", "reason": "Worker needed"})], # Router Decision 1
            ["Task executed successfully."], # Agent Execution 2
            [json.dumps({"action": "finish", "reason": "Complete"})] # Router Decision 2
        ]
        
        builder = ConversationGraphBuilder()
        graph = builder.build(domain, agents)
        
        print("Invoking graph...")
        initial_state = {
            "messages": [{"role": "user", "content": "Do work"}],
            "domain_id": "test_fewshot"
        }
        
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "2"}})
        messages = result.get("messages", [])
        
        last_msg = messages[-1]["content"] if messages else ""
        print(f"Final Response: {last_msg}")
        
        if "Task executed successfully" in last_msg:
             print("[PASS] Few-Shot routed correctly.")
        else:
             print(f"[FAIL] Unexpected outcome: {messages}")

if __name__ == "__main__":
    try:
        run_orchestrator_integration()
        run_fewshot_integration()
        print("\nAll Integration Tests Completed.")
    except Exception as e:
        print(f"\n[ERROR] Test crashed: {e}")
        import traceback
        traceback.print_exc()
