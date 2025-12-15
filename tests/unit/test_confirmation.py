#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for tool confirmation workflow
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools.confirmation import ToolConfirmation, ConfirmAction, ConfirmResult
from backend.agent.tools.registry import ToolRegistry


def test_confirmation_basic():
    """Test basic confirmation workflow"""
    print("=" * 60)
    print("Test 1: Basic confirmation workflow")
    print("=" * 60)

    # Create confirmation instance with registry for dynamic lookup
    registry = ToolRegistry(project_root='/tmp')
    confirmation = ToolConfirmation(tool_registry=registry)

    # Test 1: First time needs confirmation
    needs_confirm = confirmation.needs_confirmation('view_file', {'path': '/test/file.cpp'})
    print(f"✓ First time 'view_file' needs confirmation: {needs_confirm}")
    assert needs_confirm is True, "First time should need confirmation"

    # Test 2: Allow always
    def mock_callback_allow_always(tool_name, category, arguments):
        return ConfirmAction.ALLOW_ALWAYS

    confirmation.set_confirmation_callback(mock_callback_allow_always)
    result = confirmation.confirm_tool_execution('view_file', {'path': '/test/file.cpp'})
    print(f"✓ User chose: {result.action}")
    assert result.action == ConfirmAction.ALLOW_ALWAYS

    # Test 3: Second time should not need confirmation
    needs_confirm = confirmation.needs_confirmation('view_file', {'path': '/test/other.cpp'})
    print(f"✓ Second time 'view_file' needs confirmation: {needs_confirm}")
    assert needs_confirm is False, "Should not need confirmation after ALLOW_ALWAYS"

    # Test 4: Reset confirmations
    confirmation.reset_confirmations()
    needs_confirm = confirmation.needs_confirmation('view_file', {'path': '/test/file.cpp'})
    print(f"✓ After reset, needs confirmation: {needs_confirm}")
    assert needs_confirm is True, "Should need confirmation after reset"

    print("\n✅ Test 1 PASSED\n")


def test_bash_run_confirmation():
    """Test bash_run specific confirmation (uses dynamic signature)"""
    print("=" * 60)
    print("Test 2: bash_run confirmation (per-command)")
    print("=" * 60)

    # Create confirmation instance with registry
    registry = ToolRegistry(project_root='/tmp')
    confirmation = ToolConfirmation(tool_registry=registry)

    # Test 1: First bash_run needs confirmation
    needs_confirm = confirmation.needs_confirmation('bash_run', {'command': 'ls -la'})
    print(f"✓ First 'bash_run ls' needs confirmation: {needs_confirm}")
    assert needs_confirm is True

    # Test 2: Allow always for 'ls'
    def mock_callback_allow_always(tool_name, category, arguments):
        return ConfirmAction.ALLOW_ALWAYS

    confirmation.set_confirmation_callback(mock_callback_allow_always)
    result = confirmation.confirm_tool_execution('bash_run', {'command': 'ls -la'})
    print(f"✓ User chose: {result.action}")

    # Test 3: 'ls' with different args should not need confirmation
    # (bash_run uses base command for signature, so bash_run:ls is allowed)
    needs_confirm = confirmation.needs_confirmation('bash_run', {'command': 'ls /tmp'})
    print(f"✓ 'bash_run ls /tmp' needs confirmation: {needs_confirm}")
    assert needs_confirm is False, "'ls' should be allowed for all arguments"

    # Test 4: Different command should still need confirmation
    needs_confirm = confirmation.needs_confirmation('bash_run', {'command': 'pwd'})
    print(f"✓ 'bash_run pwd' needs confirmation: {needs_confirm}")
    assert needs_confirm is True, "'pwd' should need confirmation"

    print("\n✅ Test 2 PASSED\n")


def test_tool_categories():
    """Test tool categorization (dynamic via registry)"""
    print("=" * 60)
    print("Test 3: Tool categorization (dynamic)")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp')
    confirmation = ToolConfirmation(tool_registry=registry)

    # Test categories - these are dynamically looked up via tool's category property
    expected_categories = {
        'view_file': 'filesystem',
        'edit_file': 'filesystem',
        'bash_run': 'executor',
        'git': 'git',
    }

    for tool_name, expected_category in expected_categories.items():
        category = confirmation.get_tool_category(tool_name)
        print(f"✓ {tool_name:15} -> {category}")
        assert category == expected_category, f"Expected {expected_category}, got {category}"

    # Unknown tool should return 'unknown'
    category = confirmation.get_tool_category('nonexistent_tool')
    print(f"✓ {'nonexistent_tool':15} -> {category}")
    assert category == 'unknown', f"Expected 'unknown', got {category}"

    print("\n✅ Test 3 PASSED\n")


def test_dangerous_operations():
    """Test dangerous operation detection (dynamic via tool methods)"""
    print("=" * 60)
    print("Test 4: Dangerous operation detection")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp')
    confirmation = ToolConfirmation(tool_registry=registry)

    # Test git dangerous operations
    dangerous_cases = [
        ('git', {'action': 'push', 'args': {'force': True}}, True, "git push --force"),
        ('git', {'action': 'push', 'args': {}}, False, "git push (normal)"),
        ('git', {'action': 'reset', 'args': {'mode': 'hard'}}, True, "git reset --hard"),
        ('git', {'action': 'status', 'args': {}}, False, "git status"),
        ('bash_run', {'command': 'rm -rf /'}, True, "bash rm -rf /"),
        ('bash_run', {'command': 'ls -la'}, False, "bash ls -la"),
    ]

    for tool_name, args, expected_dangerous, description in dangerous_cases:
        is_dangerous = confirmation.is_dangerous_operation(tool_name, args)
        status = "✓" if is_dangerous == expected_dangerous else "✗"
        print(f"{status} {description}: is_dangerous={is_dangerous} (expected {expected_dangerous})")
        assert is_dangerous == expected_dangerous, f"Expected {expected_dangerous} for {description}"

    print("\n✅ Test 4 PASSED\n")


def test_session_level_only():
    """Test that confirmations are session-level only (no file persistence)"""
    print("=" * 60)
    print("Test 5: Session-level confirmations")
    print("=" * 60)

    # Create first instance
    registry = ToolRegistry(project_root='/tmp')
    confirmation1 = ToolConfirmation(tool_registry=registry)

    def mock_callback_allow_always(tool_name, category, arguments):
        return ConfirmAction.ALLOW_ALWAYS

    confirmation1.set_confirmation_callback(mock_callback_allow_always)
    confirmation1.confirm_tool_execution('view_file', {'path': '/test/file.cpp'})
    print(f"✓ Confirmed 'view_file' with ALLOW_ALWAYS in session 1")

    # Session 1 should not need confirmation
    needs_confirm = confirmation1.needs_confirmation('view_file', {'path': '/test/other.cpp'})
    print(f"✓ Session 1: needs_confirmation={needs_confirm}")
    assert needs_confirm is False

    # Create second instance - should NOT share state (session-level only)
    confirmation2 = ToolConfirmation(tool_registry=registry)
    needs_confirm = confirmation2.needs_confirmation('view_file', {'path': '/test/other.cpp'})
    print(f"✓ Session 2 (new instance): needs_confirmation={needs_confirm}")
    assert needs_confirm is True, "New session should need confirmation"

    print("\n✅ Test 5 PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Testing Tool Confirmation System")
    print("=" * 60 + "\n")

    try:
        test_confirmation_basic()
        test_bash_run_confirmation()
        test_tool_categories()
        test_dangerous_operations()
        test_session_level_only()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
