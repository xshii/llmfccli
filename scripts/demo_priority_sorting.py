#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Tool Priority Sorting System

Demonstrates how the priority system reorders tools to optimize LLM selection.
"""

import random

def demonstrate_priority_sorting():
    """Demonstrate the priority-based tool sorting"""

    # Simulate real tool priorities from the system
    tools = [
        (95, 'view_file', 'Read files - required before editing'),
        (90, 'edit_file', 'Edit files with exact string replacement'),
        (85, 'grep_search', 'Search code patterns in files'),
        (70, 'bash_run', 'Execute shell commands'),
        (65, 'list_dir', 'List directory contents'),
        (60, 'cmake_build', 'Build C/C++ projects with CMake'),
        (40, 'create_file', 'Create new files'),
        (35, 'run_tests', 'Run test suites'),
        (30, 'git', 'Git version control operations'),
        (20, 'propose_options', 'Ask user for clarification'),
        (10, 'instant_compact', 'Internal context compression'),
    ]

    print("=" * 80)
    print("TOOL PRIORITY SORTING DEMONSTRATION")
    print("=" * 80)
    print()

    # Show original order (by priority)
    print("Original Tools (sorted by priority):")
    print("-" * 80)
    for priority, name, desc in sorted(tools, key=lambda x: x[0], reverse=True):
        group = "HIGH" if priority >= 80 else "MID " if priority >= 50 else "LOW "
        print(f"  [{group}] {priority:3d} - {name:20s} {desc}")
    print()

    # Apply the sorting algorithm
    high = [(p, n, d) for p, n, d in tools if p >= 80]
    mid = [(p, n, d) for p, n, d in tools if 50 <= p < 80]
    low = [(p, n, d) for p, n, d in tools if p < 50]

    # Reverse mid-priority (will go to end)
    mid.reverse()

    # Shuffle low-priority (will go to middle)
    random.shuffle(low)

    # Construct final list: high + low + mid
    final_order = high + low + mid

    print("After Priority-Based Sorting (as sent to LLM):")
    print("-" * 80)
    print()

    # Show positions
    positions = {
        'front': list(range(len(high))),
        'middle': list(range(len(high), len(high) + len(low))),
        'end': list(range(len(high) + len(low), len(final_order)))
    }

    for i, (priority, name, desc) in enumerate(final_order):
        group = "HIGH" if priority >= 80 else "MID " if priority >= 50 else "LOW "

        # Determine position label
        if i in positions['front']:
            pos_label = "FRONT"
        elif i in positions['middle']:
            pos_label = "MIDDLE"
        else:
            pos_label = "END"

        print(f"  {i+1:2d}. [{group}] [{pos_label:6s}] {name:20s} (priority: {priority})")

    print()
    print("=" * 80)
    print()

    # Explain the strategy
    print("STRATEGY EXPLANATION:")
    print("-" * 80)
    print()
    print("Based on research: Tools at LIST ENDS have higher selection probability")
    print()
    print("1. HIGH priority (80-100) → FRONT positions")
    print(f"   - Positions: 1-{len(high)}")
    print("   - Tools: Most frequently used (view_file, edit_file, grep_search)")
    print("   - Why: Maximize visibility for essential operations")
    print()
    print("2. LOW priority (1-49) → MIDDLE positions (randomized)")
    print(f"   - Positions: {len(high)+1}-{len(high)+len(low)}")
    print("   - Tools: Rarely used (git, propose_options, instant_compact)")
    print("   - Why: Lower visibility, randomized to avoid position bias")
    print()
    print("3. MID priority (50-79) → END positions (reversed)")
    print(f"   - Positions: {len(high)+len(low)+1}-{len(final_order)}")
    print("   - Tools: Commonly used (bash_run, cmake_build, list_dir)")
    print("   - Why: End position advantage, reversed for variety")
    print()
    print("=" * 80)
    print()

    # Show distribution
    print("DISTRIBUTION SUMMARY:")
    print("-" * 80)
    high_pct = len(high) / len(final_order) * 100
    mid_pct = len(mid) / len(final_order) * 100
    low_pct = len(low) / len(final_order) * 100

    print(f"  High priority: {len(high):2d} tools ({high_pct:5.1f}%) at FRONT")
    print(f"  Mid priority:  {len(mid):2d} tools ({mid_pct:5.1f}%) at END")
    print(f"  Low priority:  {len(low):2d} tools ({low_pct:5.1f}%) in MIDDLE")
    print()
    print("=" * 80)

if __name__ == '__main__':
    demonstrate_priority_sorting()
