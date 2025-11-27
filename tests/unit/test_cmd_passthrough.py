#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test command passthrough functionality (/cmd and /cmdremote)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.remotectl.commands import RemoteCommands
from rich.console import Console


def test_local_command():
    """Test local command execution"""
    console = Console()
    commands = RemoteCommands(console)

    console.print("\n[cyan]测试 1: 本地命令执行 (/cmd)[/cyan]")
    console.print("[dim]执行: echo 'Hello from local command'[/dim]")

    success = commands.execute_local_command("echo 'Hello from local command'")

    if success:
        console.print("[green]✓ 本地命令测试通过[/green]")
    else:
        console.print("[red]✗ 本地命令测试失败[/red]")

    return success


def test_local_command_with_pipe():
    """Test local command with pipe"""
    console = Console()
    commands = RemoteCommands(console)

    console.print("\n[cyan]测试 2: 本地命令 (带管道)[/cyan]")
    console.print("[dim]执行: ls -la | head -5[/dim]")

    success = commands.execute_local_command("ls -la | head -5")

    if success:
        console.print("[green]✓ 管道命令测试通过[/green]")
    else:
        console.print("[red]✗ 管道命令测试失败[/red]")

    return success


def test_pwd():
    """Test pwd command"""
    console = Console()
    commands = RemoteCommands(console)

    console.print("\n[cyan]测试 3: 获取当前目录[/cyan]")
    console.print("[dim]执行: pwd[/dim]")

    success = commands.execute_local_command("pwd")

    if success:
        console.print("[green]✓ pwd 测试通过[/green]")
    else:
        console.print("[red]✗ pwd 测试失败[/red]")

    return success


def test_remote_command():
    """Test remote command execution"""
    console = Console()
    commands = RemoteCommands(console)

    console.print("\n[cyan]测试 4: 远程命令执行 (/cmdremote)[/cyan]")
    console.print("[dim]执行: echo 'Hello from remote command'[/dim]")

    # This will fall back to local if SSH is not enabled
    success = commands.execute_remote_command("echo 'Hello from remote command'")

    if success:
        console.print("[green]✓ 远程命令测试通过[/green]")
    else:
        console.print("[red]✗ 远程命令测试失败[/red]")

    return success


def test_error_handling():
    """Test error handling for invalid commands"""
    console = Console()
    commands = RemoteCommands(console)

    console.print("\n[cyan]测试 5: 错误处理 (无效命令)[/cyan]")
    console.print("[dim]执行: this_command_does_not_exist_12345[/dim]")

    success = commands.execute_local_command("this_command_does_not_exist_12345")

    if not success:
        console.print("[green]✓ 错误处理测试通过 (命令失败符合预期)[/green]")
        return True
    else:
        console.print("[red]✗ 错误处理测试失败 (应该返回失败)[/red]")
        return False


def main():
    """Run all tests"""
    console = Console()

    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  命令透传功能测试[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]")

    results = []

    # Run tests
    results.append(("本地命令执行", test_local_command()))
    results.append(("管道命令", test_local_command_with_pipe()))
    results.append(("pwd 命令", test_pwd()))
    results.append(("远程命令执行", test_remote_command()))
    results.append(("错误处理", test_error_handling()))

    # Print summary
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  测试总结[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[green]✓[/green]" if result else "[red]✗[/red]"
        console.print(f"{status} {name}")

    console.print(f"\n通过: {passed}/{total}")

    if passed == total:
        console.print("\n[bold green]所有测试通过! ✓[/bold green]\n")
        return 0
    else:
        console.print(f"\n[bold red]{total - passed} 个测试失败[/bold red]\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
