#!/usr/bin/env python3
"""
Comprehensive Agent Response Quality Testing Suite

Tests all specialized agents with various inputs and evaluates:
- Response completeness
- Response time
- Accuracy
- Error handling
- Edge cases
"""

import time
import json
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage
from planner_agent_team_v3 import app


class AgentQualityTester:
    """Test agent response quality"""

    def __init__(self):
        self.results = []
        self.test_count = 0

    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case"""
        self.test_count += 1

        print(f"\n{'='*80}")
        print(f"Test #{self.test_count}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"Agent: {test_case['expected_agent']}")
        print(f"Input: {test_case['input'][:100]}...")
        print(f"Expected: {test_case['expected_behavior']}")

        config = {
            "configurable": {
                "thread_id": f"quality_test_{self.test_count}_{int(time.time())}"
            }
        }
        inputs = {"messages": [HumanMessage(content=test_case["input"])], "sender": "User"}

        result = {
            "test_name": test_case["name"],
            "agent": test_case["expected_agent"],
            "input": test_case["input"],
            "success": False,
            "response": None,
            "time_taken": 0,
            "steps": 0,
            "agent_reached": False,
            "error": None,
            "evaluation": {}
        }

        start_time = time.time()

        try:
            step_count = 0
            max_steps = 20
            agent_response = None
            agent_reached = False

            for state in app.stream(inputs, config, stream_mode="values"):
                step_count += 1
                sender = state.get("sender", "Unknown")

                print(f"  Step {step_count}: {sender}", end="")

                # Check if we reached the expected agent
                if sender == test_case["expected_agent"]:
                    agent_reached = True
                    messages = state.get("messages", [])
                    if messages:
                        last_msg = messages[-1]
                        agent_response = str(last_msg.content) if hasattr(last_msg, "content") else str(last_msg)
                        print(f" ✅ (Got response: {len(agent_response)} chars)")
                else:
                    print()

                if step_count >= max_steps:
                    print(f"\n  ⚠️ Reached max steps ({max_steps})")
                    break

            elapsed = time.time() - start_time

            # Store results
            result["time_taken"] = round(elapsed, 2)
            result["steps"] = step_count
            result["agent_reached"] = agent_reached
            result["response"] = agent_response

            if agent_reached and agent_response:
                result["success"] = True
                result["evaluation"] = self.evaluate_response(
                    test_case, agent_response
                )

                print(f"\n  ✅ SUCCESS")
                print(f"  Time: {elapsed:.2f}s | Steps: {step_count}")
                print(f"  Response length: {len(agent_response)} characters")
                print(f"\n  Response preview:")
                print(f"  {agent_response[:300]}...")

                # Print evaluation
                print(f"\n  📊 Evaluation:")
                for criterion, score in result["evaluation"].items():
                    print(f"    {criterion}: {score}")

            else:
                result["success"] = False
                result["error"] = "Agent not reached or no response"
                print(f"\n  ❌ FAILED: {result['error']}")

        except Exception as e:
            elapsed = time.time() - start_time
            result["time_taken"] = round(elapsed, 2)
            result["error"] = str(e)
            result["success"] = False
            print(f"\n  ❌ ERROR: {str(e)[:200]}")

        self.results.append(result)
        return result

    def evaluate_response(self, test_case: Dict[str, Any], response: str) -> Dict[str, str]:
        """Evaluate response quality based on criteria"""
        evaluation = {}

        # Check length
        if len(response) < 50:
            evaluation["Length"] = "❌ Too short"
        elif len(response) > 5000:
            evaluation["Length"] = "⚠️ Very long"
        else:
            evaluation["Length"] = "✅ Good"

        # Check for key indicators based on agent type
        agent = test_case["expected_agent"]

        if agent == "CodeReviewAgent":
            checks = ["security", "quality", "bug", "issue", "recommendation"]
            found = sum(1 for word in checks if word.lower() in response.lower())
            evaluation["Relevance"] = f"✅ {found}/5 keywords" if found >= 3 else f"⚠️ {found}/5 keywords"

        elif agent == "ResearchAgent":
            checks = ["research", "study", "analysis", "evidence", "finding"]
            found = sum(1 for word in checks if word.lower() in response.lower())
            evaluation["Relevance"] = f"✅ {found}/5 keywords" if found >= 2 else f"⚠️ {found}/5 keywords"

        elif agent == "DataAnalysisAgent":
            checks = ["data", "analysis", "statistic", "pattern", "insight"]
            found = sum(1 for word in checks if word.lower() in response.lower())
            evaluation["Relevance"] = f"✅ {found}/5 keywords" if found >= 3 else f"⚠️ {found}/5 keywords"

        elif agent == "DocumentationAgent":
            checks = ["documentation", "api", "guide", "example", "usage"]
            found = sum(1 for word in checks if word.lower() in response.lower())
            evaluation["Relevance"] = f"✅ {found}/5 keywords" if found >= 2 else f"⚠️ {found}/5 keywords"

        elif agent == "DevOpsAgent":
            checks = ["deploy", "pipeline", "infrastructure", "ci/cd", "automation"]
            found = sum(1 for word in checks if word.lower() in response.lower())
            evaluation["Relevance"] = f"✅ {found}/5 keywords" if found >= 2 else f"⚠️ {found}/5 keywords"

        # Check for error indicators
        if "error" in response.lower() or "failed" in response.lower():
            evaluation["Status"] = "⚠️ Contains errors"
        else:
            evaluation["Status"] = "✅ No errors"

        # Check for completeness indicators
        if "complete" in response.lower() or "analysis" in response.lower():
            evaluation["Completeness"] = "✅ Appears complete"
        else:
            evaluation["Completeness"] = "⚠️ May be incomplete"

        return evaluation

    def generate_report(self):
        """Generate comprehensive test report"""
        print(f"\n\n{'='*80}")
        print("AGENT RESPONSE QUALITY TEST REPORT")
        print(f"{'='*80}\n")

        # Summary statistics
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful

        print(f"📊 SUMMARY STATISTICS")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"✅ Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")

        if successful > 0:
            avg_time = sum(r["time_taken"] for r in self.results if r["success"]) / successful
            avg_steps = sum(r["steps"] for r in self.results if r["success"]) / successful
            print(f"\n⏱️ Average Response Time: {avg_time:.2f}s")
            print(f"📈 Average Steps: {avg_steps:.1f}")

        # Results by agent
        print(f"\n\n📋 RESULTS BY AGENT")
        print(f"{'='*80}")

        agents = {}
        for result in self.results:
            agent = result["agent"]
            if agent not in agents:
                agents[agent] = {"total": 0, "success": 0, "times": []}
            agents[agent]["total"] += 1
            if result["success"]:
                agents[agent]["success"] += 1
                agents[agent]["times"].append(result["time_taken"])

        for agent, stats in agents.items():
            success_rate = stats["success"] / stats["total"] * 100
            avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0

            print(f"\n{agent}:")
            print(f"  Success Rate: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
            if stats["times"]:
                print(f"  Avg Time: {avg_time:.2f}s")
                print(f"  Time Range: {min(stats['times']):.2f}s - {max(stats['times']):.2f}s")

        # Detailed results
        print(f"\n\n📝 DETAILED TEST RESULTS")
        print(f"{'='*80}")

        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. {result['test_name']}")
            print(f"   Agent: {result['agent']}")
            print(f"   Status: {'✅ PASS' if result['success'] else '❌ FAIL'}")
            print(f"   Time: {result['time_taken']}s | Steps: {result['steps']}")

            if result["success"] and result["evaluation"]:
                print(f"   Evaluation:")
                for criterion, score in result["evaluation"].items():
                    print(f"     - {criterion}: {score}")

            if result["error"]:
                print(f"   Error: {result['error']}")

        # Recommendations
        print(f"\n\n💡 RECOMMENDATIONS")
        print(f"{'='*80}")

        if failed > 0:
            print(f"1. {failed} tests failed - review error messages above")

        slow_tests = [r for r in self.results if r["success"] and r["time_taken"] > 15]
        if slow_tests:
            print(f"2. {len(slow_tests)} tests took >15s - consider optimization")

        print(f"\n3. Review evaluation scores for areas of improvement")
        print(f"4. Consider improving prompts for agents with low relevance scores")

        # Save results to JSON
        output_file = "test_agent_quality_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Detailed results saved to: {output_file}")


def main():
    """Run all agent quality tests"""
    tester = AgentQualityTester()

    # Define test cases
    test_cases = [
        # CodeReviewAgent Tests
        {
            "name": "Simple Python Function Review",
            "expected_agent": "CodeReviewAgent",
            "input": "Review this Python code:\n\ndef calculate_total(items):\n    total = 0\n    for item in items:\n        total += item['price']\n    return total",
            "expected_behavior": "Should identify potential issues, suggest improvements"
        },
        {
            "name": "Code with Security Issue",
            "expected_agent": "CodeReviewAgent",
            "input": "Review this code for security issues:\n\nimport os\nuser_input = input('Enter filename: ')\nos.system(f'cat {user_input}')",
            "expected_behavior": "Should identify command injection vulnerability"
        },
        {
            "name": "Code with Performance Issue",
            "expected_agent": "CodeReviewAgent",
            "input": "Review this code for performance:\n\ndef find_duplicates(list1, list2):\n    duplicates = []\n    for item in list1:\n        if item in list2:\n            duplicates.append(item)\n    return duplicates",
            "expected_behavior": "Should suggest using set for O(1) lookup"
        },

        # ResearchAgent Tests
        {
            "name": "Research Python Best Practices",
            "expected_agent": "ResearchAgent",
            "input": "Research current Python best practices for error handling in 2024",
            "expected_behavior": "Should provide researched information with sources"
        },
        {
            "name": "Research Technology Comparison",
            "expected_agent": "ResearchAgent",
            "input": "Research and compare REST API vs GraphQL for modern web applications",
            "expected_behavior": "Should provide comparative analysis"
        },

        # DataAnalysisAgent Tests
        {
            "name": "Simple Data Analysis",
            "expected_agent": "DataAnalysisAgent",
            "input": "Analyze this data and find patterns: [10, 15, 13, 17, 20, 25, 22, 30, 28, 35]",
            "expected_behavior": "Should identify trends, statistics"
        },
        {
            "name": "Statistical Analysis Request",
            "expected_agent": "DataAnalysisAgent",
            "input": "Analyze this dataset for statistical insights: Sales data shows [100, 120, 115, 130, 140, 135, 150, 160, 155, 170]",
            "expected_behavior": "Should provide mean, trend, predictions"
        },

        # DocumentationAgent Tests
        {
            "name": "API Documentation Request",
            "expected_agent": "DocumentationAgent",
            "input": "Generate API documentation for a user authentication endpoint with POST /api/auth/login",
            "expected_behavior": "Should create structured API docs"
        },
        {
            "name": "README Generation",
            "expected_agent": "DocumentationAgent",
            "input": "Create a README for a Python project that handles web scraping",
            "expected_behavior": "Should generate comprehensive README"
        },

        # DevOpsAgent Tests
        {
            "name": "CI/CD Pipeline Setup",
            "expected_agent": "DevOpsAgent",
            "input": "Setup a CI/CD pipeline for a Node.js application with GitHub Actions",
            "expected_behavior": "Should provide pipeline configuration"
        },
        {
            "name": "Docker Configuration",
            "expected_agent": "DevOpsAgent",
            "input": "Create Docker configuration for deploying a Python Flask application",
            "expected_behavior": "Should provide Dockerfile and setup"
        },
    ]

    print(f"\n{'='*80}")
    print("AGENT RESPONSE QUALITY TESTING")
    print(f"Total Test Cases: {len(test_cases)}")
    print(f"{'='*80}\n")

    # Run all tests
    for test_case in test_cases:
        tester.run_test(test_case)
        time.sleep(1)  # Small delay between tests

    # Generate report
    tester.generate_report()


if __name__ == "__main__":
    main()
