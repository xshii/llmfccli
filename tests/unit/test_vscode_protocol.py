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
from backend.cli.hyperlink import create_file_hyperlink
from backend.cli.output_manager import ToolOutputManager


def test_vscode_protocol():
    """测试 VS Code 协议超链接生成"""
    print("=" * 70)
    print("测试超链接生成功能")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path_utils = PathUtils(project_root)

    test_cases = [
        {
            'name': '无行号',
            'path': 'backend/agent/tools/registry.py',
            'line': None,
        },
        {
            'name': '带行号',
            'path': 'backend/tools/filesystem_tools/view_file.py',
            'line': 42,
        },
        {
            'name': '带行号150',
            'path': 'backend/cli/main.py',
            'line': 150,
        },
    ]

    import re
    all_passed = True

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 #{i}: {case['name']}")
        print(f"  路径: {case['path']}")
        print(f"  行号: {case['line']}")

        # 测试超链接生成
        hyperlink = create_file_hyperlink(
            path=case['path'],
            project_root=project_root,
            path_utils=path_utils,
            line=case['line']
        )

        print(f"\n  生成的超链接:")
        print(f"    {hyperlink}")

        # 提取超链接 URI
        link_match = re.search(r'\[link=(.*?)\]', hyperlink)
        if link_match:
            uri = link_match.group(1)
            print(f"    URI: {uri}")

            # 验证协议格式（file:// 或 vscode://）
            if uri.startswith('file://') or uri.startswith('vscode://file'):
                print(f"    协议格式正确")

                # 验证行号（如果有）
                if case['line'] is not None:
                    if f":{case['line']}" in hyperlink:
                        print(f"    行号 {case['line']} 包含正确")
                    else:
                        print(f"    行号缺失!")
                        all_passed = False
            else:
                print(f"    未知协议格式: {uri}")
                all_passed = False
        else:
            print(f"    未找到超链接格式!")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("所有测试通过！")
        return True
    else:
        print("部分测试失败")
        return False


def test_line_number_extraction():
    """测试行号提取逻辑"""
    print("\n" + "=" * 70)
    print("测试行号提取逻辑")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path_utils = PathUtils(project_root)

    test_cases = [
        {
            'path': 'test.py',
            'line': 42,
            'expected_line': 42,
            'description': '整数行号'
        },
        {
            'path': 'test.py',
            'line': 50,
            'expected_line': 50,
            'description': '另一个行号'
        },
        {
            'path': 'test.py',
            'line': 123,
            'expected_line': 123,
            'description': '三位数行号'
        },
        {
            'path': 'test.py',
            'line': None,
            'expected_line': None,
            'description': '无行号'
        },
    ]

    import re
    all_passed = True

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 #{i}: {case['description']}")

        hyperlink = create_file_hyperlink(
            path=case['path'],
            project_root=project_root,
            path_utils=path_utils,
            line=case['line']
        )

        print(f"  参数: path={case['path']}, line={case['line']}")
        print(f"  超链接: {hyperlink}")

        # 提取 URI
        uri_match = re.search(r'\[link=(.*?)\]', hyperlink)
        if uri_match:
            uri = uri_match.group(1)

            if case['expected_line'] is None:
                # 不应该包含行号（URI 中不应该有 :数字 在文件路径之后）
                # 简单检查：文件名后面不应该紧跟 :数字
                filename = os.path.basename(case['path'])
                if f"{filename}:" in uri and re.search(rf'{filename}:\d+', uri):
                    print(f"  错误：不应该包含行号")
                    all_passed = False
                else:
                    print(f"  正确：无行号")
            else:
                # 应该包含行号
                if f":{case['expected_line']}" in hyperlink:
                    print(f"  正确：行号 {case['expected_line']}")
                else:
                    print(f"  错误：期望行号 {case['expected_line']}")
                    all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("所有测试通过！")
        return True
    else:
        print("部分测试失败")
        return False


def demo_vscode_links():
    """演示超链接效果"""
    print("\n" + "=" * 70)
    print("超链接演示")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path_utils = PathUtils(project_root)
    console = Console()

    examples = [
        {'path': 'backend/agent/tools/registry.py', 'line': 1},
        {'path': 'backend/tools/filesystem_tools/view_file.py', 'line': 42},
        {'path': 'backend/cli/main.py', 'line': None},
    ]

    console.print("\n[bold cyan]文件超链接演示[/bold cyan]\n")

    for i, example in enumerate(examples, 1):
        hyperlink = create_file_hyperlink(
            path=example['path'],
            project_root=project_root,
            path_utils=path_utils,
            line=example['line']
        )
        console.print(f"[dim]#{i}[/dim] {hyperlink}")

    console.print("\n" + "=" * 70)
    console.print("\n[yellow]使用说明:[/yellow]")
    console.print("  1. 点击路径可在编辑器中打开")
    console.print("  2. 如果有行号，会自动跳转到指定行")
    console.print("  3. 协议由 config/feature.yaml 中的配置决定\n")


if __name__ == '__main__':
    result1 = test_vscode_protocol()
    result2 = test_line_number_extraction()

    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)

    if result1 and result2:
        print("所有测试通过！\n")
        # 运行演示
        demo_vscode_links()
        sys.exit(0)
    else:
        print("部分测试失败\n")
        sys.exit(1)
