#!/usr/bin/env python3
"""Test Agent Routing Paths in Streamlit App"""

from planner_agent_team_v3 import app
from langchain_core.messages import HumanMessage
import sys

# Test cases for different agent routing
TEST_CASES = [
    {
        "name": "Simple Greeting (Thai)",
        "input": "สวัสดี",
        "expected_agent": "Planner",
        "expected_next": "FINISH",
        "description": "Should greet and finish"
    },
    {
        "name": "Simple Greeting (English)",
        "input": "Hello",
        "expected_agent": "Planner",
        "expected_next": "FINISH",
        "description": "Should greet and finish"
    },
    {
        "name": "Code Review (Thai)",
        "input": "รีวิวโค้ดให้หน่อย",
        "expected_agent": "Planner",
        "expected_next": "CodeReviewAgent",
        "description": "Should route to CodeReviewAgent"
    },
    {
        "name": "Code Review (English)",
        "input": "Review this code for bugs",
        "expected_agent": "Planner",
        "expected_next": "CodeReviewAgent",
        "description": "Should route to CodeReviewAgent"
    },
    {
        "name": "Research (Thai)",
        "input": "ค้นคว้าเรื่อง Python best practices",
        "expected_agent": "Planner",
        "expected_next": "ResearchAgent",
        "description": "Should route to ResearchAgent"
    },
    {
        "name": "Research (English)",
        "input": "Research the latest AI trends",
        "expected_agent": "Planner",
        "expected_next": "ResearchAgent",
        "description": "Should route to ResearchAgent"
    },
    {
        "name": "Data Analysis (Thai)",
        "input": "วิเคราะห์ข้อมูล sales ให้หน่อย",
        "expected_agent": "Planner",
        "expected_next": "DataAnalysisAgent",
        "description": "Should route to DataAnalysisAgent"
    },
    {
        "name": "Data Analysis (English)",
        "input": "Analyze this data and find patterns",
        "expected_agent": "Planner",
        "expected_next": "DataAnalysisAgent",
        "description": "Should route to DataAnalysisAgent"
    },
    {
        "name": "Documentation (Thai)",
        "input": "สร้าง README สำหรับโปรเจกต์",
        "expected_agent": "Planner",
        "expected_next": "DocumentationAgent",
        "description": "Should route to DocumentationAgent"
    },
    {
        "name": "Documentation (English)",
        "input": "Generate API documentation",
        "expected_agent": "Planner",
        "expected_next": "DocumentationAgent",
        "description": "Should route to DocumentationAgent"
    },
    {
        "name": "DevOps (Thai)",
        "input": "ตั้ง CI/CD pipeline ให้หน่อย",
        "expected_agent": "Planner",
        "expected_next": "DevOpsAgent",
        "description": "Should route to DevOpsAgent"
    },
    {
        "name": "DevOps (English)",
        "input": "Setup deployment pipeline",
        "expected_agent": "Planner",
        "expected_next": "DevOpsAgent",
        "description": "Should route to DevOpsAgent"
    },
    {
        "name": "Development (Thai)",
        "input": "พัฒนา login feature",
        "expected_agent": "Planner",
        "expected_next": "DevTeam",
        "description": "Should route to DevTeam"
    },
    {
        "name": "Development (English)",
        "input": "Build a user authentication system",
        "expected_agent": "Planner",
        "expected_next": "DevTeam",
        "description": "Should route to DevTeam"
    },
    {
        "name": "Ambiguous Request",
        "input": "Help me with my project",
        "expected_agent": "Planner",
        "expected_next": "supervisor",
        "description": "Should route to supervisor for intelligent routing"
    }
]


def test_routing(test_case, verbose=False):
    """Test a single routing case"""
    print(f"\n{'='*80}")
    print(f"Test: {test_case['name']}")
    print(f"Input: \"{test_case['input']}\"")
    print(f"Expected: {test_case['description']}")
    print(f"{'='*80}")

    try:
        # Create test state
        config = {"configurable": {"thread_id": f"test_{test_case['name'].lower().replace(' ', '_')}"}}
        inputs = {
            "messages": [HumanMessage(content=test_case['input'])],
            "sender": "User"
        }

        # Run graph (limit to 5 steps to see Planner output)
        result = None
        step_count = 0
        max_steps = 5
        planner_result = None

        for state in app.stream(inputs, config, stream_mode="values"):
            step_count += 1
            result = state

            # Get current sender and next_agent
            sender = result.get("sender", "Unknown")
            next_agent = result.get("next_agent", "Unknown")

            if verbose:
                print(f"  Step {step_count}: sender={sender}, next_agent={next_agent}")

            # Track when Planner executes
            if sender == "Planner":
                planner_result = result
                if verbose:
                    print(f"  📋 Planner executed, next_agent={next_agent}")

                # Check if Planner routed correctly
                expected_next = test_case['expected_next']
                if next_agent == expected_next:
                    print(f"  ✅ SUCCESS: Planner routed to {next_agent}")
                    return True
                elif next_agent == "FINISH" and expected_next == "FINISH":
                    print(f"  ✅ SUCCESS: Planner finished conversation")
                    return True
                else:
                    print(f"  ❌ FAILED: Expected {expected_next}, got {next_agent}")
                    return False

            if step_count >= max_steps:
                break

        # If we got here, check the final state
        if result:
            next_agent = result.get("next_agent", "Unknown")
            expected_next = test_case['expected_next']

            if next_agent == expected_next or (next_agent == "FINISH" and expected_next == "FINISH"):
                print(f"  ✅ SUCCESS: Final route to {next_agent}")
                return True
            else:
                print(f"  ❌ FAILED: Expected {expected_next}, got {next_agent}")
                return False
        else:
            print(f"  ❌ FAILED: No result returned")
            return False

    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {str(e)[:200]}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Run all routing tests"""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("\n" + "="*80)
    print("AGENT ROUTING TEST SUITE")
    print("Testing intelligent routing to specialized agents")
    print("="*80)

    results = []
    for test_case in TEST_CASES:
        success = test_routing(test_case, verbose=verbose)
        results.append({
            "name": test_case["name"],
            "input": test_case["input"],
            "success": success
        })

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Pass Rate: {passed/len(results)*100:.1f}%")

    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if not r["success"]:
                print(f"  ❌ {r['name']}: \"{r['input']}\"")

    print("\n" + "="*80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
