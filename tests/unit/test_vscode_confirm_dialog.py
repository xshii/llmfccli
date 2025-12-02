#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test VSCode confirmation dialog integration with edit_file

Tests the flow:
1. edit_file shows diff in VSCode
2. Displays confirmation dialog
3. Applies changes only if user confirms
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool, FileSystemError


def test_confirm_dialog_approved():
    """
    Test that edit is applied when user confirms
    """
    print("=" * 70)
    print("Test: Edit applied when user confirms")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        # Mock VSCode mode and feature flags
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled') as mock_feature, \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff, \
             patch('backend.tools.vscode_tools.vscode.confirm_dialog', return_value=True) as mock_confirm:

            # Enable both features
            def feature_enabled(key):
                return key in ['ide_integration.show_diff_before_edit', 'ide_integration.require_user_confirm']
            mock_feature.side_effect = feature_enabled

            # Execute edit
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="MODIFIED_LINE2",
                confirm=False
            )

            # Verify workflow
            assert mock_show_diff.called, "show_diff should be called"
            assert mock_confirm.called, "confirm_dialog should be called"

            # Verify dialog message
            dialog_message = mock_confirm.call_args[1]['message']
            assert "test.py" in dialog_message
            assert "lines 2-2" in dialog_message

            # Verify edit was applied
            assert result['success'] is True
            final_content = test_file.read_text()
            assert final_content == "line1\nMODIFIED_LINE2\nline3\n"

            print("✓ show_diff was called")
            print("✓ confirm_dialog was called")
            print(f"✓ Dialog message: {dialog_message}")
            print("✓ Edit was applied")

    print("\n✅ Test PASSED\n")


def test_confirm_dialog_rejected():
    """
    Test that edit is cancelled when user rejects
    """
    print("=" * 70)
    print("Test: Edit cancelled when user rejects")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        tool = EditFileTool(project_root=project_root)

        # Mock VSCode mode and feature flags
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled') as mock_feature, \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff, \
             patch('backend.tools.vscode_tools.vscode.confirm_dialog', return_value=False) as mock_confirm:

            # Enable both features
            def feature_enabled(key):
                return key in ['ide_integration.show_diff_before_edit', 'ide_integration.require_user_confirm']
            mock_feature.side_effect = feature_enabled

            # Execute edit (should raise error)
            try:
                result = tool.execute(
                    path=str(test_file),
                    line_range=[2, 2],
                    new_content="MODIFIED_LINE2",
                    confirm=False
                )
                assert False, "Should have raised FileSystemError"
            except FileSystemError as e:
                assert "cancelled by user" in str(e)
                print(f"✓ Edit cancelled with error: {e}")

            # Verify workflow
            assert mock_show_diff.called, "show_diff should be called"
            assert mock_confirm.called, "confirm_dialog should be called"

            # Verify edit was NOT applied (file unchanged)
            final_content = test_file.read_text()
            assert final_content == original_content

            print("✓ show_diff was called")
            print("✓ confirm_dialog was called (returned False)")
            print("✓ File was NOT modified (unchanged)")

    print("\n✅ Test PASSED\n")


def test_confirm_dialog_disabled():
    """
    Test that edit is applied immediately when confirmation is disabled
    """
    print("=" * 70)
    print("Test: Edit applied immediately when confirmation disabled")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        # Mock VSCode mode and feature flags
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled') as mock_feature, \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff, \
             patch('backend.tools.vscode_tools.vscode.confirm_dialog') as mock_confirm:

            # Enable only show_diff, not require_user_confirm
            def feature_enabled(key):
                return key == 'ide_integration.show_diff_before_edit'
            mock_feature.side_effect = feature_enabled

            # Execute edit
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="MODIFIED_LINE2",
                confirm=False
            )

            # Verify workflow
            assert mock_show_diff.called, "show_diff should be called"
            assert not mock_confirm.called, "confirm_dialog should NOT be called"

            # Verify edit was applied
            assert result['success'] is True
            final_content = test_file.read_text()
            assert final_content == "line1\nMODIFIED_LINE2\nline3\n"

            print("✓ show_diff was called")
            print("✓ confirm_dialog was NOT called (feature disabled)")
            print("✓ Edit was applied immediately")

    print("\n✅ Test PASSED\n")


def test_confirm_dialog_rpc_failure():
    """
    Test that edit is cancelled if RPC fails (safe fallback)
    """
    print("=" * 70)
    print("Test: Edit cancelled if RPC fails")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        tool = EditFileTool(project_root=project_root)

        # Mock VSCode mode and feature flags
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled') as mock_feature, \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff, \
             patch('backend.rpc.client.send_vscode_request') as mock_rpc:

            # Enable both features
            def feature_enabled(key):
                return key in ['ide_integration.show_diff_before_edit', 'ide_integration.require_user_confirm']
            mock_feature.side_effect = feature_enabled

            # Simulate RPC failure for confirmDialog
            def rpc_side_effect(method, params, timeout=10.0):
                if method == "confirmDialog":
                    raise Exception("RPC connection failed")
                return {"success": True}
            mock_rpc.side_effect = rpc_side_effect

            # Execute edit (should raise error due to RPC failure)
            try:
                result = tool.execute(
                    path=str(test_file),
                    line_range=[2, 2],
                    new_content="MODIFIED_LINE2",
                    confirm=False
                )
                assert False, "Should have raised FileSystemError"
            except FileSystemError as e:
                assert "cancelled by user" in str(e)
                print(f"✓ Edit cancelled with error: {e}")

            # Verify file was NOT modified
            final_content = test_file.read_text()
            assert final_content == original_content
            print("✓ File was NOT modified (safe fallback)")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing VSCode Confirmation Dialog Integration")
    print("=" * 70 + "\n")

    try:
        test_confirm_dialog_approved()
        test_confirm_dialog_rejected()
        test_confirm_dialog_disabled()
        test_confirm_dialog_rpc_failure()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Confirmation dialog working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ Edit applied when user confirms")
        print("  ✓ Edit cancelled when user rejects")
        print("  ✓ Edit applied immediately when confirmation disabled")
        print("  ✓ Edit cancelled safely if RPC fails")
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
