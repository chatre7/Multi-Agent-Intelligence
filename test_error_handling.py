#!/usr/bin/env python3
"""Test Error Handling in Agent System"""

import sys
import time
from langchain_core.messages import HumanMessage
from planner_agent_team_v3 import app


def test_specialized_agent_invocation():
    """Test if specialized agents can be invoked successfully"""
    print("\n" + "=" * 80)
    print("TEST: Specialized Agent Invocation")
    print("=" * 80)

    test_cases = [
        {
            "name": "CodeReviewAgent Test",
            "input": "Review this Python code: def add(a,b): return a+b",
            "expected_agent": "CodeReviewAgent",
        },
    ]

    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        print(f"Input: {test['input']}")

        config = {"configurable": {"thread_id": f"test_{test['name'].lower().replace(' ', '_')}"}}
        inputs = {
            "messages": [HumanMessage(content=test['input'])],
            "sender": "User",
        }

        try:
            # Run the graph with step limit
            result = None
            step_count = 0
            max_steps = 15
            start_time = time.time()

            for state in app.stream(inputs, config, stream_mode="values"):
                step_count += 1
                result = state
                sender = result.get("sender", "Unknown")
                next_agent = result.get("next_agent", "N/A")
                print(f"  Step {step_count}: sender={sender}, next_agent={next_agent}")

                # Check if we hit the specialized agent
                if sender == test['expected_agent']:
                    messages = result.get("messages", [])
                    if messages:
                        last_msg = messages[-1]
                        content = str(last_msg.content)[:300]
                        print(f"\n  {test['expected_agent']} Response:")
                        print(f"  {content}...")

                        # Check for errors in response
                        if "❌" in content or "error" in content.lower():
                            print(f"\n  ⚠️ ERROR DETECTED in agent response")
                        else:
                            print(f"\n  ✅ Agent completed successfully")

                if step_count >= max_steps:
                    print(f"\n  ⚠️ Reached max steps ({max_steps})")
                    break

            elapsed = time.time() - start_time
            print(f"\n  Time elapsed: {elapsed:.2f}s")
            print(f"  Total steps: {step_count}")

        except Exception as e:
            print(f"\n  ❌ ERROR: {type(e).__name__}: {str(e)[:200]}")
            import traceback
            traceback.print_exc()


def test_error_scenarios():
    """Test various error scenarios"""
    print("\n" + "=" * 80)
    print("TEST: Error Scenarios")
    print("=" * 80)

    error_tests = [
        {
            "name": "Empty Input",
            "input": "",
            "description": "Should handle empty input gracefully",
        },
        {
            "name": "Special Characters",
            "input": "Review this: <script>alert('xss')</script>",
            "description": "Should handle special characters safely",
        },
    ]

    for test in error_tests:
        print(f"\n--- {test['name']} ---")
        print(f"Description: {test['description']}")

        config = {"configurable": {"thread_id": f"error_test_{test['name'].lower().replace(' ', '_')}"}}
        inputs = {
            "messages": [HumanMessage(content=test['input'])],
            "sender": "User",
        }

        try:
            result = None
            count = 0
            for state in app.stream(inputs, config, stream_mode="values"):
                count += 1
                result = state
                if count >= 5:
                    break

            if result:
                print(f"  ✅ Handled gracefully ({count} steps)")
            else:
                print(f"  ⚠️ No result")

        except Exception as e:
            print(f"  ❌ ERROR: {type(e).__name__}: {str(e)[:100]}")


def main():
    """Run all error handling tests"""
    print("\n" + "=" * 80)
    print("ERROR HANDLING TEST SUITE")
    print("Testing actual agent invocation and error scenarios")
    print("=" * 80)

    test_specialized_agent_invocation()
    test_error_scenarios()

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
