"""
Test Hierarchical Chat / DevTeam Subgraph

Demonstrates the hierarchical agent system where DevTeam works autonomously.
"""

import sys

sys.path.append("D:/cmtn-project/Multi-Agent-Intelligence")

from planner_agent_team_v3 import get_dev_team_subgraph
from langchain_core.messages import SystemMessage


def test_hierarchical_devteam():
    """Test the DevTeam subgraph functionality"""

    print("🏗️ Testing Hierarchical DevTeam Subgraph")
    print("=" * 50)

    # Get the DevTeam subgraph
    dev_team = get_dev_team_subgraph()

    # Initial state
    initial_state = {
        "messages": [
            SystemMessage(content="Task: Create a simple calculator function")
        ],
        "sender": "supervisor",
        "task_summary": "Create a simple calculator function",
        "iteration_count": 0,
        "dev_status": "planning",
    }

    print("📋 Initial Task:", initial_state["task_summary"])
    print("👥 DevTeam Status:", initial_state["dev_status"])
    print()

    # Simulate a few iterations
    max_iterations = 5
    current_state = initial_state

    for i in range(max_iterations):
        print(f"🔄 Iteration {i + 1}:")

        # Run one step of the DevTeam
        try:
            result = dev_team.invoke(current_state)
            current_state = result

            # Print status
            messages = result.get("messages", [])
            if messages:
                last_msg = (
                    str(messages[-1].content)[:100] + "..."
                    if len(str(messages[-1].content)) > 100
                    else str(messages[-1].content)
                )
                print(f"   📝 Message: {last_msg}")

            dev_status = result.get("dev_status", "unknown")
            print(f"   📊 Status: {dev_status}")

            iteration_count = result.get("iteration_count", 0)
            print(f"   🔢 Iterations: {iteration_count}")

            # Check if completed
            if dev_status in ["completed", "failed"]:
                final_result = result.get("final_result", "No final result")
                print(f"   🎯 Final Result: {final_result}")
                break

        except Exception as e:
            print(f"   ❌ Error: {e}")
            break

        print()

    print("🏁 DevTeam Test Complete")
    print(f"Final Status: {current_state.get('dev_status', 'unknown')}")
    print(f"Total Iterations: {current_state.get('iteration_count', 0)}")


if __name__ == "__main__":
    test_hierarchical_devteam()
