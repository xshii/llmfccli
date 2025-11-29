#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具确认功能演示 - 展示路径超链接和智能压缩的完整效果
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools import registry
from backend.cli.path_utils import PathUtils
from backend.cli.output_manager import ToolOutputManager
from rich.console import Console
from rich.panel import Panel


def demo_tool_confirmation():
    """演示工具确认时的路径显示效果"""

    # 设置环境
    project_root = os.path.join(os.path.dirname(__file__), '../..')
    project_root = os.path.abspath(project_root)
    registry.initialize(project_root)

    # 创建组件
    path_utils = PathUtils(project_root)
    console = Console()
    output_manager = ToolOutputManager(console, path_utils, agent=None)
    output_manager.use_vscode_protocol = True

    console.print("\n" + "=" * 70)
    console.print("[bold cyan]工具确认功能演示 - 路径超链接和智能压缩[/bold cyan]")
    console.print("=" * 70 + "\n")

    # 模拟不同的工具调用场景
    scenarios = [
        {
            "name": "场景 1: view_file - 短路径（不压缩）",
            "tool_name": "view_file",
            "arguments": {
                "path": os.path.join(project_root, "backend/tools.py"),
                "line_range": (10, 50)
            }
        },
        {
            "name": "场景 2: view_file - 中等路径（不压缩）",
            "tool_name": "view_file",
            "arguments": {
                "path": os.path.join(project_root, "tests/unit/test_basic.py"),
                "line_range": (1, 100)
            }
        },
        {
            "name": "场景 3: view_file - 长路径（智能压缩）",
            "tool_name": "view_file",
            "arguments": {
                "path": os.path.join(project_root, "backend/agent/tools/filesystem/view_file.py"),
                "line_range": (42, 100)
            }
        },
        {
            "name": "场景 4: edit_file - 深层嵌套路径",
            "tool_name": "edit_file",
            "arguments": {
                "path": os.path.join(project_root, "backend/cli/output_manager.py"),
                "old_str": "old code",
                "new_str": "new code"
            }
        },
        {
            "name": "场景 5: list_dir - 项目根目录",
            "tool_name": "list_dir",
            "arguments": {
                "path": os.path.join(project_root, "backend"),
                "max_depth": 3
            }
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        console.print(f"\n[bold yellow]{scenario['name']}[/bold yellow]")
        console.print("-" * 70)

        tool_name = scenario['tool_name']
        arguments = scenario['arguments']

        # 获取工具元数据
        tool_metadata = registry.get_tool_metadata(tool_name)
        param_formats = {}

        if tool_metadata:
            properties = tool_metadata.get('schema', {}).get('function', {}).get('parameters', {}).get('properties', {})
            for param_name, param_info in properties.items():
                if param_info.get('format') == 'filepath':
                    param_formats[param_name] = 'filepath'

        # 提取行号
        line_number = None
        if 'line_range' in arguments and arguments['line_range']:
            line_range = arguments['line_range']
            if isinstance(line_range, (tuple, list)) and len(line_range) >= 1:
                line_number = line_range[0]

        # 格式化参数显示
        args_display = []
        for key, value in arguments.items():
            value_str = str(value)
            original_value = value_str

            # 处理路径参数
            if param_formats.get(key) == 'filepath' and ('/' in value_str or '\\' in value_str):
                # 显示原始路径（相对）
                if value_str.startswith(project_root):
                    rel_path = os.path.relpath(value_str, project_root)
                    console.print(f"  [dim]原始路径:[/dim] {rel_path} [dim]({len(rel_path)}字符)[/dim]")

                # 生成超链接
                value_str = output_manager._create_file_hyperlink(value_str, line=line_number)

                # 解析压缩后的显示文本
                # 格式: [link=vscode://file...]compressed_path[/link]
                import re
                match = re.search(r'\[link=.*?\](.*?)\[/link\]', value_str)
                if match:
                    compressed = match.group(1)
                    console.print(f"  [dim]压缩显示:[/dim] {compressed} [dim]({len(compressed)}字符)[/dim]")
                    console.print(f"  [dim]超链接:[/dim] 是 [dim](VSCode 协议 + 行号:{line_number or 'N/A'})[/dim]")

            elif len(value_str) > 60:
                value_str = value_str[:57] + "..."

            args_display.append(f"  • [cyan]{key}[/cyan]: {value_str}")

        # 显示最终效果
        console.print(f"\n  [bold]最终显示效果:[/bold]")
        for line in args_display:
            console.print(line)

    # 压缩效果对比
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]路径压缩效果对比表[/bold cyan]")
    console.print("=" * 70 + "\n")

    comparison_paths = [
        "backend/tools.py",
        "tests/unit/test_basic.py",
        "backend/agent/tools/filesystem/view_file.py",
        "backend/cli/output_manager.py",
        "tests/fixtures/sample-cpp/src/network_handler.cpp",
    ]

    console.print(f"{'原始路径':50s} | {'长度':4s} | {'压缩后(50字符限制)':35s} | {'长度':4s}")
    console.print("-" * 105)

    for rel_path in comparison_paths:
        full_path = os.path.join(project_root, rel_path)
        compressed = path_utils.compress_path(full_path, max_length=50)

        # 如果是项目内路径，显示相对路径
        if compressed.startswith('/'):
            display = compressed
        else:
            display = compressed

        console.print(f"{rel_path:50s} | {len(rel_path):4d} | {display:35s} | {len(display):4d}")

    # 总结
    console.print("\n" + "=" * 70)
    console.print("[bold green]✅ 改进总结[/bold green]")
    console.print("=" * 70)
    console.print("""
[bold]1. 智能路径压缩[/bold]
   • 基于字符长度（50字符）而非固定层级
   • 短路径不压缩，保持可读性
   • 长路径智能裁剪，保留关键信息

[bold]2. VSCode 超链接[/bold]
   • 自动检测 filepath 格式的参数
   • 生成 vscode://file/path:line 协议链接
   • 支持行号跳转（从 line_range 等参数提取）

[bold]3. 最优显示效果[/bold]
   • 项目内路径优先用相对路径
   • 路径压缩保留第一层和文件名
   • 中间层级智能裁剪，确保不超过限制
    """)
    console.print("=" * 70 + "\n")


if __name__ == '__main__':
    demo_tool_confirmation()
