#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add priority attributes to all tool files
"""

import os
import re
from pathlib import Path

# Tool priority mapping based on usage frequency in C/C++ development
TOOL_PRIORITIES = {
    # High priority (80-100) - most frequently used
    'view_file': 95,      # Essential - read before edit
    'edit_file': 90,      # Essential - main modification tool
    'grep_search': 85,    # Essential - code search

    # Medium priority (50-79) - commonly used
    'bash_run': 70,       # Common - execute commands
    'list_dir': 65,       # Common - explore project structure
    'cmake_build': 60,    # Common - compilation

    # Low priority (1-49) - less frequently used
    'create_file': 40,    # Less common - prefer editing existing files
    'run_tests': 35,      # Less common - testing
    'git': 30,            # Less common - version control
    'propose_options': 20, # Rare - only for ambiguous requests
    'instant_compact': 10, # Internal tool - rarely user-facing
    'vscode': 5,          # Rare - IDE integration
}

def add_priority_to_tool(file_path: Path, priority: int):
    """Add priority property to a tool file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if priority already exists
    if re.search(r'@property\s+def priority\(self\)', content):
        print(f"  ✓ {file_path.name} already has priority")
        return False

    # Find the category property and add priority after it
    pattern = r'(@property\s+def category\(self\) -> str:\s+return "[^"]*")'
    replacement = r'\1\n\n    @property\n    def priority(self) -> int:\n        return ' + str(priority)

    new_content = re.sub(pattern, replacement, content)

    if new_content == content:
        print(f"  ✗ {file_path.name}: Could not find category property")
        return False

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✓ {file_path.name}: Added priority {priority}")
    return True

def main():
    """Main function"""
    # Get tools directory
    project_root = Path(__file__).parent.parent
    tools_dir = project_root / 'backend' / 'tools'

    if not tools_dir.exists():
        print(f"Error: Tools directory not found: {tools_dir}")
        return

    print("Adding priority attributes to tools...")
    print()

    updated = 0
    skipped = 0

    # Scan all tool files
    for category_dir in tools_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith('_'):
            continue

        print(f"{category_dir.name}:")

        for py_file in category_dir.glob('*.py'):
            if py_file.name in ('__init__.py', 'base.py', 'exceptions.py', 'compiler_parser.py'):
                continue

            # Extract tool name from file name
            # bash_run.py -> bash_run
            # git_tool.py -> git
            tool_name = py_file.stem
            if tool_name.endswith('_tool'):
                tool_name = tool_name[:-5]

            priority = TOOL_PRIORITIES.get(tool_name, 50)  # Default to 50

            if add_priority_to_tool(py_file, priority):
                updated += 1
            else:
                skipped += 1

        print()

    print(f"Summary: {updated} files updated, {skipped} files skipped")

if __name__ == '__main__':
    main()
