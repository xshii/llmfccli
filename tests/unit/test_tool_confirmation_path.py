#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具确认时的路径显示和超链接功能
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools import registry
from backend.cli.path_utils import PathUtils
from backend.cli.output_manager import ToolOutputManager
from rich.console import Console


def test_path_hyperlink_in_confirmation():
    """测试工具确认时的路径超链接功能"""

    # 设置环境
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    registry.initialize(project_root)

    # 创建 PathUtils 和 ToolOutputManager
    path_utils = PathUtils(project_root)
    console = Console()
    output_manager = ToolOutputManager(console, path_utils, agent=None)

    # 启用 VSCode 协议
    output_manager.use_vscode_protocol = True

    print("=" * 60)
    print("测试工具确认时的路径显示和超链接")
    print("=" * 60)

    # Test 1: 检查 view_file 工具的 schema
    print("\n[Test 1] 检查 view_file 工具 schema 中的 filepath 标记")
    metadata = registry.get_tool_metadata('view_file')
    assert metadata is not None, "view_file 工具元数据不存在"

    properties = metadata.get('schema', {}).get('function', {}).get('parameters', {}).get('properties', {})
    assert 'path' in properties, "view_file 缺少 path 参数"
    assert properties['path'].get('format') == 'filepath', "path 参数没有标记为 filepath"
    print("   ✓ view_file.path 正确标记为 filepath")

    # Test 2: 检查 edit_file 工具的 schema
    print("\n[Test 2] 检查 edit_file 工具 schema 中的 filepath 标记")
    metadata = registry.get_tool_metadata('edit_file')
    assert metadata is not None, "edit_file 工具元数据不存在"

    properties = metadata.get('schema', {}).get('function', {}).get('parameters', {}).get('properties', {})
    assert 'path' in properties, "edit_file 缺少 path 参数"
    assert properties['path'].get('format') == 'filepath', "path 参数没有标记为 filepath"
    print("   ✓ edit_file.path 正确标记为 filepath")

    # Test 3: 模拟 _confirm_tool_execution 中的路径处理逻辑
    print("\n[Test 3] 模拟工具确认中的路径处理逻辑")

    tool_name = 'view_file'
    arguments = {
        'path': '/home/user/llmfccli/backend/agent/tools.py',
        'line_range': (42, 100)
    }

    # 获取工具 metadata
    tool_metadata = registry.get_tool_metadata(tool_name)
    param_formats = {}

    if tool_metadata:
        properties = tool_metadata.get('schema', {}).get('function', {}).get('parameters', {}).get('properties', {})
        for param_name, param_info in properties.items():
            if param_info.get('format') == 'filepath':
                param_formats[param_name] = 'filepath'

    print(f"   - 检测到的 filepath 参数: {list(param_formats.keys())}")
    assert 'path' in param_formats, "未能识别 path 为 filepath 参数"

    # 提取行号
    line_number = None
    if 'line_range' in arguments and arguments['line_range']:
        line_range = arguments['line_range']
        if isinstance(line_range, (tuple, list)) and len(line_range) >= 1:
            line_number = line_range[0]

    print(f"   - 提取的行号: {line_number}")
    assert line_number == 42, "未能正确提取行号"

    # 格式化路径参数
    args_display = []
    for key, value in arguments.items():
        value_str = str(value)

        if param_formats.get(key) == 'filepath' and ('/' in value_str or '\\' in value_str):
            # 使用超链接格式化
            value_str = output_manager._create_file_hyperlink(value_str, line=line_number)

        args_display.append(f"  • {key}: {value_str}")

    args_text = "\n".join(args_display)

    print(f"\n   格式化后的参数显示:")
    for line in args_display:
        print(f"     {line}")

    # 验证超链接格式
    assert 'vscode://file' in args_display[0], "路径未转换为 VSCode 超链接"
    assert ':42' in args_display[0], "超链接未包含行号"
    assert '[link=' in args_display[0], "未使用 Rich 超链接格式"
    print("\n   ✓ 路径成功转换为带行号的 VSCode 超链接")

    # Test 4: 测试路径压缩
    print("\n[Test 4] 测试路径压缩效果")

    long_path = '/home/user/llmfccli/backend/agent/tools/filesystem/view_file.py'
    compressed = path_utils.compress_path(long_path)
    print(f"   原始路径: {long_path}")
    print(f"   压缩路径: {compressed}")
    assert len(compressed) < len(long_path), "路径未被压缩"
    assert '...' in compressed, "压缩路径应包含 ..."
    print("   ✓ 路径压缩正常工作")

    # Test 5: 测试项目内路径
    print("\n[Test 5] 测试项目内路径的相对路径显示")

    project_file = os.path.join(project_root, 'src/network_handler.cpp')
    hyperlink = output_manager._create_file_hyperlink(project_file, line=25)
    print(f"   项目文件: {project_file}")
    print(f"   超链接: {hyperlink}")

    # 应该包含压缩的相对路径
    assert 'vscode://file' in hyperlink, "未使用 VSCode 协议"
    assert '[link=' in hyperlink, "未使用 Rich 超链接"
    print("   ✓ 项目内文件生成超链接成功")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    print("\n总结:")
    print("  ✓ 工具 schema 正确标记 filepath 格式")
    print("  ✓ 路径参数自动识别并生成超链接")
    print("  ✓ 行号信息正确提取并加入超链接")
    print("  ✓ 路径智能压缩（项目内用相对路径）")
    print("  ✓ VSCode 协议超链接格式正确")


if __name__ == '__main__':
    test_path_hyperlink_in_confirmation()
