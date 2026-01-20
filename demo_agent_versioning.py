#!/usr/bin/env python3
"""Agent Versioning Demo Script.

Demonstrates the agent versioning state machine functionality.
Shows how agents can be versioned, promoted through environments,
and managed in a production system.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_versioning import get_version_manager, AgentState, TransitionAction


def main():
    """Run agent versioning demo."""
    print("🚀 Agent Versioning State Machine Demo")
    print("=" * 50)

    # Initialize version manager
    vm = get_version_manager("./demo_agent_versions.json")

    # Demo 1: Create agent versions
    print("\n📦 Creating Agent Versions")
    print("-" * 30)

    # Create calculator agent versions
    calc_v1 = vm.create_version(
        agent_name="calculator",
        version="1.0.0",
        author="alice@example.com",
        description="Basic calculator with add/subtract/multiply/divide",
        dependencies=["math"],
    )
    print(f"✅ Created calculator v{calc_v1.version} in {calc_v1.state.value} state")

    calc_v2 = vm.create_version(
        agent_name="calculator",
        version="1.1.0",
        author="bob@example.com",
        description="Enhanced calculator with advanced functions",
        dependencies=["math", "numpy"],
    )
    print(f"✅ Created calculator v{calc_v2.version} in {calc_v2.state.value} state")

    # Create translator agent
    translator_v1 = vm.create_version(
        agent_name="translator",
        version="2.0.0",
        author="charlie@example.com",
        description="AI-powered language translator",
        dependencies=["transformers", "torch"],
    )
    print(
        f"✅ Created translator v{translator_v1.version} in {translator_v1.state.value} state"
    )

    # Demo 2: Update metadata and promote
    print("\n🔄 Promoting Versions Through Environments")
    print("-" * 45)

    # Update calculator v1.0.0 metadata for testing
    vm.update_version_metadata(
        "calculator",
        "1.0.0",
        test_results={"passed": 15, "failed": 0, "coverage": 95.0},
        performance_metrics={"latency_ms": 120, "throughput": 100},
    )
    print("✅ Updated calculator v1.0.0 with test results")

    # Promote calculator v1.0.0 to testing
    promoted_to_test = vm.transition_version(
        "calculator", "1.0.0", TransitionAction.PROMOTE
    )
    print(f"✅ Promoted calculator v1.0.0 to {promoted_to_test.state.value}")

    # Add production requirements and promote to production
    vm.update_version_metadata(
        "calculator",
        "1.0.0",
        security_scan_results={"vulnerabilities": 0, "critical_issues": 0},
        prod_config={"replicas": 3, "cpu_limit": "500m", "memory_limit": "1Gi"},
    )
    print("✅ Added production requirements to calculator v1.0.0")

    promoted_to_prod = vm.transition_version(
        "calculator", "1.0.0", TransitionAction.PROMOTE
    )
    print(f"✅ Promoted calculator v1.0.0 to {promoted_to_prod.state.value}")

    # Demo 3: Environment-specific version queries
    print("\n🌍 Environment-Specific Version Queries")
    print("-" * 40)

    dev_version = vm.get_current_version("calculator", "dev")
    test_version = vm.get_current_version("calculator", "test")
    prod_version = vm.get_current_version("calculator", "prod")

    print(
        f"Dev environment: {dev_version.version if dev_version else 'None'} ({dev_version.state.value if dev_version else 'N/A'})"
    )
    print(
        f"Test environment: {test_version.version if test_version else 'None'} ({test_version.state.value if test_version else 'N/A'})"
    )
    print(
        f"Prod environment: {prod_version.version if prod_version else 'None'} ({prod_version.state.value if prod_version else 'N/A'})"
    )

    # Demo 4: List and history
    print("\n📋 Version History and Management")
    print("-" * 35)

    # List all calculator versions
    calc_versions = vm.list_versions("calculator")
    print(f"Calculator versions: {len(calc_versions)}")
    for v in calc_versions:
        print(f"  - v{v.version}: {v.state.value} (by {v.author})")

    # Show transition history
    history = vm.get_transition_history("calculator")
    print(f"\nTransition history: {len(history)} events")
    for event in history[:3]:  # Show first 3
        print(
            f"  - {event['agent_name']} v{event['version']}: {event['current_state']} at {event['updated_at'][:19]}"
        )

    # Demo 5: Validation examples
    print("\n🛡️ Validation Examples")
    print("-" * 25)

    # Try to promote without validation (should fail)
    try:
        vm.transition_version("calculator", "1.1.0", TransitionAction.PROMOTE)
        print("❌ Unexpected success - validation should have failed")
    except Exception as e:
        print(f"✅ Correctly blocked promotion: {type(e).__name__}")

    # Try invalid transition
    try:
        vm.transition_version("calculator", "1.0.0", TransitionAction.ARCHIVE)
        print("❌ Unexpected success - invalid transition")
    except Exception as e:
        print(f"✅ Correctly blocked invalid transition: {type(e).__name__}")

    print("\n🎉 Agent Versioning Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Version creation with metadata")
    print("  ✅ Environment promotion (dev → test → prod)")
    print("  ✅ Validation requirements for production")
    print("  ✅ State transition history")
    print("  ✅ Environment-specific queries")
    print("  ✅ Invalid transition blocking")

    # Cleanup
    import os

    if os.path.exists("./demo_agent_versions.json"):
        os.remove("./demo_agent_versions.json")
        print("\n🧹 Cleaned up demo files")


if __name__ == "__main__":
    main()
