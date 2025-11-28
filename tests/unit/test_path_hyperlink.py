#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试路径超链接功能
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console
from backend.cli.path_utils import PathUtils
from backend.cli.output_manager import ToolOutputManager


def test_path_hyperlink():
    """测试压缩路径的超链接功能"""
    print("=" * 60)
    print("测试路径超链接功能")
    print("=" * 60)

    # 设置测试环境
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console()
    path_utils = PathUtils(project_root)

    # 创建 mock agent
    class MockAgent:
        token_counter = None

    agent = MockAgent()

    # 创建 output manager
    output_manager = ToolOutputManager(console, path_utils, agent)

    # 测试路径
    test_paths = [
        "/home/user/llmfccli/backend/agent/tool_registry.py",
        "backend/tools/filesystem_tools/view_file.py",
        "/usr/lib/python3/site-packages/very/long/path/to/module.py",
    ]

    print("\n压缩前 -> 压缩后（带超链接）:\n")

    for path in test_paths:
        # 获取绝对路径
        abs_path = os.path.abspath(path) if not os.path.isabs(path) else path

        # 压缩路径
        compressed = path_utils.compress_path(path, max_length=40)

        # 创建超链接
        hyperlink = f"[link=file://{abs_path}]{compressed}[/link]"

        # 显示结果
        print(f"原始: {path}")
        print(f"压缩: {compressed}")
        console.print(f"超链接: {hyperlink}")
        print()

    # 测试工具调用格式化
    print("\n" + "=" * 60)
    print("测试工具调用格式化（带超链接）")
    print("=" * 60)

    # Mock tool schema
    from backend.agent.tools import registry

    # 模拟 view_file 工具调用
    tool_args = {
        'path': 'backend/agent/tool_registry.py',
        'line_range': [1, 100]
    }

    formatted = output_manager._format_tool_call('view_file', tool_args)
    console.print(f"\n工具调用: {formatted}\n")

    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    print("\n提示: 在支持 OSC 8 的终端（如 iTerm2, WezTerm, 新版 Windows Terminal）")
    print("      中，上面的路径应该是可点击的超链接。")
    print("      点击后会在默认编辑器中打开文件。\n")


if __name__ == '__main__':
    test_path_hyperlink()
