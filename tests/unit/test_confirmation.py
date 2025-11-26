#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for tool confirmation workflow
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tool_confirmation import ToolConfirmation, ConfirmAction


def test_confirmation_basic():
    """Test basic confirmation workflow"""
    print("=" * 60)
    print("Test 1: Basic confirmation workflow")
    print("=" * 60)

    # Create temporary confirmation file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name

    try:
        # Create confirmation instance
        confirmation = ToolConfirmation(confirmation_file=temp_file)

        # Test 1: First time needs confirmation
        needs_confirm = confirmation.needs_confirmation('view_file', {'path': '/test/file.cpp'})
        print(f"✓ First time 'view_file' needs confirmation: {needs_confirm}")
        assert needs_confirm is True, "First time should need confirmation"

        # Test 2: Allow always
        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)
        action = confirmation.confirm_tool_execution('view_file', {'path': '/test/file.cpp'})
        print(f"✓ User chose: {action}")
        assert action == ConfirmAction.ALLOW_ALWAYS

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

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_bash_run_confirmation():
    """Test bash_run specific confirmation"""
    print("=" * 60)
    print("Test 2: bash_run confirmation (per-command)")
    print("=" * 60)

    # Create temporary confirmation file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name

    try:
        # Create confirmation instance
        confirmation = ToolConfirmation(confirmation_file=temp_file)

        # Test 1: First bash_run needs confirmation
        needs_confirm = confirmation.needs_confirmation('bash_run', {'command': 'ls -la'})
        print(f"✓ First 'bash_run ls' needs confirmation: {needs_confirm}")
        assert needs_confirm is True

        # Test 2: Allow always for 'ls'
        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)
        action = confirmation.confirm_tool_execution('bash_run', {'command': 'ls -la'})
        print(f"✓ User chose: {action}")

        # Test 3: 'ls' with different args should not need confirmation
        needs_confirm = confirmation.needs_confirmation('bash_run', {'command': 'ls /tmp'})
        print(f"✓ 'bash_run ls /tmp' needs confirmation: {needs_confirm}")
        assert needs_confirm is False, "'ls' should be allowed for all arguments"

        # Test 4: Different command should still need confirmation
        needs_confirm = confirmation.needs_confirmation('bash_run', {'command': 'pwd'})
        print(f"✓ 'bash_run pwd' needs confirmation: {needs_confirm}")
        assert needs_confirm is True, "'pwd' should need confirmation"

        print("\n✅ Test 2 PASSED\n")

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_tool_categories():
    """Test tool categorization"""
    print("=" * 60)
    print("Test 3: Tool categorization")
    print("=" * 60)

    # Create temporary confirmation file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name

    try:
        confirmation = ToolConfirmation(confirmation_file=temp_file)

        # Test categories
        categories = {
            'view_file': 'filesystem',
            'edit_file': 'filesystem',
            'bash_run': 'executor',
            'cmake_build': 'executor',
            'parse_cpp': 'analyzer',
        }

        for tool_name, expected_category in categories.items():
            category = confirmation.get_tool_category(tool_name)
            print(f"✓ {tool_name:15} -> {category}")
            assert category == expected_category, f"Expected {expected_category}, got {category}"

        print("\n✅ Test 3 PASSED\n")

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_persistence():
    """Test confirmation persistence"""
    print("=" * 60)
    print("Test 4: Confirmation persistence")
    print("=" * 60)

    # Create temporary confirmation file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name

    try:
        # Create first instance and allow a tool
        confirmation1 = ToolConfirmation(confirmation_file=temp_file)

        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation1.set_confirmation_callback(mock_callback_allow_always)
        confirmation1.confirm_tool_execution('view_file', {'path': '/test/file.cpp'})
        print(f"✓ Confirmed 'view_file' with ALLOW_ALWAYS")

        # Create second instance - should load from file
        confirmation2 = ToolConfirmation(confirmation_file=temp_file)
        needs_confirm = confirmation2.needs_confirmation('view_file', {'path': '/test/other.cpp'})
        print(f"✓ New instance loads confirmation: needs_confirmation={needs_confirm}")
        assert needs_confirm is False, "Should load confirmation from file"

        print("\n✅ Test 4 PASSED\n")

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Testing Tool Confirmation System")
    print("=" * 60 + "\n")

    try:
        test_confirmation_basic()
        test_bash_run_confirmation()
        test_tool_categories()
        test_persistence()

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
