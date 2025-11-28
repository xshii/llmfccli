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

    # Test 1: Add short output (outputs are now managed by output_manager)
    cli.output_manager.current_command = "test command 1"
    cli.output_manager.add_tool_output(
        "view_file",
        "Line 1\nLine 2\nLine 3",
        args={"path": "/test/file.py"}
    )

    assert len(cli.output_manager.tool_outputs) == 1
    console.print("[green]✓ Test 1: Short output added[/green]")

    # Test 2: Add long output
    cli.output_manager.tool_outputs = []
    long_output = "\n".join([f"Line {i}" for i in range(30)])
    cli.output_manager.add_tool_output(
        "bash_run",
        long_output,
        args={"command": "ls -la"}
    )

    assert len(cli.output_manager.tool_outputs) == 1
    console.print("[green]✓ Test 2: Long output added[/green]")

    # Test 3: Output manager state
    assert cli.output_manager.current_command == "test command 1"
    console.print("[green]✓ Test 3: Output manager state correct[/green]")

    # Test 4: Display summary with execution time and token usage (visual test)
    console.print("\n[cyan]Test 4: Display summary with time and token usage (visual inspection)[/cyan]")
    import time
    cli.output_manager.current_command = "编译项目并修复错误"
    cli.output_manager.command_start_time = time.time() - 5.3  # Simulate 5.3 seconds elapsed

    # Simulate token usage
    if hasattr(cli.agent, 'token_counter'):
        cli.agent.token_counter.usage['total'] = 12500  # 12.5K tokens used
        console.print(f"[dim]Simulated token usage: {cli.agent.token_counter.usage['total']} tokens[/dim]")

    cli.output_manager.tool_outputs = []

    # Add multiple outputs
    cli.output_manager.add_tool_output(
        "bash_run",
        "$ cmake --build build\n[ 10%] Building...\n✓ Build complete",
        args={"command": "cmake --build build"}
    )

    long_compilation = "\n".join([f"[{i}%] Building object {i}..." for i in range(0, 100, 10)])
    cli.output_manager.add_tool_output(
        "bash_run",
        long_compilation,
        args={"command": "make -j8"}
    )

    cli.output_manager.add_tool_output(
        "edit_file",
        "File: src/main.cpp\nEdited lines: 45-67",
        args={"path": "src/main.cpp", "old_str": "old code", "new_str": "new code"}
    )

    cli.output_manager.display_tool_outputs_summary()
    console.print("[green]✓ Test 4: Summary displayed[/green]")

    console.print("\n[bold green]All tests passed![/bold green]")

if __name__ == '__main__':
    test_tool_output_management()
