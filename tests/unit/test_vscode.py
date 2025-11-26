#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test VSCode integration tools

Tests the VSCode tool functions in mock mode.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.tools import vscode


def test_vscode_tools():
    """Test VSCode tools with mock responses"""
    print("\n" + "=" * 60)
    print("Testing VSCode Tools")
    print("=" * 60)

    # Ensure we're not in VSCode mode
    if 'VSCODE_INTEGRATION' in os.environ:
        del os.environ['VSCODE_INTEGRATION']

    # Test 1: Check mock data
    print("\n1. Checking mock data...")
    assert vscode.MOCK_DATA is not None
    assert 'active_file' in vscode.MOCK_DATA
    assert 'selection' in vscode.MOCK_DATA
    print("✓ Mock data available")

    # Test 2: Get active file
    print("\n2. Testing get_active_file()...")
    file_info = vscode.get_active_file()
    assert 'path' in file_info
    assert 'content' in file_info
    assert 'language' in file_info
    print(f"✓ Got active file: {file_info['path']}")
    print(f"  Language: {file_info['language']}")
    print(f"  Lines: {file_info['lineCount']}")

    # Test 3: Get selection
    print("\n3. Testing get_selection()...")
    selection = vscode.get_selection()
    assert 'text' in selection
    assert 'start' in selection
    assert 'end' in selection
    print(f"✓ Got selection: {selection['text'][:40]}...")
    print(f"  Start: L{selection['start']['line']}:C{selection['start']['character']}")
    print(f"  End: L{selection['end']['line']}:C{selection['end']['character']}")

    # Test 4: Show diff
    print("\n4. Testing show_diff()...")
    result = vscode.show_diff(
        title="Test Diff",
        original_path="/test/file.cpp",
        modified_content="modified content"
    )
    assert result.get('success') == True
    print(f"✓ Diff shown: {result.get('message')}")

    # Test 5: Apply changes
    print("\n5. Testing apply_changes()...")
    result = vscode.apply_changes(
        path="/test/file.cpp",
        old_str="old code",
        new_str="new code"
    )
    assert result.get('success') == True
    print(f"✓ Changes applied: {result.get('message')}")

    # Test 6: Open file
    print("\n6. Testing open_file()...")
    result = vscode.open_file(
        path="/test/network.cpp",
        line=42,
        column=10
    )
    assert result.get('success') == True
    print(f"✓ File opened: {result.get('message')}")

    # Test 7: Get workspace folder
    print("\n7. Testing get_workspace_folder()...")
    workspace = vscode.get_workspace_folder()
    assert workspace is not None
    assert len(workspace) > 0
    print(f"✓ Workspace: {workspace}")

    print("\n" + "=" * 60)
    print("✅ All VSCode tool tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    test_vscode_tools()
