#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test diff preview during confirmation stage

Verifies that edit_file shows diff preview BEFORE user confirms,
not after confirmation.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool
from backend.agent.tools.confirmation import ToolConfirmation, ConfirmAction
from backend.agent.tools.registry import ToolRegistry


def test_diff_shown_during_confirmation():
    """
    Test that diff is shown during confirmation (before execute)
    """
    print("=" * 70)
    print("Test: Diff shown during confirmation stage")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        # Create tool registry (auto-discovers tools)
        registry = ToolRegistry(project_root=project_root)

        # Create confirmation manager with registry
        confirmation = ToolConfirmation(tool_registry=registry)

        # Mock VSCode mode and feature flags
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled', return_value=True), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Mock confirmation callback
            def mock_confirm_callback(tool_name, category, arguments):
                # At this point, show_diff should already have been called
                assert mock_show_diff.called, "show_diff should be called BEFORE asking user"
                print("✓ show_diff was called BEFORE user confirmation")
                return ConfirmAction.ALLOW_ONCE

            confirmation.set_confirmation_callback(mock_confirm_callback)

            # Trigger confirmation (this should call get_diff_preview)
            action = confirmation.confirm_tool_execution(
                'edit_file',
                {
                    'path': str(test_file),
                    'line_range': [2, 2],
                    'new_content': 'MODIFIED_LINE2'
                }
            )

            assert action == ConfirmAction.ALLOW_ONCE
            assert mock_show_diff.called, "show_diff should have been called"

            # Verify diff preview was shown
            show_diff_call = mock_show_diff.call_args
            assert "Preview:" in show_diff_call[1]['title']
            print(f"✓ Diff title: {show_diff_call[1]['title']}")
            print("✓ User saw diff BEFORE confirming")

    print("\n✅ Test PASSED\n")


def test_execute_without_duplicate_diff():
    """
    Test that execute() doesn't show diff again (already shown during confirmation)
    """
    print("=" * 70)
    print("Test: execute() doesn't duplicate diff")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled', return_value=True), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Call execute directly (simulating post-confirmation)
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="MODIFIED_LINE2",
                confirm=False
            )

            # execute() should NOT call show_diff
            assert not mock_show_diff.called, "execute() should NOT show diff (already shown during confirmation)"
            print("✓ execute() did NOT call show_diff (no duplication)")

            # Verify file was modified
            assert result['success'] is True
            final_content = test_file.read_text()
            assert "MODIFIED_LINE2" in final_content
            print("✓ File was modified successfully")

    print("\n✅ Test PASSED\n")


def test_preview_disabled_in_non_vscode_mode():
    """
    Test that preview is skipped in non-VSCode mode
    """
    print("=" * 70)
    print("Test: Preview skipped in non-VSCode mode")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        with patch('backend.rpc.client.is_vscode_mode', return_value=False), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Call get_diff_preview
            tool.get_diff_preview(
                path=str(test_file),
                line_range=[2, 2],
                new_content="MODIFIED"
            )

            # show_diff should NOT be called in non-VSCode mode
            assert not mock_show_diff.called, "show_diff should be skipped in non-VSCode mode"
            print("✓ show_diff was skipped (non-VSCode mode)")

    print("\n✅ Test PASSED\n")


def test_preview_with_invalid_range():
    """
    Test that preview handles invalid range gracefully
    """
    print("=" * 70)
    print("Test: Preview handles invalid range gracefully")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled', return_value=True), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Call with invalid range (end < start)
            tool.get_diff_preview(
                path=str(test_file),
                line_range=[2, 1],  # Invalid: end < start
                new_content="MODIFIED"
            )

            # show_diff should NOT be called for invalid range
            assert not mock_show_diff.called, "show_diff should be skipped for invalid range"
            print("✓ Invalid range handled gracefully (no crash)")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing Diff Preview During Confirmation")
    print("=" * 70 + "\n")

    try:
        test_diff_shown_during_confirmation()
        test_execute_without_duplicate_diff()
        test_preview_disabled_in_non_vscode_mode()
        test_preview_with_invalid_range()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Diff preview at confirmation working!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ Diff shown BEFORE user confirms (not after)")
        print("  ✓ execute() doesn't duplicate diff")
        print("  ✓ Preview skipped in non-VSCode mode")
        print("  ✓ Invalid ranges handled gracefully")
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
