#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test VSCode diff integration with edit_file tool

Verifies that edit_file properly integrates with VSCode diff preview
when the feature is enabled.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool


def test_vscode_diff_preview_enabled():
    """
    Test that edit_file shows diff in VSCode when feature is enabled
    """
    print("=" * 70)
    print("Test: VSCode diff preview enabled")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        original_content = "def hello():\n    print('Hello')\n    return 42\n"
        test_file.write_text(original_content)

        # Mock VSCode mode and feature flags
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled') as mock_feature, \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Enable the feature
            def feature_enabled(feature_name):
                return feature_name == "ide_integration.show_diff_before_edit"
            mock_feature.side_effect = feature_enabled

            # Mock show_diff to return success
            mock_show_diff.return_value = {'success': True, 'message': 'Diff shown'}

            # Execute edit
            tool = EditFileTool(project_root=project_root)
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="    print('Goodbye')",
                confirm=False
            )

            # Verify edit was successful
            assert result['success'] is True
            print("✓ Edit completed successfully")

            # Verify show_diff was called
            assert mock_show_diff.called, "show_diff should have been called"
            print("✓ VSCode show_diff was called")

            # Verify show_diff was called with correct parameters
            call_args = mock_show_diff.call_args
            assert call_args is not None
            args, kwargs = call_args

            # Check title contains file name and line range
            title = kwargs.get('title') or args[0]
            assert 'test.py' in title
            assert '2-2' in title
            print(f"✓ Diff title: {title}")

            # Check original_path
            original_path = kwargs.get('original_path') or args[1]
            assert str(test_file) in original_path
            print(f"✓ Original path: {original_path}")

            # Check modified_content contains the new line
            modified_content = kwargs.get('modified_content') or args[2]
            assert "print('Goodbye')" in modified_content
            assert "print('Hello')" not in modified_content
            print("✓ Modified content is correct")

            # Verify file was actually modified
            final_content = test_file.read_text()
            assert "print('Goodbye')" in final_content
            print("✓ File was modified on disk")

    print("\n✅ Test PASSED\n")


def test_vscode_diff_preview_disabled():
    """
    Test that edit_file works normally when feature is disabled
    """
    print("=" * 70)
    print("Test: VSCode diff preview disabled")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        # Mock VSCode mode but disable feature
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled', return_value=False), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Execute edit
            tool = EditFileTool(project_root=project_root)
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="LINE TWO",
                confirm=False
            )

            # Verify edit was successful
            assert result['success'] is True
            print("✓ Edit completed successfully")

            # Verify show_diff was NOT called
            assert not mock_show_diff.called, "show_diff should NOT have been called when feature is disabled"
            print("✓ VSCode show_diff was NOT called (feature disabled)")

            # Verify file was modified
            content = test_file.read_text()
            assert "LINE TWO" in content
            print("✓ File was modified on disk")

    print("\n✅ Test PASSED\n")


def test_vscode_diff_preview_non_vscode_mode():
    """
    Test that edit_file works normally when not in VSCode mode
    """
    print("=" * 70)
    print("Test: Non-VSCode mode (CLI standalone)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        # Mock non-VSCode mode
        with patch('backend.rpc.client.is_vscode_mode', return_value=False), \
             patch('backend.feature.is_feature_enabled', return_value=True), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Execute edit
            tool = EditFileTool(project_root=project_root)
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="LINE TWO",
                confirm=False
            )

            # Verify edit was successful
            assert result['success'] is True
            print("✓ Edit completed successfully")

            # Verify show_diff was NOT called
            assert not mock_show_diff.called, "show_diff should NOT have been called in non-VSCode mode"
            print("✓ VSCode show_diff was NOT called (non-VSCode mode)")

            # Verify file was modified
            content = test_file.read_text()
            assert "LINE TWO" in content
            print("✓ File was modified on disk")

    print("\n✅ Test PASSED\n")


def test_vscode_diff_preview_error_handling():
    """
    Test that edit_file continues even if VSCode diff preview fails
    """
    print("=" * 70)
    print("Test: VSCode diff preview error handling")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        # Mock VSCode mode with show_diff raising an error
        with patch('backend.rpc.client.is_vscode_mode', return_value=True), \
             patch('backend.feature.is_feature_enabled', return_value=True), \
             patch('backend.tools.vscode_tools.vscode.show_diff') as mock_show_diff:

            # Make show_diff raise an exception
            mock_show_diff.side_effect = Exception("VSCode RPC error")

            # Execute edit - should succeed despite VSCode error
            tool = EditFileTool(project_root=project_root)
            result = tool.execute(
                path=str(test_file),
                line_range=[2, 2],
                new_content="LINE TWO",
                confirm=False
            )

            # Verify edit was successful despite VSCode error
            assert result['success'] is True
            print("✓ Edit completed successfully despite VSCode error")

            # Verify show_diff was called but failed
            assert mock_show_diff.called
            print("✓ VSCode show_diff was called but failed gracefully")

            # Verify file was still modified
            content = test_file.read_text()
            assert "LINE TWO" in content
            print("✓ File was modified on disk (edit_file is resilient)")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing VSCode Diff Integration with edit_file")
    print("=" * 70 + "\n")

    try:
        test_vscode_diff_preview_enabled()
        test_vscode_diff_preview_disabled()
        test_vscode_diff_preview_non_vscode_mode()
        test_vscode_diff_preview_error_handling()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - VSCode diff integration working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ VSCode diff preview shows when feature is enabled")
        print("  ✓ Diff preview is skipped when feature is disabled")
        print("  ✓ Diff preview is skipped in non-VSCode mode")
        print("  ✓ Edit continues even if diff preview fails (resilient)")
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
