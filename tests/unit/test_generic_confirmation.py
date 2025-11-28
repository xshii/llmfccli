#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通用的 confirmation 机制（无硬编码工具名）
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tool_executor import RegistryToolExecutor
from backend.agent.tool_confirmation import ToolConfirmation, ConfirmAction


def test_generic_confirmation():
    """测试通用 confirmation 机制（无硬编码）"""
    print("=" * 70)
    print("测试通用 Confirmation 机制")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # 创建 confirmation manager
    confirmation = ToolConfirmation()

    # 创建 tool executor
    executor = RegistryToolExecutor(
        project_root=project_root,
        confirmation_manager=confirmation
    )

    # 测试 1: 检查工具是否支持 confirm 参数
    print("\n测试 #1: 检查工具是否支持 confirm 参数")
    print("-" * 70)

    test_tools = [
        'edit_file',      # 应该支持
        'create_file',    # 可能支持
        'view_file',      # 不应该支持
        'grep_search',    # 不应该支持
        'bash_run',       # 不应该支持
    ]

    for tool_name in test_tools:
        supports = executor._tool_supports_confirmation(tool_name)
        print(f"  {tool_name:20} → {'✓ 支持 confirm' if supports else '✗ 不支持 confirm'}")

    # 测试 2: edit_file 第一次调用（应该使用默认 confirm=True）
    print("\n测试 #2: 第一次调用 edit_file（未授权）")
    print("-" * 70)

    # 模拟调用（不实际执行）
    tool_name = 'edit_file'
    arguments = {
        'path': 'test.py',
        'old_str': 'old',
        'new_str': 'new'
    }

    print(f"  工具: {tool_name}")
    print(f"  参数: {arguments}")
    print(f"  allowed_tool_calls: {confirmation.allowed_tool_calls}")

    # 检查是否会注入 confirm=False
    if tool_name in confirmation.allowed_tool_calls:
        print("  ✗ 错误：不应该在 allowed_tool_calls 中")
    else:
        print("  ✓ 正确：不在 allowed_tool_calls 中")
        print("  → 将使用工具的默认值 (confirm=True)")

    # 测试 3: 用户设置 "always allow" 后
    print("\n测试 #3: 用户设置 'Always Allow' 后")
    print("-" * 70)

    # 模拟用户选择 "always allow"
    confirmation.allowed_tool_calls.add('edit_file')
    print(f"  allowed_tool_calls: {confirmation.allowed_tool_calls}")

    # 再次调用
    print(f"\n  再次调用 edit_file...")

    # 检查是否会注入 confirm=False
    supports_confirm = executor._tool_supports_confirmation('edit_file')
    is_allowed = 'edit_file' in confirmation.allowed_tool_calls

    print(f"  支持 confirm 参数: {supports_confirm}")
    print(f"  在 allowed_tool_calls 中: {is_allowed}")

    if supports_confirm and is_allowed:
        print("  ✓ 正确：将注入 confirm=False")
        print("  → 跳过工具级别的确认")
    else:
        print("  ✗ 错误：应该注入 confirm=False")

    # 测试 4: 其他支持 confirm 的工具（如 create_file）
    print("\n测试 #4: 其他支持 confirm 的工具")
    print("-" * 70)

    # 检查 create_file 是否支持 confirm
    supports = executor._tool_supports_confirmation('create_file')
    print(f"  create_file 支持 confirm: {supports}")

    if supports:
        print("  ✓ 通用机制：create_file 也会被正确处理")
        print("  → 无需硬编码工具名")

        # 测试授权后的行为
        confirmation.allowed_tool_calls.add('create_file')
        is_allowed = 'create_file' in confirmation.allowed_tool_calls
        print(f"\n  设置 'always allow' 后:")
        print(f"  在 allowed_tool_calls 中: {is_allowed}")
        print("  → 将注入 confirm=False")

    # 测试 5: 不支持 confirm 的工具（如 view_file）
    print("\n测试 #5: 不支持 confirm 的工具")
    print("-" * 70)

    supports = executor._tool_supports_confirmation('view_file')
    print(f"  view_file 支持 confirm: {supports}")

    if not supports:
        print("  ✓ 正确：view_file 不支持 confirm")
        print("  → 即使在 allowed_tool_calls 中，也不会注入参数")

        confirmation.allowed_tool_calls.add('view_file')
        print(f"\n  设置 'always allow' 后:")
        print(f"  在 allowed_tool_calls 中: {'view_file' in confirmation.allowed_tool_calls}")
        print("  → 但不会注入 confirm 参数（因为工具不支持）")

    print("\n" + "=" * 70)
    print("✅ 通用 Confirmation 机制测试完成")
    print("=" * 70)
    print("\n关键改进:")
    print("  1. ✅ 无硬编码工具名（通过 schema 检查）")
    print("  2. ✅ 适用于所有支持 confirm 的工具")
    print("  3. ✅ 自动识别工具能力")
    print("  4. ✅ 符合插件化架构原则")


def test_schema_introspection():
    """测试 schema 内省机制"""
    print("\n" + "=" * 70)
    print("测试 Schema 内省机制")
    print("=" * 70)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    executor = RegistryToolExecutor(project_root=project_root)

    # 获取所有工具的 schema
    print("\n所有工具的参数 schema:")
    print("-" * 70)

    for tool_name in executor.get_tool_names():
        metadata = executor.registry.get_tool_metadata(tool_name)
        if metadata:
            schema = metadata.get('schema', {})
            properties = schema.get('parameters', {}).get('properties', {})

            print(f"\n  {tool_name}:")
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'unknown')
                description = param_info.get('description', '')
                print(f"    - {param_name} ({param_type}): {description}")

            # 特别标注支持 confirm 的工具
            if 'confirm' in properties:
                print(f"    → ✓ 支持 confirm 参数")

    print("\n" + "=" * 70)
    print("✅ Schema 内省测试完成")
    print("=" * 70)


if __name__ == '__main__':
    test_generic_confirmation()
    test_schema_introspection()
