#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test edit_file with explicit operation parameter
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool


def test_mode_0_replace_single_line():
    """Test operation=0: Replace single line"""
    print("=" * 70)
    print("Test: operation=0 replace single line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="REPLACED_LINE2",
            operation=0
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nREPLACED_LINE2\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_mode_0_replace_multiple_lines():
    """Test operation=0: Replace multiple lines"""
    print("=" * 70)
    print("Test: operation=0 replace multiple lines")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 4],
            new_content="NEW_A\nNEW_B",
            operation=0
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nNEW_A\nNEW_B\nline5\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_mode_1_insert_before():
    """Test operation=1: Insert before line"""
    print("=" * 70)
    print("Test: operation=1 insert before line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="import json",
            operation=1
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content - new line inserted BEFORE line2
        final_content = test_file.read_text()
        expected_content = "line1\nimport json\nline2\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct (inserted before line 2)")

    print("\n✅ Test PASSED\n")


def test_mode_2_insert_after():
    """Test operation=2: Insert after line"""
    print("=" * 70)
    print("Test: operation=2 insert after line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="import json",
            operation=2
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content - new line inserted AFTER line2
        final_content = test_file.read_text()
        expected_content = "line1\nline2\nimport json\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct (inserted after line 2)")

    print("\n✅ Test PASSED\n")


def test_mode_1_insert_at_beginning():
    """Test operation=1: Insert at beginning of file"""
    print("=" * 70)
    print("Test: operation=1 insert at beginning")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[1, 1],
            new_content="#!/usr/bin/env python3",
            operation=1
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content - inserted BEFORE line1
        final_content = test_file.read_text()
        expected_content = "#!/usr/bin/env python3\nline1\nline2\n"
        assert final_content == expected_content
        print("✓ File content is correct (inserted at beginning)")

    print("\n✅ Test PASSED\n")


def test_mode_2_insert_at_end():
    """Test operation=2: Insert at end of file"""
    print("=" * 70)
    print("Test: operation=2 insert at end")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="# End of file",
            operation=2
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content - inserted AFTER line2
        final_content = test_file.read_text()
        expected_content = "line1\nline2\n# End of file\n"
        assert final_content == expected_content
        print("✓ File content is correct (inserted at end)")

    print("\n✅ Test PASSED\n")


def test_insert_operation_ignores_end_line():
    """Test that insert operations only use start_line (end_line is ignored)"""
    print("=" * 70)
    print("Test: Insert operations ignore end_line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        # operation=1 with different end_line - should work and ignore end_line
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 99],  # end_line=99 is ignored
            new_content="inserted_before",
            operation=1
        )
        assert result['success'] is True
        print(f"✓ operation=1 with different end_line works (end_line ignored)")

        # Verify insertion happened before line 2
        final_content = test_file.read_text()
        expected_content = "line1\ninserted_before\nline2\nline3\n"
        assert final_content == expected_content
        print("✓ Correctly inserted before line 2 (start_line)")

        # Reset file for operation=2 test
        test_file.write_text("line1\nline2\nline3\n")

        # operation=2 with different end_line - should work and ignore end_line
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 99],  # end_line=99 is ignored
            new_content="inserted_after",
            operation=2
        )
        assert result['success'] is True
        print(f"✓ operation=2 with different end_line works (end_line ignored)")

        # Verify insertion happened after line 2
        final_content = test_file.read_text()
        expected_content = "line1\nline2\ninserted_after\nline3\n"
        assert final_content == expected_content
        print("✓ Correctly inserted after line 2 (start_line)")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing edit_file with operation parameter")
    print("=" * 70 + "\n")

    try:
        test_mode_0_replace_single_line()
        test_mode_0_replace_multiple_lines()
        test_mode_1_insert_before()
        test_mode_2_insert_after()
        test_mode_1_insert_at_beginning()
        test_mode_2_insert_at_end()
        test_insert_operation_ignores_end_line()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Operation parameter working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ operation=0: Replace single line works")
        print("  ✓ operation=0: Replace multiple lines works")
        print("  ✓ operation=1: Insert before line works")
        print("  ✓ operation=2: Insert after line works")
        print("  ✓ operation=1: Insert at beginning works")
        print("  ✓ operation=2: Insert at end works")
        print("  ✓ Insert operations correctly ignore end_line")
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
