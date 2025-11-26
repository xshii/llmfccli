#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for enhanced CLI features
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.cli import CLI
from rich.console import Console

def test_tool_output_management():
    """Test tool output tracking and display"""
    console = Console()

    # Create CLI instance (skip precheck for testing)
    cli = CLI(skip_precheck=True)

    # Test 1: Add short output (should not collapse)
    cli.current_command = "test command 1"
    cli.add_tool_output(
        "view_file",
        "Line 1\nLine 2\nLine 3",
        args={"path": "/test/file.py"}
    )

    assert len(cli.tool_outputs) == 1
    assert not cli.tool_outputs[0]['collapsed'], "Short output should not collapse"
    console.print("[green]✓ Test 1: Short output not collapsed[/green]")

    # Test 2: Add long output (should auto-collapse)
    cli.tool_outputs = []
    long_output = "\n".join([f"Line {i}" for i in range(30)])
    cli.add_tool_output(
        "bash_run",
        long_output,
        args={"command": "ls -la"}
    )

    assert len(cli.tool_outputs) == 1
    assert cli.tool_outputs[0]['collapsed'], "Long output should auto-collapse"
    console.print("[green]✓ Test 2: Long output auto-collapsed[/green]")

    # Test 3: Toggle output
    cli.toggle_last_output()
    assert not cli.tool_outputs[0]['collapsed'], "Output should be expanded after toggle"
    console.print("[green]✓ Test 3: Toggle expands output[/green]")

    # Test 4: Display summary with execution time and token usage (visual test)
    console.print("\n[cyan]Test 4: Display summary with time and token usage (visual inspection)[/cyan]")
    import time
    cli.current_command = "编译项目并修复错误"
    cli.command_start_time = time.time() - 5.3  # Simulate 5.3 seconds elapsed

    # Simulate token usage
    if hasattr(cli.agent, 'token_counter'):
        cli.agent.token_counter.usage['total'] = 12500  # 12.5K tokens used
        console.print(f"[dim]Simulated token usage: {cli.agent.token_counter.usage['total']} tokens[/dim]")

    cli.tool_outputs = []

    # Add multiple outputs
    cli.add_tool_output(
        "bash_run",
        "$ cmake --build build\n[ 10%] Building...\n✓ Build complete",
        args={"command": "cmake --build build"},
        auto_collapse=False
    )

    long_compilation = "\n".join([f"[{i}%] Building object {i}..." for i in range(0, 100, 10)])
    cli.add_tool_output(
        "bash_run",
        long_compilation,
        args={"command": "make -j8", "cwd": "/project"}
    )

    cli.add_tool_output(
        "edit_file",
        "File: src/main.cpp\nEdited lines: 45-67",
        args={"path": "src/main.cpp", "old_str": "old code", "new_str": "new code"}
    )

    cli.display_tool_outputs_summary()
    console.print("[green]✓ Test 4: Summary displayed[/green]")

    console.print("\n[bold green]All tests passed![/bold green]")

if __name__ == '__main__':
    test_tool_output_management()
