#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test edit_file with explicit mode parameter
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool


def test_mode_0_replace_single_line():
    """Test mode=0: Replace single line"""
    print("=" * 70)
    print("Test: mode=0 replace single line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="REPLACED_LINE2",
            mode=0
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
    """Test mode=0: Replace multiple lines"""
    print("=" * 70)
    print("Test: mode=0 replace multiple lines")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 4],
            new_content="NEW_A\nNEW_B",
            mode=0
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
    """Test mode=1: Insert before line"""
    print("=" * 70)
    print("Test: mode=1 insert before line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="import json",
            mode=1
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
    """Test mode=2: Insert after line"""
    print("=" * 70)
    print("Test: mode=2 insert after line")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="import json",
            mode=2
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
    """Test mode=1: Insert at beginning of file"""
    print("=" * 70)
    print("Test: mode=1 insert at beginning")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[1, 1],
            new_content="#!/usr/bin/env python3",
            mode=1
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
    """Test mode=2: Insert at end of file"""
    print("=" * 70)
    print("Test: mode=2 insert at end")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            line_range=[2, 2],
            new_content="# End of file",
            mode=2
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content - inserted AFTER line2
        final_content = test_file.read_text()
        expected_content = "line1\nline2\n# End of file\n"
        assert final_content == expected_content
        print("✓ File content is correct (inserted at end)")

    print("\n✅ Test PASSED\n")


def test_insert_mode_validation():
    """Test that insert modes require single line"""
    print("=" * 70)
    print("Test: Insert modes validation")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("line1\nline2\nline3\n")

        tool = EditFileTool(project_root=project_root)

        # mode=1 with range should fail
        try:
            tool.execute(
                path=str(test_file),
                line_range=[2, 3],
                new_content="new",
                mode=1
            )
            assert False, "Should have raised error"
        except Exception as e:
            assert "Insert mode requires single line" in str(e)
            print(f"✓ Correctly rejected mode=1 with range: {e}")

        # mode=2 with range should fail
        try:
            tool.execute(
                path=str(test_file),
                line_range=[2, 3],
                new_content="new",
                mode=2
            )
            assert False, "Should have raised error"
        except Exception as e:
            assert "Insert mode requires single line" in str(e)
            print(f"✓ Correctly rejected mode=2 with range: {e}")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing edit_file with mode parameter")
    print("=" * 70 + "\n")

    try:
        test_mode_0_replace_single_line()
        test_mode_0_replace_multiple_lines()
        test_mode_1_insert_before()
        test_mode_2_insert_after()
        test_mode_1_insert_at_beginning()
        test_mode_2_insert_at_end()
        test_insert_mode_validation()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Mode parameter working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ mode=0: Replace single line works")
        print("  ✓ mode=0: Replace multiple lines works")
        print("  ✓ mode=1: Insert before line works")
        print("  ✓ mode=2: Insert after line works")
        print("  ✓ mode=1: Insert at beginning works")
        print("  ✓ mode=2: Insert at end works")
        print("  ✓ Insert modes validation works")
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
