#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 VS Code 协议超链接功能
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console
from backend.cli.path_utils import PathUtils
from backend.cli.output_manager import ToolOutputManager


def test_vscode_protocol():
    """测试 VS Code 协议超链接生成"""
    print("=" * 70)
    print("测试 VS Code 协议超链接")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console(file=open(os.devnull, 'w'))
    path_utils = PathUtils(project_root)

    class MockAgent:
        token_counter = None

    # 测试 VS Code 协议
    output_manager_vscode = ToolOutputManager(
        console, path_utils, MockAgent(),
        use_vscode_protocol=True  # 启用 VS Code 协议
    )

    # 测试 file:// 协议
    output_manager_file = ToolOutputManager(
        console, path_utils, MockAgent(),
        use_vscode_protocol=False  # 使用标准 file:// 协议
    )

    test_cases = [
        {
            'name': '无行号',
            'tool': 'view_file',
            'args': {'path': 'backend/agent/tool_registry.py'},
            'expected_vscode': r'vscode://file/.*tool_registry\.py',
            'expected_file': r'file://.*tool_registry\.py'
        },
        {
            'name': '带行号范围',
            'tool': 'view_file',
            'args': {
                'path': 'backend/tools/filesystem_tools/view_file.py',
                'line_range': [42, 100]
            },
            'expected_vscode': r'vscode://file/.*view_file\.py:42',
            'expected_file': r'file://.*view_file\.py'
        },
        {
            'name': '带单个行号',
            'tool': 'edit_file',
            'args': {
                'path': 'backend/cli/main.py',
                'line': 150
            },
            'expected_vscode': r'vscode://file/.*main\.py:150',
            'expected_file': r'file://.*main\.py'
        },
    ]

    import re
    all_passed = True

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 #{i}: {case['name']}")
        print(f"  工具: {case['tool']}")
        print(f"  参数: {case['args']}")

        # 测试 VS Code 协议
        formatted_vscode = output_manager_vscode._format_tool_call(case['tool'], case['args'])
        print(f"\n  VS Code 协议:")
        print(f"    {formatted_vscode}")

        # 提取超链接
        vscode_match = re.search(r'\[link=(vscode://[^\]]+)\]', formatted_vscode)
        if vscode_match:
            vscode_uri = vscode_match.group(1)
            print(f"    URI: {vscode_uri}")

            # 验证格式
            if re.match(case['expected_vscode'], vscode_uri):
                print(f"    ✓ VS Code URI 格式正确")
            else:
                print(f"    ✗ VS Code URI 格式错误！")
                print(f"      期望匹配: {case['expected_vscode']}")
                all_passed = False
        else:
            print(f"    ✗ 未找到 VS Code 超链接！")
            all_passed = False

        # 测试 file:// 协议
        formatted_file = output_manager_file._format_tool_call(case['tool'], case['args'])
        print(f"\n  File 协议:")
        print(f"    {formatted_file}")

        file_match = re.search(r'\[link=(file://[^\]]+)\]', formatted_file)
        if file_match:
            file_uri = file_match.group(1)
            print(f"    URI: {file_uri}")

            if re.match(case['expected_file'], file_uri):
                print(f"    ✓ File URI 格式正确")
            else:
                print(f"    ✗ File URI 格式错误！")
                all_passed = False
        else:
            print(f"    ✗ 未找到 file:// 超链接！")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


def test_line_number_extraction():
    """测试行号提取逻辑"""
    print("\n" + "=" * 70)
    print("测试行号提取逻辑")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console(file=open(os.devnull, 'w'))
    path_utils = PathUtils(project_root)

    class MockAgent:
        token_counter = None

    output_manager = ToolOutputManager(
        console, path_utils, MockAgent(),
        use_vscode_protocol=True
    )

    test_cases = [
        {
            'args': {'path': 'test.py', 'line_range': [42, 100]},
            'expected_line': 42,
            'description': 'line_range 列表'
        },
        {
            'args': {'path': 'test.py', 'line_range': (50, 60)},
            'expected_line': 50,
            'description': 'line_range 元组'
        },
        {
            'args': {'path': 'test.py', 'line': 123},
            'expected_line': 123,
            'description': 'line 参数'
        },
        {
            'args': {'path': 'test.py'},
            'expected_line': None,
            'description': '无行号'
        },
    ]

    import re
    all_passed = True

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 #{i}: {case['description']}")

        hyperlink = output_manager._create_file_hyperlink(
            case['args']['path'],
            line=case['args'].get('line') or (
                case['args']['line_range'][0]
                if 'line_range' in case['args'] and case['args']['line_range']
                else None
            )
        )

        print(f"  参数: {case['args']}")
        print(f"  超链接: {hyperlink}")

        # 提取行号
        uri_match = re.search(r'\[link=(vscode://file[^\]]+)\]', hyperlink)
        if uri_match:
            uri = uri_match.group(1)

            if case['expected_line'] is None:
                # 不应该包含行号
                if ':' not in uri.split('/')[-1]:
                    print(f"  ✓ 正确：无行号")
                else:
                    print(f"  ✗ 错误：不应该包含行号")
                    all_passed = False
            else:
                # 应该包含行号
                if f":{case['expected_line']}" in uri:
                    print(f"  ✓ 正确：行号 {case['expected_line']}")
                else:
                    print(f"  ✗ 错误：期望行号 {case['expected_line']}")
                    all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


def demo_vscode_links():
    """演示 VS Code 超链接效果"""
    print("\n" + "=" * 70)
    print("VS Code 超链接演示")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    console = Console()
    path_utils = PathUtils(project_root)

    class MockAgent:
        token_counter = None

    output_manager = ToolOutputManager(
        console, path_utils, MockAgent(),
        use_vscode_protocol=True
    )

    examples = [
        {
            'tool': 'view_file',
            'args': {
                'path': 'backend/agent/tool_registry.py',
                'line_range': [1, 50]
            }
        },
        {
            'tool': 'edit_file',
            'args': {
                'path': 'backend/tools/filesystem_tools/view_file.py',
                'line': 42
            }
        },
        {
            'tool': 'grep_search',
            'args': {
                'pattern': 'class.*Tool',
                'path': 'backend/tools'
            }
        },
    ]

    console.print("\n[bold cyan]🎯 模拟工具调用（VS Code 协议）[/bold cyan]\n")

    for i, example in enumerate(examples, 1):
        console.print(f"[dim]─── 调用 #{i} ───[/dim]")
        output_manager.add_tool_output(
            tool_name=example['tool'],
            output='执行成功',
            args=example['args']
        )
        console.print()

    console.print("=" * 70)
    console.print("\n[yellow]💡 使用说明:[/yellow]")
    console.print("  1. 在 VS Code 中点击路径会直接在编辑器中打开")
    console.print("  2. 如果有行号，会自动跳转到指定行")
    console.print("  3. 格式: vscode://file/absolute/path:line:column")
    console.print("  4. Cmd/Ctrl + 点击路径即可打开\n")


if __name__ == '__main__':
    result1 = test_vscode_protocol()
    result2 = test_line_number_extraction()

    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)

    if result1 and result2:
        print("🎉 所有测试通过！\n")
        # 运行演示
        demo_vscode_links()
        sys.exit(0)
    else:
        print("⚠️  部分测试失败\n")
        sys.exit(1)
