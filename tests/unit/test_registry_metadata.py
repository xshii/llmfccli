#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ToolRegistry.get_tool_metadata 方法
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools import registry


def test_registry_get_tool_metadata():
    """测试 registry.get_tool_metadata 方法"""

    # 初始化 registry
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    registry.initialize(project_root)

    print("测试 registry.get_tool_metadata 方法")
    print("=" * 60)

    # Test 1: 检查方法存在
    print("\n1. 检查方法是否存在...")
    assert hasattr(registry, 'get_tool_metadata'), "❌ registry 没有 get_tool_metadata 方法"
    print("   ✓ registry 有 get_tool_metadata 方法")

    # Test 2: 测试获取已存在的工具元数据
    print("\n2. 测试获取 view_file 工具元数据...")
    metadata = registry.get_tool_metadata('view_file')
    assert metadata is not None, "❌ get_tool_metadata('view_file') 返回 None"
    print(f"   ✓ 成功获取元数据")
    print(f"   - name: {metadata.get('name')}")
    print(f"   - category: {metadata.get('category')}")
    print(f"   - description: {metadata.get('description')[:50]}...")

    # Test 3: 检查 schema 结构
    print("\n3. 检查 schema 结构...")
    schema = metadata.get('schema')
    assert schema is not None, "❌ metadata 没有 schema"
    assert 'function' in schema, "❌ schema 没有 function 字段"
    assert 'parameters' in schema['function'], "❌ schema.function 没有 parameters"
    assert 'properties' in schema['function']['parameters'], "❌ schema.function.parameters 没有 properties"
    print("   ✓ schema 结构正确")
    print(f"   - schema keys: {list(schema.keys())}")
    print(f"   - function keys: {list(schema['function'].keys())}")
    print(f"   - parameters: {list(schema['function']['parameters']['properties'].keys())}")

    # Test 4: 测试路径参数的 format 标记
    print("\n4. 检查路径参数是否标记为 filepath...")
    properties = schema['function']['parameters']['properties']
    if 'path' in properties:
        path_format = properties['path'].get('format')
        print(f"   - path format: {path_format}")
        if path_format == 'filepath':
            print("   ✓ path 参数正确标记为 filepath")
        else:
            print("   ⚠ path 参数未标记为 filepath（这是可选的）")

    # Test 5: 测试不存在的工具
    print("\n5. 测试不存在的工具...")
    metadata = registry.get_tool_metadata('non_existent_tool')
    assert metadata is None, "❌ 不存在的工具应该返回 None"
    print("   ✓ 不存在的工具正确返回 None")

    # Test 6: 测试 CLI 中实际使用的方式
    print("\n6. 模拟 CLI _confirm_tool_execution 中的使用...")
    tool_name = 'view_file'
    tool_metadata = registry.get_tool_metadata(tool_name)
    param_formats = {}

    if tool_metadata:
        properties = tool_metadata.get('schema', {}).get('function', {}).get('parameters', {}).get('properties', {})
        for param_name, param_info in properties.items():
            if param_info.get('format') == 'filepath':
                param_formats[param_name] = 'filepath'

    print(f"   ✓ 成功提取参数格式信息")
    print(f"   - filepath 参数: {list(param_formats.keys())}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")


if __name__ == '__main__':
    test_registry_get_tool_metadata()
