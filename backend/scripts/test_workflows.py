#!/usr/bin/env python
"""
Manual test script for workflow strategies.

Usage:
    cd backend
    uv run python scripts/test_workflows.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.domain.entities import Agent, DomainConfig
from src.domain.value_objects import AgentState, SemanticVersion
from src.infrastructure.langgraph.workflow_strategies import (
    OrchestratorStrategy,
    FewShotStrategy,
    HybridStrategy,
    get_workflow_strategy,
)


def test_orchestrator():
    """Test orchestrator workflow."""
    print("\n" + "="*60)
    print("Testing Orchestrator Strategy")
    print("="*60)
    
    # Create domain
    domain = DomainConfig(
        id="test_software_dev",
        name="Test Software Development",
        description="Test orchestrator workflow",
        agents=["planner", "coder", "tester"],
        default_agent="planner",
        metadata={
            "workflow_type": "orchestrator",
            "orchestration": {
                "pipeline": ["planner", "coder", "tester"]
            }
        }
    )
    
    # Create agents
    agents = {
        "planner": Agent(
            id="planner",
            name="Planner",
            domain_id="test_software_dev",
            description="Plans tasks",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.PRODUCTION,
            system_prompt="You are a planner.",
            capabilities=["planning"],
            tools=[],
            model_name="test-model",
        ),
        "coder": Agent(
            id="coder",
            name="Coder",
            domain_id="test_software_dev",
            description="Writes code",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.PRODUCTION,
            system_prompt="You are a coder.",
            capabilities=["coding"],
            tools=[],
            model_name="test-model",
        ),
        "tester": Agent(
            id="tester",
            name="Tester",
            domain_id="test_software_dev",
            description="Tests code",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.PRODUCTION,
            system_prompt="You are a tester.",
            capabilities=["testing"],
            tools=[],
            model_name="test-model",
        ),
    }
    
    # Execute
    strategy = OrchestratorStrategy()
    result = strategy.execute(domain, agents, "Build a REST API for user management")
    
    # Display results
    print(f"\n✅ Strategy: {result.metadata.get('strategy')}")
    print(f"📝 Total Steps: {len(result.steps)}")
    print(f"\n🔄 Execution Flow:")
    for i, step in enumerate(result.steps, 1):
        print(f"  {i}. Agent: {step.agent_id}")
        print(f"     Task: {step.task[:50]}...")
        print(f"     Result: {step.metadata.get('result')}")
        print()
    
    print(f"✨ Final Response: {result.final_response}")
    return result


def test_few_shot():
    """Test few-shot workflow."""
    print("\n" + "="*60)
    print("Testing Few-Shot Strategy")
    print("="*60)
    
    # Create domain
    domain = DomainConfig(
        id="test_social_chat",
        name="Test Social Chat",
        description="Test few-shot workflow",
        agents=["empath", "comedian"],
        default_agent="empath",
        metadata={
            "workflow_type": "few_shot",
            "few_shot": {
                "max_handoffs": 3
            }
        }
    )
    
    # Create agents
    agents = {
        "empath": Agent(
            id="empath",
            name="Empath",
            domain_id="test_social_chat",
            description="Empathetic agent",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.PRODUCTION,
            system_prompt="You are empathetic.",
            capabilities=["empathy"],
            tools=[],
            model_name="test-model",
        ),
        "comedian": Agent(
            id="comedian",
            name="Comedian",
            domain_id="test_social_chat",
            description="Funny agent",
            version=SemanticVersion(1, 0, 0),
            state=AgentState.PRODUCTION,
            system_prompt="You are funny.",
            capabilities=["humor"],
            tools=[],
            model_name="test-model",
        ),
    }
    
    # Execute
    strategy = FewShotStrategy()
    result = strategy.execute(domain, agents, "I feel sad today, can you help?")
    
    # Display results
    print(f"\n✅ Strategy: {result.metadata.get('strategy')}")
    print(f"📝 Total Steps: {len(result.steps)}")
    print(f"🔁 Total Handoffs: {result.metadata.get('total_handoffs')}")
    print(f"\n🔄 Execution Flow:")
    for i, step in enumerate(result.steps, 1):
        handoff = step.metadata.get('handoff_to')
        print(f"  {i}. Agent: {step.agent_id}")
        print(f"     Iteration: {step.metadata.get('iteration')}")
        print(f"     Result: {step.metadata.get('result')}")
        if handoff:
            print(f"     ➡️  Handoff to: {handoff}")
        print()
    
    print(f"✨ Final Response: {result.final_response}")
    return result


def test_factory():
    """Test factory function."""
    print("\n" + "="*60)
    print("Testing Factory Function")
    print("="*60)
    
    # Test orchestrator
    domain_orch = DomainConfig(
        id="test1",
        name="Test 1",
        description="Test",
        agents=["a1"],
        default_agent="a1",
        metadata={"workflow_type": "orchestrator"}
    )
    strategy = get_workflow_strategy(domain_orch)
    print(f"✅ Orchestrator domain → {type(strategy).__name__}")
    
    # Test few-shot
    domain_few = DomainConfig(
        id="test2",
        name="Test 2",
        description="Test",
        agents=["a1"],
        default_agent="a1",
        metadata={"workflow_type": "few_shot"}
    )
    strategy = get_workflow_strategy(domain_few)
    print(f"✅ Few-shot domain → {type(strategy).__name__}")
    
    # Test hybrid
    domain_hybrid = DomainConfig(
        id="test3",
        name="Test 3",
        description="Test",
        agents=["a1"],
        default_agent="a1",
        metadata={"workflow_type": "hybrid"}
    )
    strategy = get_workflow_strategy(domain_hybrid)
    print(f"✅ Hybrid domain → {type(strategy).__name__}")
    
    # Test default (no metadata)
    domain_default = DomainConfig(
        id="test4",
        name="Test 4",
        description="Test",
        agents=["a1"],
        default_agent="a1",
    )
    strategy = get_workflow_strategy(domain_default)
    print(f"✅ Default domain → {type(strategy).__name__}")


def main():
    """Run all manual tests."""
    print("\n🧪 Multi-Workflow Strategy - Manual Testing")
    print("="*60)
    
    try:
        # Test 1: Orchestrator
        test_orchestrator()
        
        # Test 2: Few-shot
        test_few_shot()
        
        # Test 3: Factory
        test_factory()
        
        print("\n" + "="*60)
        print("✅ All manual tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
