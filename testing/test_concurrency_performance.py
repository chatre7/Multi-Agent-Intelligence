#!/usr/bin/env python3
"""Test System Concurrency and Performance"""

import asyncio
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_agents import get_multi_agent_orchestrator
from database_manager import get_database_manager


async def test_concurrent_orchestration():
    """Test concurrent agent orchestration"""
    print("⚡ Testing Concurrent Agent Orchestration")
    print("=" * 50)

    orchestrator = get_multi_agent_orchestrator()

    # Test multiple concurrent tasks
    tasks = [
        orchestrator.orchestrate_task(f"Analyze dataset {i}", strategy="parallel")
        for i in range(3)
    ]

    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()

    successful_tasks = sum(1 for r in results if not isinstance(r, Exception))
    failed_tasks = len(results) - successful_tasks

    print(f"✅ Concurrent orchestration completed in {end_time - start_time:.2f}s")
    print(f"📊 Results: {successful_tasks} successful, {failed_tasks} failed")

    return end_time - start_time


def test_database_concurrency():
    """Test concurrent database operations"""
    print("\\n💾 Testing Database Concurrency")
    print("=" * 50)

    db = get_database_manager()
    results = []
    errors = []

    def worker(worker_id):
        try:
            # Create user
            user_data = db.create_user(
                {
                    "username": f"concurrency_user_{worker_id}_{int(time.time())}",
                    "email": f"concurrency_{worker_id}_{int(time.time())}@test.com",
                    "password_hash": f"hash_{worker_id}",
                    "role": "user",
                }
            )
            results.append(f"Worker {worker_id}: User {user_data['id']} created")

            # Record metric
            db.record_agent_metric(f"Agent_{worker_id}", "test", True, 1.0, 50)
            results.append(f"Worker {worker_id}: Metric recorded")

        except Exception as e:
            errors.append(f"Worker {worker_id}: {str(e)}")

    # Start concurrent workers
    threads = []
    num_workers = 5

    start_time = time.time()
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for completion
    for t in threads:
        t.join()
    end_time = time.time()

    print(f"✅ Database concurrency test completed in {end_time - start_time:.2f}s")
    print(f"📊 Results: {len(results)} operations successful, {len(errors)} errors")

    if errors:
        print("❌ Errors encountered:")
        for error in errors[:3]:  # Show first 3 errors
            print(f"   {error}")

    return end_time - start_time


async def main():
    print("🚀 System Concurrency & Performance Test")
    print("=" * 60)

    # Test concurrent orchestration
    orch_time = await test_concurrent_orchestration()

    # Test database concurrency
    db_time = test_database_concurrency()

    # Performance summary
    print("\\n📈 Performance Summary")
    print("=" * 50)
    print(f"🤖 Concurrent Orchestration: {orch_time:.2f}s")
    print(f"💾 Database Concurrency: {db_time:.2f}s")
    print(f"⚡ Total Test Time: {orch_time + db_time:.2f}s")

    # System health check
    print("\\n🏥 System Health Check")
    print("=" * 50)

    db = get_database_manager()
    stats = db.get_database_stats()

    print(f"👥 Total Users: {stats['users_count']}")
    print(f"💬 Total Conversations: {stats['conversations_count']}")
    print(f"📊 Total Metrics: {stats['agent_metrics_count']}")
    print(f"💾 Database Size: {stats['db_size_mb']:.2f} MB")

    print("\\n🎉 System concurrency and performance test completed!")


if __name__ == "__main__":
    asyncio.run(main())
