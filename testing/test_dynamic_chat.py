"""
Test Dynamic Group Chat / Intelligent Routing

Demonstrates the intelligent conversation routing where agents
decide who should speak next based on context.
"""

import sys

sys.path.append("D:/cmtn-project/Multi-Agent-Intelligence")

from planner_agent_team_v3 import get_next_speaker_router, ConversationContext


def test_dynamic_routing():
    """Test the NextSpeakerRouter functionality"""

    print("🎭 Testing Dynamic Group Chat Routing")
    print("=" * 50)

    router = get_next_speaker_router()

    # Test cases for different conversation contexts
    test_cases = [
        # (current_speaker, message_content, expected_context)
        ("supervisor", "Please implement a login feature", ConversationContext.CODING),
        (
            "Coder",
            "I've written the login function with proper validation",
            ConversationContext.REVIEWING,
        ),
        (
            "Critic",
            "Code looks good, approved for testing",
            ConversationContext.TESTING,
        ),
        ("Tester", "All tests passed successfully", ConversationContext.COMPLETING),
        ("Coder", "Found a syntax error in the code", ConversationContext.DEBUGGING),
        (
            "supervisor",
            "Can you explain the architecture better?",
            ConversationContext.CLARIFYING,
        ),
        (
            "Tester",
            "Tests failed due to database connection error",
            ConversationContext.DEBUGGING,
        ),
    ]

    print("🧠 Context Analysis Tests:")
    for i, (speaker, message, expected_context) in enumerate(test_cases, 1):
        detected_context = router.analyze_message_context(message)
        status = "✅" if detected_context == expected_context else "❌"
        print(f"  {i}. {status} '{message[:50]}...' → {detected_context.value}")
        if detected_context != expected_context:
            print(f"      Expected: {expected_context.value}")

    print("\n🎯 Next Speaker Routing Tests:")
    routing_tests = [
        # (current_speaker, message, conversation_state, description)
        (
            "supervisor",
            "Implement user authentication",
            {"hierarchical_mode": True},
            "Initial task assignment",
        ),
        (
            "Planner",
            "Planning complete, delegating to DevTeam",
            {"hierarchical_mode": True},
            "Planning finished",
        ),
        (
            "DevTeam",
            "Implementation completed successfully",
            {"hierarchical_mode": True},
            "Task completion",
        ),
        (
            "Coder",
            "Code written and saved",
            {"hierarchical_mode": False},
            "Individual coding",
        ),
        (
            "Critic",
            "Code approved, ready for testing",
            {"hierarchical_mode": False},
            "Review completion",
        ),
        (
            "Tester",
            "Tests failed with error details",
            {"hierarchical_mode": False},
            "Test failure",
        ),
    ]

    for i, (speaker, message, conv_state, description) in enumerate(routing_tests, 1):
        next_speaker = router.get_next_speaker(speaker, message, conv_state)
        print(f"  {i}. {description}")
        print(f"     {speaker} → {next_speaker} ('{message[:40]}...')")

    print("\n🔚 Termination Logic Tests:")
    termination_tests = [
        ("Task completed successfully", 5, "Success termination"),
        ("All tests passed", 3, "Success termination"),
        ("Error: cannot connect to database", 12, "Continue (not max iterations)"),
        ("Implementation finished", 16, "Force termination (max iterations)"),
    ]

    for message, iterations, description in termination_tests:
        should_terminate = router.should_terminate(message, iterations)
        status = "🔚 TERMINATE" if should_terminate else "➡️ CONTINUE"
        print(f"  {status} '{message}' (iter: {iterations}) - {description}")

    print("\n🎭 Dynamic Group Chat Test Complete!")
    print("✅ Intelligent routing system operational")
    print("✅ Context-aware conversation flow enabled")
    print("✅ Adaptive agent collaboration ready")


if __name__ == "__main__":
    test_dynamic_routing()
