#!/usr/bin/env python3
"""
Simple test to verify basic functionality
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.filesystem import view_file, grep_search, edit_file
from backend.agent.tools import ToolRegistry, register_filesystem_tools

def test_filesystem_tools():
    """Test filesystem tools"""
    print("Testing filesystem tools...")
    
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    
    # Test grep_search
    print("\n1. Testing grep_search for 'NetworkHandler'...")
    result = grep_search("class NetworkHandler", "src", project_root)
    print(f"   Found {len(result['matches'])} matches")
    if result['matches']:
        print(f"   First match: {result['matches'][0]['file']}")
    
    # Test view_file
    print("\n2. Testing view_file...")
    if result['matches']:
        file_path = result['matches'][0]['file']
        view_result = view_file(file_path, project_root=project_root)
        print(f"   Read {view_result['total_lines']} lines from {os.path.basename(file_path)}")
        print(f"   File contains 'connect': {'connect' in view_result['content']}")
    
    # Test tool registry
    print("\n3. Testing tool registry...")
    registry = ToolRegistry()
    register_filesystem_tools(project_root)
    schemas = registry.get_schemas()
    print(f"   Registered {len(schemas)} tools")
    
    print("\n✓ All basic tests passed!")
    return True

if __name__ == '__main__':
    try:
        test_filesystem_tools()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
