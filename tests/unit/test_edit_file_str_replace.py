#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test edit_file with old_str/new_str (Claude Code style)
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool


def test_simple_replace():
    """Test simple unique string replacement"""
    print("=" * 70)
    print("Test: Simple unique string replacement")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("def hello():\n    print('world')\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            old_str="print('world')",
            new_str="print('Hello World!')"
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "def hello():\n    print('Hello World!')\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_multiline_replace():
    """Test multiline string replacement"""
    print("=" * 70)
    print("Test: Multiline string replacement")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("def foo():\n    x = 1\n    y = 2\n    return x + y\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            old_str="    x = 1\n    y = 2\n    return x + y",
            new_str="    result = 1 + 2\n    return result"
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "def foo():\n    result = 1 + 2\n    return result\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_replace_with_context():
    """Test replacement with surrounding context for uniqueness"""
    print("=" * 70)
    print("Test: Replace with surrounding context")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text(
            "value = 1\nprint(value)\nvalue = 2\nprint(value)\n"
        )

        tool = EditFileTool(project_root=project_root)
        # Replace second "value = " by including context
        result = tool.execute(
            path=str(test_file),
            old_str="print(value)\nvalue = 2",
            new_str="print(value)\nvalue = 20"
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "value = 1\nprint(value)\nvalue = 20\nprint(value)\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_replace_all():
    """Test replace_all parameter"""
    print("=" * 70)
    print("Test: Replace all occurrences")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text(
            "old_name = 1\nprint(old_name)\nreturn old_name\n"
        )

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            old_str="old_name",
            new_str="new_name",
            replace_all=True
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")
        assert "3 occurrences" in result['message']

        # Verify file content
        final_content = test_file.read_text()
        expected_content = "new_name = 1\nprint(new_name)\nreturn new_name\n"
        assert final_content == expected_content
        print("✓ File content is correct")

    print("\n✅ Test PASSED\n")


def test_non_unique_fails():
    """Test that non-unique string fails without replace_all"""
    print("=" * 70)
    print("Test: Non-unique string fails")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("foo\nfoo\nfoo\n")

        tool = EditFileTool(project_root=project_root)
        try:
            result = tool.execute(
                path=str(test_file),
                old_str="foo",
                new_str="bar"
            )
            assert False, "Should have raised error"
        except Exception as e:
            assert "appears 3 times" in str(e)
            print(f"✓ Correctly rejected non-unique string: {e}")

    print("\n✅ Test PASSED\n")


def test_string_not_found_fails():
    """Test that missing string fails"""
    print("=" * 70)
    print("Test: Missing string fails")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        test_file.write_text("hello world\n")

        tool = EditFileTool(project_root=project_root)
        try:
            result = tool.execute(
                path=str(test_file),
                old_str="goodbye",
                new_str="farewell"
            )
            assert False, "Should have raised error"
        except Exception as e:
            assert "String not found" in str(e)
            print(f"✓ Correctly rejected missing string: {e}")

    print("\n✅ Test PASSED\n")


def test_preserve_indentation():
    """Test that indentation is preserved exactly"""
    print("=" * 70)
    print("Test: Preserve exact indentation")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'test.py'
        # Mix of spaces and tabs
        test_file.write_text("def foo():\n\tif True:\n\t    return 1\n")

        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path=str(test_file),
            old_str="\tif True:\n\t    return 1",
            new_str="\tif True:\n\t    return 2"
        )

        assert result['success'] is True
        print(f"✓ Result: {result['message']}")

        # Verify file content (exact indentation)
        final_content = test_file.read_text()
        expected_content = "def foo():\n\tif True:\n\t    return 2\n"
        assert final_content == expected_content
        print("✓ Indentation preserved correctly")

    print("\n✅ Test PASSED\n")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Testing edit_file with old_str/new_str (Claude Code style)")
    print("=" * 70 + "\n")

    try:
        test_simple_replace()
        test_multiline_replace()
        test_replace_with_context()
        test_replace_all()
        test_non_unique_fails()
        test_string_not_found_fails()
        test_preserve_indentation()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Edit file working correctly!")
        print("=" * 70 + "\n")

        print("Summary:")
        print("  ✓ Simple unique string replacement works")
        print("  ✓ Multiline string replacement works")
        print("  ✓ Replace with context for uniqueness works")
        print("  ✓ Replace all occurrences works")
        print("  ✓ Non-unique string correctly rejected")
        print("  ✓ Missing string correctly rejected")
        print("  ✓ Exact indentation preserved")
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
