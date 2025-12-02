#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test tool priority sorting logic
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.agent.tools.registry import ToolRegistry

def main():
    """Test tool priority sorting"""
    print("Testing Tool Priority Sorting")
    print("=" * 80)
    print()

    # Create registry
    registry = ToolRegistry(project_root=str(project_root))

    # Get schemas with priority sorting
    schemas = registry.get_openai_schemas()

    print(f"Total tools: {len(schemas)}")
    print()

    # Display tool order
    print("Tool Order (after priority sorting):")
    print("-" * 80)

    for i, schema in enumerate(schemas, 1):
        tool_name = schema['function']['name']

        # Get tool to check priority
        tool = registry.get(tool_name)
        priority = getattr(tool, 'priority', 50) if tool else 50

        # Determine group
        if priority >= 80:
            group = "HIGH"
        elif priority >= 50:
            group = "MID "
        else:
            group = "LOW "

        print(f"{i:2d}. [{group}] {tool_name:20s} (priority: {priority})")

    print()
    print("=" * 80)
    print()

    # Analyze distribution
    high_count = sum(1 for s in schemas if getattr(registry.get(s['function']['name']), 'priority', 50) >= 80)
    mid_count = sum(1 for s in schemas if 50 <= getattr(registry.get(s['function']['name']), 'priority', 50) < 80)
    low_count = sum(1 for s in schemas if getattr(registry.get(s['function']['name']), 'priority', 50) < 50)

    print("Distribution:")
    print(f"  High priority (80-100): {high_count} tools")
    print(f"  Mid priority  (50-79):  {mid_count} tools")
    print(f"  Low priority  (1-49):   {low_count} tools")
    print()

    # Verify ordering rules
    print("Verification:")

    # Rule 1: High priority tools should be at the front
    high_tools_positions = [i for i, s in enumerate(schemas)
                           if getattr(registry.get(s['function']['name']), 'priority', 50) >= 80]
    if high_tools_positions:
        expected_high = list(range(high_count))
        if high_tools_positions == expected_high:
            print("  ✓ High priority tools are at the front")
        else:
            print(f"  ✗ High priority tools not at front: {high_tools_positions}")

    # Rule 2: Mid priority tools should be at the end (reversed)
    mid_tools_positions = [i for i, s in enumerate(schemas)
                          if 50 <= getattr(registry.get(s['function']['name']), 'priority', 50) < 80]
    if mid_tools_positions:
        expected_mid_start = len(schemas) - mid_count
        if all(pos >= expected_mid_start for pos in mid_tools_positions):
            print("  ✓ Mid priority tools are at the end")
        else:
            print(f"  ✗ Mid priority tools not at end: {mid_tools_positions}")

    # Rule 3: Low priority tools should be in the middle
    low_tools_positions = [i for i, s in enumerate(schemas)
                          if getattr(registry.get(s['function']['name']), 'priority', 50) < 50]
    if low_tools_positions:
        expected_low_start = high_count
        expected_low_end = len(schemas) - mid_count
        if all(expected_low_start <= pos < expected_low_end for pos in low_tools_positions):
            print("  ✓ Low priority tools are in the middle")
        else:
            print(f"  ✗ Low priority tools not in middle: {low_tools_positions}")

    print()

if __name__ == '__main__':
    main()
