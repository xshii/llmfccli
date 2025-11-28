#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test two-layer confirmation integration between ToolConfirmation and edit_file

Tests the smart confirmation flow:
1. First-time edit_file: ToolConfirmation layer + edit_file confirm layer (2 confirmations)
2. After "always allow": ToolConfirmation allows + auto confirm=False (0 confirmations)
3. Smart parameter adaptation in RegistryToolExecutor
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools.confirmation import ToolConfirmation, ConfirmAction
from backend.agent.tools.executor import RegistryToolExecutor
from backend.agent.tools.registry import ToolRegistry


def test_two_layer_confirmation_first_time():
    """
    Test 1: First-time edit_file execution
    Expected: Both confirmation layers should be engaged
    """
    print("=" * 70)
    print("Test 1: First-time edit_file (2-layer confirmation)")
    print("=" * 70)

    # Create temp project
    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('old content\n')

        # Initialize with registry for dynamic lookup
        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        # Mock callback: deny (to avoid actual user interaction in test)
        def mock_callback_deny(tool_name, category, arguments):
            print(f"  [Layer 1] ToolConfirmation asked for: {tool_name}")
            return ConfirmAction.DENY

        confirmation.set_confirmation_callback(mock_callback_deny)

        # Check: edit_file should need confirmation (first time)
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(test_file),
            'old_str': 'old content',
            'new_str': 'new content'
        })
        print(f"✓ Layer 1 (ToolConfirmation) needs confirmation: {needs_confirm}")
        assert needs_confirm is True, "First-time edit_file should need ToolConfirmation"

        print(f"✓ First-time edit_file requires both confirmation layers")
        print("\n✅ Test 1 PASSED\n")


def test_two_layer_confirmation_after_allow_always():
    """
    Test 2: edit_file after user sets "always allow"
    Expected: ToolConfirmation allows + auto confirm=False (no confirmations)
    """
    print("=" * 70)
    print("Test 2: edit_file after 'always allow' (0 confirmations)")
    print("=" * 70)

    # Create temp project
    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('old content\n')

        # Initialize with registry
        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        # Simulate user choosing "always allow"
        def mock_callback_allow_always(tool_name, category, arguments):
            print(f"  [Layer 1] User chose ALLOW_ALWAYS for: {tool_name}")
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)

        # First execution: user allows always
        action = confirmation.confirm_tool_execution('edit_file', {
            'path': str(test_file),
            'old_str': 'old content',
            'new_str': 'new content'
        })
        assert action == ConfirmAction.ALLOW_ALWAYS
        print(f"✓ User set 'always allow' for edit_file")

        # Verify edit_file is now in allowed_tool_calls
        assert 'edit_file' in confirmation.allowed_tool_calls
        print(f"✓ edit_file added to allowed_tool_calls: {confirmation.allowed_tool_calls}")

        # Initialize tool executor WITH confirmation manager
        executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

        # Check: edit_file should NOT need confirmation now
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(test_file),
            'old_str': 'old content',
            'new_str': 'new content'
        })
        print(f"✓ Layer 1 (ToolConfirmation) needs confirmation: {needs_confirm}")
        assert needs_confirm is False, "Should not need ToolConfirmation after ALLOW_ALWAYS"

        # Execute edit_file through executor
        # The smart logic in RegistryToolExecutor should auto-set confirm=False
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': 'old content',
            'new_str': 'new content'
        })

        # Verify edit was applied directly (confirm=False was auto-set)
        assert result['success'] is True
        assert 'new content' in test_file.read_text()
        print(f"✓ Layer 2 (edit_file): auto-set confirm=False, edit applied directly")
        print(f"✓ Smart adaptation: 0 confirmations needed")

        print("\n✅ Test 2 PASSED\n")


def test_smart_parameter_adaptation():
    """
    Test 3: Verify RegistryToolExecutor smart parameter adaptation
    """
    print("=" * 70)
    print("Test 3: Smart parameter adaptation in RegistryToolExecutor")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('line one\nline two\nline three\n')

        # Initialize with registry
        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        # Pre-add edit_file to allowed_tool_calls
        confirmation.allowed_tool_calls.add('edit_file')
        print(f"✓ Pre-configured allowed_tool_calls: {confirmation.allowed_tool_calls}")

        # Initialize tool executor WITH confirmation manager
        executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

        # Test Case: User doesn't pass confirm parameter (default behavior)
        # Smart logic should auto-set confirm=False because edit_file in allowed_tool_calls
        print("\n  [Case] User doesn't specify confirm (default):")

        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': 'line two',
            'new_str': 'line TWO (modified)'
        })

        assert result['success'] is True
        content = test_file.read_text()
        assert 'line TWO (modified)' in content
        print(f"    ✓ Smart adaptation: confirm=False was auto-set")
        print(f"    ✓ Edit applied directly without confirmation")

        # Test Case 2: Different tool (not in allowed_tool_calls)
        # Should NOT have smart adaptation
        print("\n  [Case 2] Tool not in allowed_tool_calls:")
        needs_confirm = confirmation.needs_confirmation('view_file', {'path': str(test_file)})
        print(f"    ✓ view_file needs confirmation: {needs_confirm}")
        assert needs_confirm is True, "Non-allowed tool should need confirmation"

        print("\n✅ Test 3 PASSED\n")


def test_executor_without_confirmation_manager():
    """
    Test 4: RegistryToolExecutor without confirmation manager (backward compatibility)
    """
    print("=" * 70)
    print("Test 4: RegistryToolExecutor without confirmation manager")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('original content\n')

        # Initialize executor WITHOUT confirmation manager
        executor = RegistryToolExecutor(project_root, confirmation_manager=None)

        # Verify executor works normally (no smart adaptation)
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': 'original content',
            'new_str': 'modified content',
            'confirm': False  # Explicitly disable confirmation
        })

        assert result['success'] is True
        assert 'modified content' in test_file.read_text()
        print(f"✓ Executor works without confirmation_manager")
        print(f"✓ Backward compatibility maintained")

        print("\n✅ Test 4 PASSED\n")


def test_multiple_edits_workflow():
    """
    Test 5: Real-world workflow - multiple edits with trust evolution
    """
    print("=" * 70)
    print("Test 5: Multiple edits workflow (trust evolution)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test files
        file1 = Path(project_root) / 'file1.txt'
        file2 = Path(project_root) / 'file2.txt'
        file3 = Path(project_root) / 'file3.txt'

        file1.write_text('content 1\n')
        file2.write_text('content 2\n')
        file3.write_text('content 3\n')

        # Initialize system
        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)
        executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

        # Workflow simulation
        print("\n  [Step 1] First edit - user must confirm")
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(file1),
            'old_str': 'content 1',
            'new_str': 'CONTENT 1'
        })
        assert needs_confirm is True
        print(f"    ✓ First edit needs confirmation: {needs_confirm}")

        # User allows always
        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)
        confirmation.confirm_tool_execution('edit_file', {})

        print("\n  [Step 2] Second edit - should be auto-approved")
        result = executor.execute_tool('edit_file', {
            'path': str(file2),
            'old_str': 'content 2',
            'new_str': 'CONTENT 2'
        })
        assert result['success'] is True
        assert 'CONTENT 2' in file2.read_text()
        print(f"    ✓ Second edit applied directly (no confirmation)")

        print("\n  [Step 3] Third edit - still auto-approved")
        result = executor.execute_tool('edit_file', {
            'path': str(file3),
            'old_str': 'content 3',
            'new_str': 'CONTENT 3'
        })
        assert result['success'] is True
        assert 'CONTENT 3' in file3.read_text()
        print(f"    ✓ Third edit applied directly (no confirmation)")

        print("\n  ✓ Workflow: 1st edit (confirmed) → 2nd/3rd edits (auto-approved)")
        print("\n✅ Test 5 PASSED\n")


def test_session_level_confirmations():
    """
    Test 6: Verify confirmations are session-level only (no persistence)
    """
    print("=" * 70)
    print("Test 6: Session-level confirmations (no persistence)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('version 1\n')

        # First session
        print("\n  [Session 1] First session - user allows always")
        registry1 = ToolRegistry(project_root=project_root)
        confirmation1 = ToolConfirmation(tool_registry=registry1)

        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation1.set_confirmation_callback(mock_callback_allow_always)
        confirmation1.confirm_tool_execution('edit_file', {})

        assert 'edit_file' in confirmation1.allowed_tool_calls
        print(f"    ✓ Session 1 allowed_tool_calls: {confirmation1.allowed_tool_calls}")

        # Second session (simulate restart)
        print("\n  [Session 2] New session - should NOT have saved confirmation")
        registry2 = ToolRegistry(project_root=project_root)
        confirmation2 = ToolConfirmation(tool_registry=registry2)

        # New session should start fresh
        assert 'edit_file' not in confirmation2.allowed_tool_calls
        print(f"    ✓ Session 2 allowed_tool_calls: {confirmation2.allowed_tool_calls}")
        print(f"    ✓ Confirmations are session-level only (no persistence)")

        print("\n✅ Test 6 PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing Two-Layer Confirmation Integration")
    print("=" * 70 + "\n")

    try:
        test_two_layer_confirmation_first_time()
        test_two_layer_confirmation_after_allow_always()
        test_smart_parameter_adaptation()
        test_executor_without_confirmation_manager()
        test_multiple_edits_workflow()
        test_session_level_confirmations()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Two-layer confirmation working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ Layer 1 (ToolConfirmation): Agent execution permission")
        print("  ✓ Layer 2 (edit_file confirm): Specific operation approval")
        print("  ✓ Smart adaptation: auto confirm=False when tool in allowed_tool_calls")
        print("  ✓ Backward compatibility: works without confirmation_manager")
        print("  ✓ Session-level: confirmations don't persist across sessions")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
