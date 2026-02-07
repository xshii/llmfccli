#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ToolOutputManager 的路径超链接功能
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console
from backend.cli.path_utils import PathUtils
from backend.cli.output_manager import ToolOutputManager


def test_hyperlink_format():
    """测试超链接格式是否正确"""
    print("=" * 60)
    print("测试超链接格式")
    print("=" * 60)

    # 设置环境
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console(file=open(os.devnull, 'w'))  # 不输出到终端
    path_utils = PathUtils(project_root)

    class MockAgent:
        token_counter = None

    output_manager = ToolOutputManager(console, path_utils, MockAgent())

    # 测试用例
    test_cases = [
        {
            'tool': 'view_file',
            'args': {'path': 'backend/agent/tool_registry.py'},
            'expected_pattern': r'\[link=file://.*tool_registry\.py\].*\[/link\]'
        },
        {
            'tool': 'edit_file',
            'args': {'path': 'backend/tools/filesystem_tools/view_file.py'},
            'expected_pattern': r'\[link=file://.*view_file\.py\].*\[/link\]'
        },
        {
            'tool': 'create_file',
            'args': {'path': '/tmp/test.txt'},
            'expected_pattern': r'\[link=file:///tmp/test\.txt\].*\[/link\]'
        },
    ]

    import re
    all_passed = True

    for i, case in enumerate(test_cases, 1):
        formatted = output_manager._format_tool_call(case['tool'], case['args'])

        print(f"\n测试 #{i}: {case['tool']}")
        print(f"  参数: {case['args']}")
        print(f"  格式化: {formatted}")

        # 检查是否包含超链接或纯路径（取决于 hyperlink_protocol 配置）
        if '[link=file://' in formatted and '[/link]' in formatted:
            # file:// 协议模式
            link_match = re.search(r'\[link=file://([^\]]+)\]([^\[]+)\[/link\]', formatted)
            if link_match:
                abs_path = link_match.group(1)
                display_text = link_match.group(2)

                print(f"  ✓ 包含超链接")
                print(f"    绝对路径: {abs_path}")
                print(f"    显示文本: {display_text}")

                # 验证路径是绝对路径
                if os.path.isabs(abs_path) or abs_path.startswith('/'):
                    print(f"  ✓ 路径是绝对路径")
                else:
                    print(f"  ✗ 路径不是绝对路径！")
                    all_passed = False
            else:
                print(f"  ✗ 超链接格式不正确！")
                all_passed = False
        elif case['args'].get('path', '') in formatted:
            # none 协议模式：路径以纯文本显示
            print(f"  ✓ 纯路径模式（none 协议）")
        else:
            print(f"  ✗ 未找到路径！")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


def test_non_path_params():
    """测试非路径参数不应该被压缩或添加超链接"""
    print("\n" + "=" * 60)
    print("测试非路径参数处理")
    print("=" * 60)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console(file=open(os.devnull, 'w'))
    path_utils = PathUtils(project_root)

    class MockAgent:
        token_counter = None

    output_manager = ToolOutputManager(console, path_utils, MockAgent())

    # 测试非路径参数
    test_cases = [
        {
            'tool': 'grep_search',
            'args': {
                'pattern': 'class.*Tool',
                'file_pattern': '*.py',
                'path': 'backend/tools'  # 这个是路径
            },
            'path_params': ['path'],  # 只有 path 应该被处理
            'non_path_params': ['pattern', 'file_pattern']
        },
        {
            'tool': 'bash_run',
            'args': {
                'command': 'ls -la /tmp',
                'timeout': 30
            },
            'path_params': [],
            'non_path_params': ['command', 'timeout']
        },
    ]

    all_passed = True

    for i, case in enumerate(test_cases, 1):
        formatted = output_manager._format_tool_call(case['tool'], case['args'])

        print(f"\n测试 #{i}: {case['tool']}")
        print(f"  格式化: {formatted}")

        # 检查路径参数应该有超链接
        for param in case['path_params']:
            if f"{param}=" in formatted:
                # 应该包含超链接
                if '[link=file://' in formatted:
                    print(f"  ✓ 路径参数 '{param}' 包含超链接")
                else:
                    print(f"  ⚠ 路径参数 '{param}' 未包含超链接（可能路径格式不符）")

        # 检查非路径参数不应该有超链接
        has_extra_links = formatted.count('[link=file://') > len(case['path_params'])
        if not has_extra_links:
            print(f"  ✓ 非路径参数未被错误处理")
        else:
            print(f"  ✗ 非路径参数被错误添加了超链接！")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == '__main__':
    result1 = test_hyperlink_format()
    result2 = test_non_path_params()

    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)

    if result1 and result2:
        print("🎉 所有测试套件通过！")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败")
        sys.exit(1)
