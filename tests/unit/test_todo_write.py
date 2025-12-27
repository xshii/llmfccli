#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TodoWrite 工具测试用例

测试 TodoManager 和 todo_write 工具的核心功能
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console


def test_todo_manager_basic():
    """测试 TodoManager 基本功能"""
    console = Console()

    from backend.todo import get_todo_manager, TodoStatus

    manager = get_todo_manager()
    manager.clear()  # 清空之前的状态

    # 测试设置任务
    result = manager.set_todos([
        {'content': '分析代码', 'status': 'completed', 'activeForm': '分析代码中'},
        {'content': '修改文件', 'status': 'in_progress', 'activeForm': '修改文件中'},
        {'content': '运行测试', 'status': 'pending', 'activeForm': '运行测试中'},
    ])

    assert result['success'] is True
    assert result['total'] == 3
    assert result['completed'] == 1
    assert result['pending'] == 1
    assert result['in_progress'] == 1

    console.print("[green]✓ Test 1: 基本任务设置成功[/green]")


def test_todo_manager_single_in_progress():
    """测试同一时间只能有一个 in_progress"""
    console = Console()

    from backend.todo import get_todo_manager

    manager = get_todo_manager()
    manager.clear()

    # 尝试设置两个 in_progress - 应该失败
    result = manager.set_todos([
        {'content': '任务1', 'status': 'in_progress', 'activeForm': '执行任务1'},
        {'content': '任务2', 'status': 'in_progress', 'activeForm': '执行任务2'},
    ])

    assert result['success'] is False
    assert 'in_progress' in result['error']

    console.print("[green]✓ Test 2: 多个 in_progress 被正确拒绝[/green]")


def test_todo_manager_progress():
    """测试进度计算"""
    console = Console()

    from backend.todo import get_todo_manager

    manager = get_todo_manager()
    manager.clear()

    # 0% 进度
    manager.set_todos([
        {'content': '任务1', 'status': 'pending', 'activeForm': '任务1'},
        {'content': '任务2', 'status': 'pending', 'activeForm': '任务2'},
    ])
    assert manager.progress_percent == 0

    # 50% 进度
    manager.set_todos([
        {'content': '任务1', 'status': 'completed', 'activeForm': '任务1'},
        {'content': '任务2', 'status': 'pending', 'activeForm': '任务2'},
    ])
    assert manager.progress_percent == 50

    # 100% 进度
    manager.set_todos([
        {'content': '任务1', 'status': 'completed', 'activeForm': '任务1'},
        {'content': '任务2', 'status': 'completed', 'activeForm': '任务2'},
    ])
    assert manager.progress_percent == 100

    console.print("[green]✓ Test 3: 进度计算正确[/green]")


def test_todo_manager_current_task():
    """测试当前任务获取"""
    console = Console()

    from backend.todo import get_todo_manager

    manager = get_todo_manager()
    manager.clear()

    # 无 in_progress 时
    manager.set_todos([
        {'content': '任务1', 'status': 'completed', 'activeForm': '任务1'},
        {'content': '任务2', 'status': 'pending', 'activeForm': '任务2'},
    ])
    assert manager.current_task is None

    # 有 in_progress 时
    manager.set_todos([
        {'content': '任务1', 'status': 'completed', 'activeForm': '任务1'},
        {'content': '正在执行的任务', 'status': 'in_progress', 'activeForm': '执行中'},
        {'content': '任务3', 'status': 'pending', 'activeForm': '任务3'},
    ])
    assert manager.current_task is not None
    assert manager.current_task.content == '正在执行的任务'
    assert manager.current_task.active_form == '执行中'

    console.print("[green]✓ Test 4: 当前任务获取正确[/green]")


def test_todo_manager_display():
    """测试显示文本生成"""
    console = Console()

    from backend.todo import get_todo_manager

    manager = get_todo_manager()
    manager.clear()

    manager.set_todos([
        {'content': '任务1', 'status': 'completed', 'activeForm': '任务1'},
        {'content': '当前任务', 'status': 'in_progress', 'activeForm': '正在处理'},
        {'content': '任务3', 'status': 'pending', 'activeForm': '任务3'},
    ])

    display = manager.get_display_text()

    # 应该包含进度条
    assert '█' in display or '░' in display
    # 应该包含百分比
    assert '33%' in display or '34%' in display  # 1/3 ≈ 33%
    # 应该包含当前任务
    assert '正在处理' in display

    console.print(f"[dim]显示文本: {display}[/dim]")
    console.print("[green]✓ Test 5: 显示文本生成正确[/green]")


def test_todo_write_tool():
    """测试 todo_write 工具"""
    console = Console()

    from backend.tools.agent_tools.todo_write import TodoWriteTool
    from backend.todo import get_todo_manager

    # 清空状态
    get_todo_manager().clear()

    tool = TodoWriteTool()

    # 验证工具属性
    assert tool.name == 'todo_write'
    assert tool.category == 'agent'
    assert tool.priority == 85  # 高优先级

    # 测试执行
    result = tool.execute(todos=[
        {'content': '读取配置', 'status': 'completed', 'activeForm': '读取配置中'},
        {'content': '处理数据', 'status': 'in_progress', 'activeForm': '处理数据中'},
        {'content': '保存结果', 'status': 'pending', 'activeForm': '保存结果中'},
    ])

    assert result['success'] is True
    assert result['total'] == 3
    assert result['current_task'] == '处理数据'

    console.print("[green]✓ Test 6: todo_write 工具执行成功[/green]")


def test_todo_write_tool_schema():
    """测试 todo_write 工具 schema"""
    console = Console()

    from backend.tools.agent_tools.todo_write import TodoWriteTool

    tool = TodoWriteTool()
    schema = tool.get_openai_schema()

    # 验证 schema 结构
    assert schema['type'] == 'function'
    assert schema['function']['name'] == 'todo_write'
    assert 'parameters' in schema['function']
    assert 'todos' in schema['function']['parameters']['properties']

    console.print(f"[dim]Schema: {schema['function']['name']}[/dim]")
    console.print("[green]✓ Test 7: todo_write schema 正确[/green]")


def test_todo_manager_singleton():
    """测试 TodoManager 单例模式"""
    console = Console()

    from backend.todo import get_todo_manager

    manager1 = get_todo_manager()
    manager2 = get_todo_manager()

    # 应该是同一个实例
    assert manager1 is manager2

    # 修改 manager1 应该影响 manager2
    manager1.clear()
    manager1.set_todos([
        {'content': '测试任务', 'status': 'pending', 'activeForm': '测试中'},
    ])

    assert manager2.total_count == 1
    assert manager2.todos[0].content == '测试任务'

    console.print("[green]✓ Test 8: 单例模式正确[/green]")


def test_todo_manager_callback():
    """测试变更回调"""
    console = Console()

    from backend.todo import get_todo_manager

    manager = get_todo_manager()
    manager.clear()

    # 记录回调次数
    callback_count = [0]

    def on_change(mgr):
        callback_count[0] += 1

    manager.on_change(on_change)

    # 设置任务应该触发回调
    manager.set_todos([
        {'content': '任务1', 'status': 'pending', 'activeForm': '任务1'},
    ])

    assert callback_count[0] == 1

    # 清空也应该触发回调
    manager.clear()
    assert callback_count[0] == 2

    console.print("[green]✓ Test 9: 变更回调正确[/green]")


def test_todo_item_serialization():
    """测试 TodoItem 序列化"""
    console = Console()

    from backend.todo import TodoItem, TodoStatus

    # 测试 to_dict
    item = TodoItem(
        content='测试任务',
        status=TodoStatus.IN_PROGRESS,
        active_form='正在测试'
    )

    d = item.to_dict()
    assert d['content'] == '测试任务'
    assert d['status'] == 'in_progress'
    assert d['activeForm'] == '正在测试'

    # 测试 from_dict
    item2 = TodoItem.from_dict({
        'content': '另一个任务',
        'status': 'completed',
        'activeForm': '已完成'
    })

    assert item2.content == '另一个任务'
    assert item2.status == TodoStatus.COMPLETED
    assert item2.active_form == '已完成'

    console.print("[green]✓ Test 10: TodoItem 序列化正确[/green]")


if __name__ == '__main__':
    console = Console()
    console.print("[bold cyan]测试 TodoWrite 机制[/bold cyan]\n")

    test_todo_manager_basic()
    test_todo_manager_single_in_progress()
    test_todo_manager_progress()
    test_todo_manager_current_task()
    test_todo_manager_display()
    test_todo_write_tool()
    test_todo_write_tool_schema()
    test_todo_manager_singleton()
    test_todo_manager_callback()
    test_todo_item_serialization()

    console.print("\n[bold green]所有测试通过！[/bold green]")
