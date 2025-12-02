#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simplified edit_file tool

New rule: All operations use line_range=[start, end] where end >= start.
To insert without removing, include original line content in new_content.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool


def test_replace_single_line():
    """
    Test replacing a single line
    """
    print("=" * 70)
    print("Test: Replace single line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[3, 3],  # Replace line 3
            new_content="MODIFIED_LINE3",
            confirm=False
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nline2\nMODIFIED_LINE3\nline4\nline5\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_replace_multiple_lines():
    """
    Test replacing multiple lines
    """
    print("=" * 70)
    print("Test: Replace multiple lines")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 4],  # Replace lines 2-4
            new_content="NEW_LINE_A\nNEW_LINE_B",
            confirm=False
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nNEW_LINE_A\nNEW_LINE_B\nline5\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_insert_after_line():
    """
    Test inserting after a line (by including original content)
    """
    print("=" * 70)
    print("Test: Insert after line 2 (include original line 2)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        # To insert after line 2, replace line 2 with "line2\nNEW_LINE"
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],  # Operate on line 2
            new_content="line2\nINSERTED_LINE",  # Include original line 2 + new line
            confirm=False
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nline2\nINSERTED_LINE\nline3\nline4\nline5\n"
        assert final_content == expected_content
        print("✓ File content is correct")
        print("✓ Line 2 preserved, new line inserted after it")

    print("\n✅ Test PASSED\n")


def test_insert_at_beginning():
    """
    Test inserting at the beginning of file
    """
    print("=" * 70)
    print("Test: Insert at beginning (include original line 1)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        # To insert at beginning, replace line 1 with "HEADER\nline1"
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[1, 1],  # Operate on line 1
            new_content="HEADER_LINE\nline1",  # New line + original line 1
            confirm=False
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "HEADER_LINE\nline1\nline2\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_insert_at_end():
    """
    Test inserting at the end of file
    """
    print("=" * 70)
    print("Test: Insert at end (include original last line)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        # To insert at end, replace line 3 with "line3\nFOOTER"
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[3, 3],  # Operate on line 3
            new_content="line3\nFOOTER_LINE",  # Original line 3 + new line
            confirm=False
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nline2\nline3\nFOOTER_LINE\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_add_import_statement():
    """
    Real-world example: Add import statement after existing imports
    """
    print("=" * 70)
    print("Test: Add import statement (real-world example)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'app.py'
        test_file.write_text("import os\nimport sys\n\ndef main():\n    pass\n")

        # Add "import json" after "import sys"
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],  # Operate on line 2
            new_content="import sys\nimport json",  # Original + new import
            confirm=False
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "import os\nimport sys\nimport json\n\ndef main():\n    pass\n"
        assert final_content == expected_content
        print("✓ File content is correct")
        print("✓ Import added correctly")

    print("\n✅ Test PASSED\n")


def test_error_invalid_range():
    """
    Test error handling for invalid line range
    """
    print("=" * 70)
    print("Test: Error handling for invalid line range")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        # Test 1: end_line exceeds file length
        try:
            result = tool.execute(
                path=str(test_file),
                line_range=[1, 10],  # File only has 3 lines
                new_content="new_content",
                confirm=False
            )
            assert False, "Should have raised an error"
        except Exception as e:
            assert "exceeds file length" in str(e)
            print(f"✓ Correctly rejected out-of-bounds range: {e}")

        # Test 2: end < start (no longer allowed)
        try:
            result = tool.execute(
                path=str(test_file),
                line_range=[3, 2],  # end < start
                new_content="new_content",
                confirm=False
            )
            assert False, "Should have raised an error"
        except Exception as e:
            error_msg = str(e)
            # Validator error may be wrapped in ValidationError
            assert "must be >=" in error_msg or "end_line" in error_msg
            print(f"✓ Correctly rejected end < start: {e}")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing Simplified edit_file Tool")
    print("=" * 70 + "\n")

    try:
        test_replace_single_line()
        test_replace_multiple_lines()
        test_insert_after_line()
        test_insert_at_beginning()
        test_insert_at_end()
        test_add_import_statement()
        test_error_invalid_range()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Simplified edit_file working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ Replace single line works")
        print("  ✓ Replace multiple lines works")
        print("  ✓ Insert after line works (by including original content)")
        print("  ✓ Insert at beginning works")
        print("  ✓ Insert at end works")
        print("  ✓ Real-world import example works")
        print("  ✓ Error handling works")
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
