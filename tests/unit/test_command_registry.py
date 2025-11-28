#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试动态命令注册系统
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.cli.command_registry import CommandRegistry
from rich.console import Console


def test_command_discovery():
    """测试命令自动发现"""
    console = Console()

    # 创建注册器
    registry = CommandRegistry(console)

    # 检查是否发现了所有命令
    commands = registry.list_commands()
    console.print(f"[cyan]发现的命令: {', '.join(sorted(commands))}[/cyan]")

    # 应该至少包含这些命令
    expected_commands = {'help', 'compact', 'model', 'vscode'}
    assert expected_commands.issubset(set(commands)), \
        f"缺少命令: {expected_commands - set(commands)}"

    console.print("[green]✓ Test 1: 命令自动发现成功[/green]")


def test_lazy_loading():
    """测试懒加载"""
    console = Console()

    # 创建注册器（不应该实例化任何命令）
    registry = CommandRegistry(console)
    assert len(registry._command_instances) == 0, \
        "初始化时不应该有命令实例"

    console.print("[green]✓ Test 2: 懒加载初始状态正确[/green]")

    # 获取 help 命令（应该触发实例化）
    help_cmd = registry.get('help')
    assert help_cmd is not None, "help 命令应该存在"
    assert len(registry._command_instances) == 1, \
        "获取 help 后应该有 1 个实例"

    console.print("[green]✓ Test 3: 懒加载按需实例化成功[/green]")

    # 再次获取同一命令（应该返回缓存的实例）
    help_cmd2 = registry.get('help')
    assert help_cmd is help_cmd2, "应该返回同一个实例"
    assert len(registry._command_instances) == 1, \
        "重复获取不应该创建新实例"

    console.print("[green]✓ Test 4: 实例缓存正确[/green]")


def test_command_metadata():
    """测试命令元数据"""
    console = Console()

    # 创建注册器
    registry = CommandRegistry(console)

    # 获取所有元数据
    metadata = registry.get_all_metadata()
    assert 'help' in metadata, "应该有 help 命令元数据"

    help_meta = metadata['help']
    assert help_meta.name == 'help', "命令名称应该是 help"
    assert help_meta.category == 'agent', "help 应该属于 agent 类别"
    assert help_meta.usage == '/help', "用法应该是 /help"

    console.print("[green]✓ Test 5: 命令元数据读取正确[/green]")


def test_category_grouping():
    """测试按类别分组"""
    console = Console()

    # 创建注册器
    registry = CommandRegistry(console)

    # 按类别分组
    by_category = registry.get_commands_by_category()

    # 应该有 agent, model, vscode 等类别
    assert 'agent' in by_category, "应该有 agent 类别"
    assert 'model' in by_category, "应该有 model 类别"
    assert 'vscode' in by_category, "应该有 vscode 类别"

    # agent 类别应该包含 help 和 compact
    agent_commands = {cmd.name for cmd in by_category['agent']}
    assert 'help' in agent_commands, "agent 类别应该包含 help"
    assert 'compact' in agent_commands, "agent 类别应该包含 compact"

    console.print(f"[cyan]类别分组:[/cyan]")
    for category, commands in sorted(by_category.items()):
        cmd_names = ', '.join(cmd.name for cmd in commands)
        console.print(f"  {category}: {cmd_names}")

    console.print("[green]✓ Test 6: 类别分组正确[/green]")


def test_dependency_injection():
    """测试依赖注入"""
    console = Console()

    # 模拟 agent 和 remote_commands 依赖
    class MockAgent:
        pass

    class MockRemoteCommands:
        pass

    mock_agent = MockAgent()
    mock_remote = MockRemoteCommands()

    # 创建注册器并提供依赖
    registry = CommandRegistry(
        console,
        agent=mock_agent,
        remote_commands=mock_remote
    )

    # 获取需要依赖的命令
    compact_cmd = registry.get('compact')
    assert compact_cmd is not None, "compact 命令应该存在"
    assert compact_cmd.agent is mock_agent, "应该注入了 agent 依赖"

    model_cmd = registry.get('model')
    assert model_cmd is not None, "model 命令应该存在"
    assert model_cmd.remote_commands is mock_remote, \
        "应该注入了 remote_commands 依赖"

    console.print("[green]✓ Test 7: 依赖注入正确[/green]")


def test_help_command_with_registry():
    """测试 help 命令能访问 registry"""
    console = Console()

    # 创建注册器
    registry = CommandRegistry(console)

    # 获取 help 命令
    help_cmd = registry.get('help')
    assert help_cmd is not None, "help 命令应该存在"
    assert help_cmd.command_registry is registry, \
        "help 命令应该持有 registry 引用"

    console.print("[green]✓ Test 8: help 命令可以访问 registry[/green]")

    # 执行 help 命令（应该动态生成帮助）
    console.print("\n[cyan]--- 动态生成的帮助信息 ---[/cyan]")
    result = help_cmd.execute([])
    assert result is True, "help 命令应该返回 True"

    console.print("[green]✓ Test 9: help 命令执行成功[/green]")


if __name__ == '__main__':
    console = Console()
    console.print("[bold cyan]测试动态命令注册系统[/bold cyan]\n")

    test_command_discovery()
    test_lazy_loading()
    test_command_metadata()
    test_category_grouping()
    test_dependency_injection()
    test_help_command_with_registry()

    console.print("\n[bold green]所有测试通过！[/bold green]")
