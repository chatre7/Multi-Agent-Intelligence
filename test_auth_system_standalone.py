#!/usr/bin/env python3
"""Test Authentication System"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_system import get_auth_manager, get_rbac_manager
import uuid


def test_authentication():
    print("🔐 Testing Authentication System")
    print("=" * 50)

    # Test auth manager initialization
    auth_manager = get_auth_manager()
    rbac_manager = get_rbac_manager()
    print("✅ Auth managers initialized")

    # Test user registration
    print("\\n📝 Testing User Registration...")
    try:
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        password = "testpassword123"

        user_id = auth_manager.create_user(
            username=username,
            email=email,
            password=password,
            full_name="Test User",
            role="user",
        )
        print(f"✅ User registered: {username}")
    except Exception as e:
        print(f"⚠️ User registration failed: {e}")
        return

    # Test user login
    print("\\n🔑 Testing User Login...")
    try:
        authenticated_user = auth_manager.authenticate_user(username, password)
        print(f"✅ User authenticated: {authenticated_user['username']}")

        # Generate token
        token = auth_manager.generate_token(user_id)
        print(f"✅ Token generated: {token[:50]}...")
    except Exception as e:
        print(f"⚠️ User login failed: {e}")

    # Test token validation
    print("\\n✅ Testing Token Validation...")
    try:
        if "token" in locals():
            user_data = auth_manager.validate_token(token)
            print(f"✅ Token validated for user: {user_data['username']}")
        else:
            print("⚠️ Skipping token validation (no token available)")
    except Exception as e:
        print(f"⚠️ Token validation failed: {e}")

    # Test role-based access
    print("\\n👥 Testing Role-Based Access...")
    try:
        from auth_system import UserRole, Permission
        # Get user to check role
        users = auth_manager.list_users()
        test_user = next((u for u in users if u['id'] == user_id), None)

        if test_user:
            user_role = UserRole(test_user['role'])
            has_read = rbac_manager.check_permission(user_role, Permission.AGENT_READ)
            has_admin = rbac_manager.check_permission(user_role, Permission.USER_MANAGE)

            print(f"✅ Permission checks: Read access = {has_read}, Admin access = {has_admin}")
        else:
            print("⚠️ Could not find test user for permission checks")
    except Exception as e:
        print(f"⚠️ Permission check failed: {e}")

    print("\\n🎉 Authentication system test completed!")


if __name__ == "__main__":
    test_authentication()
