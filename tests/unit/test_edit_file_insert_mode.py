#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test INSERT MODE for edit_file tool

Verifies that edit_file properly handles INSERT MODE when line_range
has end_line < start_line (e.g., [3, 2] means insert after line 2).
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool


def test_insert_after_line():
    """
    Test inserting content after a specific line
    """
    print("=" * 70)
    print("Test: Insert after line 2 using line_range=[3, 2]")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file with 5 lines
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\nline4\nline5\n"
        test_file.write_text(original_content)

        # Insert after line 2 (between line 2 and line 3)
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[3, 2],  # INSERT MODE: insert after line 2
            new_content="inserted_line",
            confirm=False
        )

        # Verify result
        assert result['success'] is True
        assert result['operation_mode'] == 'insert'
        assert result['old_line_count'] == 0  # No lines removed
        assert result['new_line_count'] == 1  # 1 line inserted
        print(f"✓ Result: {result['message']}")
        print(f"✓ Operation mode: {result['operation_mode']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nline2\ninserted_line\nline3\nline4\nline5\n"
        assert final_content == expected_content, f"Expected:\n{expected_content}\n\nGot:\n{final_content}"
        print("✓ File content is correct")
        print(f"  Line 1: line1")
        print(f"  Line 2: line2")
        print(f"  Line 3: inserted_line (NEW)")
        print(f"  Line 4: line3")
        print(f"  Line 5: line4")
        print(f"  Line 6: line5")

    print("\n✅ Test PASSED\n")


def test_insert_at_beginning():
    """
    Test inserting content at the beginning of file
    """
    print("=" * 70)
    print("Test: Insert at beginning using line_range=[1, 0]")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        # Insert at beginning
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[1, 0],  # INSERT MODE: insert at beginning
            new_content="header_line",
            confirm=False
        )

        # Verify result
        assert result['success'] is True
        assert result['operation_mode'] == 'insert'
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "header_line\nline1\nline2\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct")
        print(f"  Line 1: header_line (NEW)")
        print(f"  Line 2: line1")
        print(f"  Line 3: line2")
        print(f"  Line 4: line3")

    print("\n✅ Test PASSED\n")


def test_insert_at_end():
    """
    Test inserting content at the end of file
    """
    print("=" * 70)
    print("Test: Insert at end using line_range=[4, 3]")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file with 3 lines
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        # Insert after line 3 (at the end)
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[4, 3],  # INSERT MODE: insert after line 3
            new_content="footer_line",
            confirm=False
        )

        # Verify result
        assert result['success'] is True
        assert result['operation_mode'] == 'insert'
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nline2\nline3\nfooter_line\n"
        assert final_content == expected_content
        print("✓ File content is correct")
        print(f"  Line 1: line1")
        print(f"  Line 2: line2")
        print(f"  Line 3: line3")
        print(f"  Line 4: footer_line (NEW)")

    print("\n✅ Test PASSED\n")


def test_insert_multiple_lines():
    """
    Test inserting multiple lines
    """
    print("=" * 70)
    print("Test: Insert multiple lines after line 1")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        # Insert multiple lines after line 1
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 1],  # INSERT MODE: insert after line 1
            new_content="new_line_a\nnew_line_b\nnew_line_c",
            confirm=False
        )

        # Verify result
        assert result['success'] is True
        assert result['operation_mode'] == 'insert'
        assert result['new_line_count'] == 3
        print(f"✓ Result: {result['message']}")
        print(f"✓ Inserted {result['new_line_count']} lines")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nnew_line_a\nnew_line_b\nnew_line_c\nline2\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_replace_mode_still_works():
    """
    Test that normal REPLACE MODE still works correctly
    """
    print("=" * 70)
    print("Test: REPLACE MODE (line_range=[2, 3]) still works")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\nline4\n"
        test_file.write_text(original_content)

        # Replace lines 2-3
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 3],  # REPLACE MODE
            new_content="replaced_line",
            confirm=False
        )

        # Verify result
        assert result['success'] is True
        assert result['operation_mode'] == 'replace'
        assert result['old_line_count'] == 2  # Replaced 2 lines
        assert result['new_line_count'] == 1  # With 1 line
        print(f"✓ Result: {result['message']}")
        print(f"✓ Operation mode: {result['operation_mode']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nreplaced_line\nline4\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_replace_single_line():
    """
    Test replacing a single line with REPLACE MODE
    """
    print("=" * 70)
    print("Test: REPLACE single line using line_range=[2, 2]")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file
        test_file = Path(project_root) / 'test.py'
        original_content = "line1\nline2\nline3\n"
        test_file.write_text(original_content)

        # Replace line 2 only
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],  # REPLACE MODE: replace line 2
            new_content="modified_line2",
            confirm=False
        )

        # Verify result
        assert result['success'] is True
        assert result['operation_mode'] == 'replace'
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "line1\nmodified_line2\nline3\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_insert_error_cases():
    """
    Test error handling for INSERT MODE
    """
    print("=" * 70)
    print("Test: INSERT MODE error cases")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        # Create test file with 3 lines
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        # Test 1: Insert position exceeds file length
        try:
            result = tool.execute(
                path=str(test_file),
                line_range=[10, 9],  # Insert after line 9, but file only has 3 lines
                new_content="new_line",
                confirm=False
            )
            assert False, "Should have raised an error"
        except Exception as e:
            assert "exceeds file length" in str(e)
            print(f"✓ Correctly rejected insert beyond file length: {e}")

        # Test 2: Negative insert position
        try:
            result = tool.execute(
                path=str(test_file),
                line_range=[1, -1],  # Invalid: negative position
                new_content="new_line",
                confirm=False
            )
            assert False, "Should have raised an error"
        except Exception as e:
            assert "must be >= 0" in str(e)
            print(f"✓ Correctly rejected negative insert position: {e}")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing INSERT MODE for edit_file")
    print("=" * 70 + "\n")

    try:
        test_insert_after_line()
        test_insert_at_beginning()
        test_insert_at_end()
        test_insert_multiple_lines()
        test_replace_mode_still_works()
        test_replace_single_line()
        test_insert_error_cases()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - INSERT MODE working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ Insert after specific line works")
        print("  ✓ Insert at beginning works")
        print("  ✓ Insert at end works")
        print("  ✓ Insert multiple lines works")
        print("  ✓ REPLACE MODE still works correctly")
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
