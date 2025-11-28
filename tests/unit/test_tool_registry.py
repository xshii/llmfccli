#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的 ToolRegistry 架构
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tool_registry import ToolRegistry


def test_tool_discovery():
    """测试工具自动发现"""
    print("=" * 60)
    print("Test 1: Tool Auto-Discovery")
    print("=" * 60)

    # 创建注册器
    registry = ToolRegistry(project_root='/tmp/test')

    # 检查是否发现了所有工具
    tools = registry.list_tools()
    print(f"\n发现的工具 ({len(tools)}): {', '.join(sorted(tools))}")

    # 应该至少包含这些核心工具
    expected_tools = {'view_file', 'edit_file', 'create_file', 'grep_search', 'list_dir', 'bash_run', 'compact_last'}
    found_tools = set(tools)

    missing = expected_tools - found_tools
    if missing:
        print(f"\n❌ 缺少工具: {missing}")
        return False
    else:
        print(f"\n✅ 所有核心工具已发现")

    return True


def test_tool_metadata():
    """测试工具元数据"""
    print("\n" + "=" * 60)
    print("Test 2: Tool Metadata")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 获取所有元数据
    metadata = registry.get_all_metadata()

    print(f"\n工具元数据 ({len(metadata)} tools):")
    for name, meta in sorted(metadata.items()):
        print(f"  - {name:15} | {meta.category:12} | {meta.description[:40]}...")

    # 检查分类
    by_category = registry.get_tools_by_category()
    print(f"\n按类别分组:")
    for category, tool_list in sorted(by_category.items()):
        tool_names = ', '.join(t.name for t in tool_list)
        print(f"  {category:12}: {tool_names}")

    print("\n✅ 元数据读取成功")
    return True


def test_openai_schemas():
    """测试 OpenAI schema 生成"""
    print("\n" + "=" * 60)
    print("Test 3: OpenAI Schema Generation")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 获取所有 OpenAI schemas
    schemas = registry.get_openai_schemas()

    print(f"\n生成的 OpenAI Schemas ({len(schemas)} tools):")
    for schema in sorted(schemas, key=lambda x: x['function']['name']):
        func = schema['function']
        params = func['parameters']
        required = params.get('required', [])

        print(f"\n  Tool: {func['name']}")
        print(f"    Description: {func['description'][:60]}...")
        print(f"    Parameters: {list(params.get('properties', {}).keys())}")
        print(f"    Required: {required}")

    print("\n✅ Schema 生成成功")
    return True


def test_lazy_loading():
    """测试懒加载"""
    print("\n" + "=" * 60)
    print("Test 4: Lazy Loading")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 初始状态：没有实例化任何工具
    print(f"\n初始化后实例数: {len(registry._tool_instances)}")
    if len(registry._tool_instances) != 0:
        print("❌ 初始化时不应该有任何实例")
        return False

    # 获取一个工具（触发懒加载）
    tool = registry.get('view_file')
    print(f"获取 view_file 后实例数: {len(registry._tool_instances)}")

    if tool is None:
        print("❌ 无法加载 view_file 工具")
        return False

    if len(registry._tool_instances) != 1:
        print("❌ 应该只有 1 个实例")
        return False

    # 再次获取同一个工具（应该返回缓存）
    tool2 = registry.get('view_file')
    if tool is not tool2:
        print("❌ 应该返回同一个实例")
        return False

    print(f"再次获取后实例数: {len(registry._tool_instances)} (缓存命中)")

    print("\n✅ 懒加载正常工作")
    return True


def test_tool_execution():
    """测试工具执行"""
    print("\n" + "=" * 60)
    print("Test 5: Tool Execution")
    print("=" * 60)

    # 使用实际的项目根目录
    test_project_root = os.path.join(os.path.dirname(__file__), '../..')
    registry = ToolRegistry(project_root=test_project_root)

    # 测试 list_dir 工具
    print("\n执行 list_dir 工具...")
    result = registry.execute('list_dir', {'path': '.', 'max_depth': 1})

    if 'success' in result and result['success']:
        print(f"✅ list_dir 成功: 找到 {result.get('total', 0)} 个项目")
        print(f"   前 5 项: {result.get('items', [])[:5]}")
    else:
        print(f"❌ list_dir 失败: {result}")
        return False

    return True


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("测试新的 ToolRegistry 插件化架构")
    print("=" * 60)

    tests = [
        test_tool_discovery,
        test_tool_metadata,
        test_openai_schemas,
        test_lazy_loading,
        test_tool_execution,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)

    if all(results):
        print("\n🎉 所有测试通过！新 ToolRegistry 架构工作正常！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败")
        sys.exit(1)
