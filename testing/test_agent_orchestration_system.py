#!/usr/bin/env python3
"""Test Agent Orchestration"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_agents import get_multi_agent_orchestrator


async def test_agent_orchestration():
    print("🤖 Testing Agent Orchestration")
    print("=" * 50)

    # Test orchestrator initialization
    orchestrator = get_multi_agent_orchestrator()
    print("✅ Multi-agent orchestrator initialized")

    # Test sequential orchestration
    print("\\n🔄 Testing Sequential Orchestration...")
    try:
        result = await orchestrator.orchestrate_task(
            "Review this Python code for bugs: def add(a,b): return a+b",
            strategy="sequential",
        )
        print(f"✅ Sequential orchestration completed: {len(str(result))} chars")
        print(
            "📄 Result preview:",
            str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
        )
    except Exception as e:
        print(f"⚠️ Sequential orchestration failed: {e}")

    # Test parallel orchestration
    print("\\n🔀 Testing Parallel Orchestration...")
    try:
        result = await orchestrator.orchestrate_task(
            "Analyze this data and create a summary", strategy="parallel"
        )
        print(f"✅ Parallel orchestration completed: {len(str(result))} chars")
    except Exception as e:
        print(f"⚠️ Parallel orchestration failed: {e}")

    # Test consensus orchestration
    print("\\n⚖️ Testing Consensus Orchestration...")
    try:
        result = await orchestrator.orchestrate_task(
            "Should we use React or Vue for this project?", strategy="consensus"
        )
        print(f"✅ Consensus orchestration completed: {len(str(result))} chars")
    except Exception as e:
        print(f"⚠️ Consensus orchestration failed: {e}")

    print("\\n🎉 Agent orchestration test completed!")


if __name__ == "__main__":
    asyncio.run(test_agent_orchestration())
