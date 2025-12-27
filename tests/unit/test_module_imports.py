#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有模块可以正确导入

这个测试确保所有模块的导入语句正确，避免类似 BaseCommand vs Command 的问题。
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console


def test_cli_commands_import():
    """测试所有 CLI 命令可以导入"""
    console = Console()

    # 所有 CLI 命令
    commands = [
        ('backend.cli.commands.help', 'HelpCommand'),
        ('backend.cli.commands.compact', 'CompactCommand'),
        ('backend.cli.commands.model', 'ModelCommand'),
        ('backend.cli.commands.vscode', 'VSCodeCommand'),
        ('backend.cli.commands.shell', 'CmdCommand'),
        ('backend.cli.commands.role', 'RoleCommand'),
        ('backend.cli.commands.session', 'SessionCommand'),
        ('backend.cli.commands.todo', 'TodoCommand'),
    ]

    for module_path, class_name in commands:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            console.print(f"[green]✓[/green] {module_path}.{class_name}")
        except Exception as e:
            console.print(f"[red]✗[/red] {module_path}.{class_name}: {e}")
            raise

    console.print("[green]✓ Test 1: 所有 CLI 命令导入成功[/green]")


def test_tools_import():
    """测试所有工具可以导入"""
    console = Console()

    # 关键工具
    tools = [
        ('backend.tools.agent_tools.todo_write', 'TodoWriteTool'),
        ('backend.tools.agent_tools.propose_options', 'ProposeOptionsTool'),
        ('backend.tools.agent_tools.instant_compact', 'InstantCompactTool'),
        ('backend.tools.filesystem_tools.view_file', 'ViewFileTool'),
        ('backend.tools.filesystem_tools.edit_file', 'EditFileTool'),
        ('backend.tools.filesystem_tools.create_file', 'CreateFileTool'),
        ('backend.tools.filesystem_tools.grep_search', 'GrepSearchTool'),
        ('backend.tools.filesystem_tools.list_dir', 'ListDirTool'),
        ('backend.tools.git_tools.git_tool', 'GitTool'),
        ('backend.tools.executor_tools.bash_run', 'BashRunTool'),
    ]

    for module_path, class_name in tools:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            console.print(f"[green]✓[/green] {module_path}.{class_name}")
        except Exception as e:
            console.print(f"[red]✗[/red] {module_path}.{class_name}: {e}")
            raise

    console.print("[green]✓ Test 2: 所有工具导入成功[/green]")


def test_core_modules_import():
    """测试核心模块可以导入"""
    console = Console()

    # 核心模块
    modules = [
        ('backend.todo', ['TodoManager', 'TodoItem', 'TodoStatus', 'get_todo_manager']),
        ('backend.session', ['SessionManager', 'get_session_manager']),
        ('backend.roles', ['RoleManager', 'get_role_manager']),
        ('backend.agent.tools', ['ToolRegistry', 'ToolExecutor', 'ConfirmAction']),
        ('backend.agent.loop', ['AgentLoop']),
        ('backend.llm.client', ['OllamaClient']),
    ]

    for module_path, exports in modules:
        try:
            module = __import__(module_path, fromlist=exports)
            for export in exports:
                obj = getattr(module, export)
            console.print(f"[green]✓[/green] {module_path}: {', '.join(exports)}")
        except Exception as e:
            console.print(f"[red]✗[/red] {module_path}: {e}")
            raise

    console.print("[green]✓ Test 3: 所有核心模块导入成功[/green]")


def test_command_instantiation():
    """测试命令可以正确实例化"""
    console = Console()

    from backend.cli.commands.todo import TodoCommand
    from backend.cli.commands.session import SessionCommand
    from backend.cli.commands.role import RoleCommand

    # 测试实例化（不需要依赖）
    todo_cmd = TodoCommand(console)
    assert todo_cmd.name == 'todo'
    console.print("[green]✓[/green] TodoCommand 实例化成功")

    session_cmd = SessionCommand(console, project_root='/tmp')
    assert session_cmd.name == 'session'
    console.print("[green]✓[/green] SessionCommand 实例化成功")

    role_cmd = RoleCommand(console)
    assert role_cmd.name == 'role'
    console.print("[green]✓[/green] RoleCommand 实例化成功")

    console.print("[green]✓ Test 4: 命令实例化成功[/green]")


def test_tool_instantiation():
    """测试工具可以正确实例化"""
    console = Console()

    from backend.tools.agent_tools.todo_write import TodoWriteTool

    # 测试实例化
    tool = TodoWriteTool()
    assert tool.name == 'todo_write'
    assert tool.category == 'agent'
    assert tool.priority == 85
    console.print("[green]✓[/green] TodoWriteTool 实例化成功")

    # 测试 schema 生成
    schema = tool.get_openai_schema()
    assert schema['function']['name'] == 'todo_write'
    console.print("[green]✓[/green] TodoWriteTool schema 生成成功")

    console.print("[green]✓ Test 5: 工具实例化成功[/green]")


if __name__ == '__main__':
    console = Console()
    console.print("[bold cyan]测试模块导入[/bold cyan]\n")

    test_cli_commands_import()
    test_tools_import()
    test_core_modules_import()
    test_command_instantiation()
    test_tool_instantiation()

    console.print("\n[bold green]所有测试通过！[/bold green]")
