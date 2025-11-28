#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示路径超链接功能（实际工具调用显示）
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console
from backend.cli.path_utils import PathUtils
from backend.cli.output_manager import ToolOutputManager


def demo_hyperlink():
    """演示路径超链接在工具调用中的显示效果"""
    print("\n" + "=" * 70)
    print(" 路径超链接演示 - 模拟工具调用输出")
    print("=" * 70 + "\n")

    # 设置环境
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console()
    path_utils = PathUtils(project_root)

    # Mock agent
    class MockAgent:
        token_counter = None

    agent = MockAgent()

    # 创建 output manager
    output_manager = ToolOutputManager(console, path_utils, agent)

    # 模拟多个工具调用
    test_cases = [
        {
            'tool': 'view_file',
            'args': {
                'path': 'backend/agent/tool_registry.py',
                'line_range': [1, 50]
            },
            'output': '文件内容已读取（50 行）'
        },
        {
            'tool': 'edit_file',
            'args': {
                'path': 'backend/tools/filesystem_tools/view_file.py',
                'old_str': 'def execute',
                'new_str': 'def execute_modified'
            },
            'output': '✓ 文件已修改'
        },
        {
            'tool': 'create_file',
            'args': {
                'path': 'backend/cli/components/status_bar.py',
                'content': '# Status bar component\n...'
            },
            'output': '✓ 文件已创建'
        },
        {
            'tool': 'grep_search',
            'args': {
                'pattern': 'class.*Tool',
                'file_pattern': '*.py',
                'path': 'backend/tools'
            },
            'output': '找到 7 个匹配项'
        },
    ]

    console.print("[bold cyan]🎯 模拟 Agent 执行多个工具调用...[/bold cyan]\n")

    # 显示每个工具调用
    for i, case in enumerate(test_cases, 1):
        console.print(f"[dim]─── 调用 #{i} ───[/dim]")
        output_manager.add_tool_output(
            tool_name=case['tool'],
            output=case['output'],
            args=case['args']
        )
        console.print()

    console.print("=" * 70)
    console.print("\n[bold green]✅ 演示完成！[/bold green]")
    console.print("\n[yellow]💡 提示:[/yellow]")
    console.print("  1. 上面显示的路径应该是可点击的超链接（在支持 OSC 8 的终端中）")
    console.print("  2. 支持的终端：iTerm2, WezTerm, Windows Terminal, kitty")
    console.print("  3. 压缩的路径（如 backend/.../view_file.py）仍然可以点击打开完整路径")
    console.print("  4. Cmd/Ctrl + 点击路径即可在编辑器中打开文件\n")


if __name__ == '__main__':
    demo_hyperlink()
