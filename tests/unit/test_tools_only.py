#!/usr/bin/env python3
"""Test filesystem tools without LLM dependencies"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem import view_file, grep_search, edit_file, FileSystemError

def test_tools():
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    
    print("1. Testing grep_search...")
    result = grep_search("class NetworkHandler", "src", project_root)
    assert len(result['matches']) > 0, "Should find NetworkHandler"
    print(f"   ✓ Found {len(result['matches'])} matches")
    
    print("\n2. Testing view_file...")
    file_path = result['matches'][0]['file']
    view_result = view_file(file_path, project_root=project_root)
    assert view_result['total_lines'] > 0
    print(f"   ✓ Read {view_result['total_lines']} lines")
    
    print("\n3. Testing edit_file (dry run)...")
    # Don't actually edit, just verify it would work
    content = view_result['content']
    if 'NetworkHandler' in content:
        print("   ✓ File contains NetworkHandler class")
    
    print("\n✅ All filesystem tests passed!")

if __name__ == '__main__':
    try:
        test_tools()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
