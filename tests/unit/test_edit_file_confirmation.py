#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test confirmation integration between ToolConfirmation and edit_file

Tests the confirmation flow with exact string replacement (Claude Code style):
1. First-time edit_file: ToolConfirmation layer (1 confirmation)
2. After "always allow": No confirmation needed
3. Smart parameter adaptation in RegistryToolExecutor
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools.confirmation import ToolConfirmation, ConfirmAction, ConfirmResult
from backend.agent.tools.executor import RegistryToolExecutor
from backend.agent.tools.registry import ToolRegistry


def test_confirmation_first_time():
    """
    Test 1: First-time edit_file execution
    Expected: Confirmation layer should be engaged
    """
    print("=" * 70)
    print("Test 1: First-time edit_file (needs confirmation)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('line one\nline two\nline three\n')

        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        def mock_callback_deny(tool_name, category, arguments):
            print(f"  [Layer 1] ToolConfirmation asked for: {tool_name}")
            return ConfirmAction.DENY

        confirmation.set_confirmation_callback(mock_callback_deny)

        # First time should need confirmation
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(test_file),
            'old_str': 'line two',
            'new_str': 'line TWO'
        })
        print(f"✓ ToolConfirmation needs confirmation: {needs_confirm}")
        assert needs_confirm is True, "First time should need confirmation"

        print("✓ First-time edit_file requires confirmation")
        print("\n✅ Test 1 PASSED\n")


def test_confirmation_after_allow_always():
    """
    Test 2: edit_file execution after 'always allow'
    Expected: No confirmation needed
    """
    print("=" * 70)
    print("Test 2: edit_file after 'always allow' (0 confirmations)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('line one\nline two\nline three\n')

        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        def mock_callback_allow_always(tool_name, category, arguments):
            print(f"  [Layer 1] User chose ALLOW_ALWAYS for: {tool_name}")
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)

        # First execution: user allows always
        result = confirmation.confirm_tool_execution('edit_file', {
            'path': str(test_file),
            'old_str': 'line two',
            'new_str': 'line TWO'
        })
        assert result.action == ConfirmAction.ALLOW_ALWAYS
        print(f"✓ User set 'always allow' for edit_file")

        # Verify edit_file is now in allowed_tool_calls
        assert 'edit_file' in confirmation.allowed_tool_calls
        print(f"✓ edit_file added to allowed_tool_calls: {confirmation.allowed_tool_calls}")

        # Initialize tool executor WITH confirmation manager
        executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

        # Check: edit_file should NOT need confirmation now
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(test_file),
            'old_str': 'line two',
            'new_str': 'line TWO'
        })
        print(f"✓ ToolConfirmation needs confirmation: {needs_confirm}")
        assert needs_confirm is False, "Should not need confirmation after ALLOW_ALWAYS"

        # Execute edit_file through executor
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': 'line two',
            'new_str': 'line TWO'
        })

        # Verify edit was applied
        assert result['success'] is True, f"Edit failed: {result.get('error')}"
        content = test_file.read_text()
        assert 'line TWO' in content
        print(f"✓ Edit applied successfully")
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
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('line one\nline two\nline three\n')

        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        # Set up: allow edit_file always
        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)
        confirmation.confirm_tool_execution('edit_file', {
            'path': str(test_file),
            'old_str': 'line two',
            'new_str': 'line TWO'
        })

        # Create executor with confirmation manager
        executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

        # Execute multiple edits - all should work without confirmation
        edits = [
            ('line one', 'LINE ONE'),
            ('line three', 'LINE THREE'),
        ]

        for old_str, new_str in edits:
            # Reset file content for each test
            test_file.write_text('line one\nline two\nline three\n')

            result = executor.execute_tool('edit_file', {
                'path': str(test_file),
                'old_str': old_str,
                'new_str': new_str
            })

            assert result['success'] is True, f"Edit '{old_str}' -> '{new_str}' failed: {result.get('error')}"
            content = test_file.read_text()
            assert new_str in content, f"Expected '{new_str}' in content"
            print(f"✓ Edit '{old_str}' -> '{new_str}' succeeded without confirmation")

        print("\n✅ Test 3 PASSED\n")


def test_different_files_same_tool():
    """
    Test 4: Verify that 'always allow' works for different files
    """
    print("=" * 70)
    print("Test 4: Always allow works for different files")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        file1 = Path(project_root) / 'file1.txt'
        file2 = Path(project_root) / 'file2.txt'
        file1.write_text('hello world\n')
        file2.write_text('foo bar\n')

        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)
        confirmation.confirm_tool_execution('edit_file', {
            'path': str(file1),
            'old_str': 'hello',
            'new_str': 'HELLO'
        })

        # Signature should be 'edit_file' (not file-specific)
        print(f"✓ allowed_tool_calls: {confirmation.allowed_tool_calls}")
        assert 'edit_file' in confirmation.allowed_tool_calls

        executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

        # Edit file1 - should not need confirmation
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(file1),
            'old_str': 'hello',
            'new_str': 'HELLO'
        })
        assert needs_confirm is False, "file1 should not need confirmation"
        print(f"✓ file1: needs_confirmation={needs_confirm}")

        # Edit file2 - should also not need confirmation (same tool)
        needs_confirm = confirmation.needs_confirmation('edit_file', {
            'path': str(file2),
            'old_str': 'foo',
            'new_str': 'FOO'
        })
        assert needs_confirm is False, "file2 should also not need confirmation"
        print(f"✓ file2: needs_confirmation={needs_confirm}")

        # Actually execute edit on file2
        result = executor.execute_tool('edit_file', {
            'path': str(file2),
            'old_str': 'foo',
            'new_str': 'FOO'
        })
        assert result['success'] is True
        assert 'FOO' in file2.read_text()
        print(f"✓ file2 edited successfully without confirmation")

        print("\n✅ Test 4 PASSED\n")


def test_confirmation_reset():
    """
    Test 5: Verify reset_confirmations clears the always allow state
    """
    print("=" * 70)
    print("Test 5: Reset confirmations")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('original content\n')

        registry = ToolRegistry(project_root=project_root)
        confirmation = ToolConfirmation(tool_registry=registry)

        def mock_callback_allow_always(tool_name, category, arguments):
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback_allow_always)
        confirmation.confirm_tool_execution('edit_file', {
            'path': str(test_file),
            'old_str': 'original',
            'new_str': 'ORIGINAL'
        })

        # Should not need confirmation
        needs_confirm = confirmation.needs_confirmation('edit_file', {'path': str(test_file)})
        assert needs_confirm is False
        print(f"✓ Before reset: needs_confirmation={needs_confirm}")

        # Reset
        confirmation.reset_confirmations()
        print(f"✓ Reset confirmations")

        # Should need confirmation again
        needs_confirm = confirmation.needs_confirmation('edit_file', {'path': str(test_file)})
        assert needs_confirm is True
        print(f"✓ After reset: needs_confirmation={needs_confirm}")

        print("\n✅ Test 5 PASSED\n")


def test_session_level_confirmations():
    """
    Test 6: Verify confirmations are session-level only (no persistence)
    """
    print("=" * 70)
    print("Test 6: Session-level confirmations (no persistence)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
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


def test_exact_string_replacement():
    """
    Test 7: Exact string replacement (Claude Code style)
    """
    print("=" * 70)
    print("Test 7: Exact string replacement (Claude Code style)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        original_content = """def hello():
    print('Hello')
    return 42
"""
        test_file.write_text(original_content)

        executor = RegistryToolExecutor(project_root, confirmation_manager=None)

        # Test 1: Replace single line
        print("\n  [Test 1] Replace single line")
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': "    print('Hello')",
            'new_str': "    print('Goodbye')"
        })
        assert result['success'] is True, f"Edit failed: {result.get('error')}"
        content = test_file.read_text()
        assert "print('Goodbye')" in content
        assert "print('Hello')" not in content
        print(f"    ✓ Single line replacement successful")

        # Test 2: Replace multiple lines
        print("\n  [Test 2] Replace multiple lines")
        test_file.write_text(original_content)
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': "    print('Hello')\n    return 42",
            'new_str': "    return 'Done'"
        })
        assert result['success'] is True, f"Edit failed: {result.get('error')}"
        content = test_file.read_text()
        assert "return 'Done'" in content
        print(f"    ✓ Multi-line replacement successful")

        # Test 3: Replace with multiple lines
        print("\n  [Test 3] Replace one line with multiple lines")
        test_file.write_text("line1\nline2\nline3\n")
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': 'line1',
            'new_str': "new line 1\nnew line 2"
        })
        assert result['success'] is True, f"Edit failed: {result.get('error')}"
        content = test_file.read_text()
        assert "new line 1\nnew line 2" in content
        print(f"    ✓ Line expansion successful")

        print("\n✅ Test 7 PASSED\n")


def test_replace_all():
    """
    Test 8: Replace all occurrences
    """
    print("=" * 70)
    print("Test 8: Replace all occurrences")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.txt'
        test_file.write_text('foo bar foo baz foo\n')

        executor = RegistryToolExecutor(project_root, confirmation_manager=None)

        # Replace all 'foo' with 'FOO'
        result = executor.execute_tool('edit_file', {
            'path': str(test_file),
            'old_str': 'foo',
            'new_str': 'FOO',
            'replace_all': True
        })
        assert result['success'] is True, f"Edit failed: {result.get('error')}"
        content = test_file.read_text()
        assert content == 'FOO bar FOO baz FOO\n'
        assert 'foo' not in content
        print(f"✓ Replaced all occurrences: {content.strip()}")

        print("\n✅ Test 8 PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing Confirmation Integration (Exact String Replacement)")
    print("=" * 70 + "\n")

    try:
        test_confirmation_first_time()
        test_confirmation_after_allow_always()
        test_smart_parameter_adaptation()
        test_different_files_same_tool()
        test_confirmation_reset()
        test_session_level_confirmations()
        test_exact_string_replacement()
        test_replace_all()

        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70 + "\n")

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
