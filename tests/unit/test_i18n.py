#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具的多语言支持
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools import registry
from backend.utils.i18n import I18n


def test_tool_i18n():
    """测试工具的多语言描述"""

    # 测试项目根目录
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')

    print("=" * 60)
    print("测试工具多语言支持")
    print("=" * 60)

    # Test 1: 测试中文（默认）
    print("\n[Test 1] 测试中文描述（默认）")
    I18n.initialize(language='zh')
    registry.initialize(project_root)

    schemas = registry.get_schemas()
    view_file_schema = next(s for s in schemas if s['function']['name'] == 'view_file')

    print(f"   当前语言: {I18n.get_language()}")
    print(f"   工具名称: {view_file_schema['function']['name']}")
    print(f"   工具描述: {view_file_schema['function']['description']}")
    print(f"   path 参数描述: {view_file_schema['function']['parameters']['properties']['path']['description']}")

    assert I18n.get_language() == 'zh', "语言应该是中文"
    assert '读取文件内容' in view_file_schema['function']['description'], "描述应该是中文"
    assert '文件路径' in view_file_schema['function']['parameters']['properties']['path']['description'], "参数描述应该是中文"
    print("   ✓ 中文描述正确")

    # Test 2: 测试英文
    print("\n[Test 2] 测试英文描述")
    I18n.set_language('en')

    # 重新初始化 registry 以重新生成 schema
    registry.initialize(project_root)
    schemas = registry.get_schemas()
    view_file_schema = next(s for s in schemas if s['function']['name'] == 'view_file')

    print(f"   当前语言: {I18n.get_language()}")
    print(f"   工具名称: {view_file_schema['function']['name']}")
    print(f"   工具描述: {view_file_schema['function']['description']}")
    print(f"   path 参数描述: {view_file_schema['function']['parameters']['properties']['path']['description']}")

    assert I18n.get_language() == 'en', "语言应该是英文"
    assert 'Read file contents' in view_file_schema['function']['description'], "描述应该是英文"
    assert 'File path' in view_file_schema['function']['parameters']['properties']['path']['description'], "参数描述应该是英文"
    print("   ✓ 英文描述正确")

    # Test 3: 测试 edit_file 工具
    print("\n[Test 3] 测试 edit_file 工具的多语言支持")

    # 中文
    I18n.set_language('zh')
    registry.initialize(project_root)
    schemas = registry.get_schemas()
    edit_file_schema = next(s for s in schemas if s['function']['name'] == 'edit_file')

    print(f"   [中文] 工具描述: {edit_file_schema['function']['description']}")
    print(f"   [中文] old_str 参数: {edit_file_schema['function']['parameters']['properties']['old_str']['description']}")

    assert '编辑文件' in edit_file_schema['function']['description'], "edit_file 描述应该是中文"
    assert '替换' in edit_file_schema['function']['parameters']['properties']['old_str']['description'], "old_str 参数应该是中文"

    # 英文
    I18n.set_language('en')
    registry.initialize(project_root)
    schemas = registry.get_schemas()
    edit_file_schema = next(s for s in schemas if s['function']['name'] == 'edit_file')

    print(f"   [英文] 工具描述: {edit_file_schema['function']['description']}")
    print(f"   [英文] old_str 参数: {edit_file_schema['function']['parameters']['properties']['old_str']['description']}")

    assert 'Edit file' in edit_file_schema['function']['description'], "edit_file 描述应该是英文"
    assert 'replace' in edit_file_schema['function']['parameters']['properties']['old_str']['description'].lower(), "old_str 参数应该是英文"

    print("   ✓ edit_file 多语言支持正确")

    # Test 4: 测试所有文件系统工具
    print("\n[Test 4] 检查所有文件系统工具的多语言支持")

    tool_names = ['view_file', 'edit_file', 'create_file', 'list_dir', 'grep_search']

    for tool_name in tool_names:
        # 测试中文
        I18n.set_language('zh')
        registry.initialize(project_root)
        metadata = registry.get_tool_metadata(tool_name)
        assert metadata is not None, f"{tool_name} 元数据不存在"

        zh_desc = metadata['description']

        # 测试英文
        I18n.set_language('en')
        registry.initialize(project_root)
        metadata = registry.get_tool_metadata(tool_name)

        en_desc = metadata['description']

        print(f"   {tool_name}:")
        print(f"     中文: {zh_desc}")
        print(f"     英文: {en_desc}")

        assert zh_desc != en_desc, f"{tool_name} 的中英文描述应该不同"

    print("   ✓ 所有工具都有中英文描述")

    # Test 5: 测试环境变量配置
    print("\n[Test 5] 测试环境变量配置")

    # 设置环境变量
    os.environ['CLAUDE_QWEN_LANG'] = 'en'
    I18n._current_language = None  # 重置
    I18n.initialize()

    print(f"   环境变量 CLAUDE_QWEN_LANG=en")
    print(f"   检测到的语言: {I18n.get_language()}")

    assert I18n.get_language() == 'en', "应该从环境变量读取语言"

    # 清理环境变量
    os.environ.pop('CLAUDE_QWEN_LANG', None)
    I18n._current_language = None
    I18n.initialize()

    print(f"   清除环境变量后的语言: {I18n.get_language()}")
    assert I18n.get_language() == 'zh', "默认应该是中文"

    print("   ✓ 环境变量配置正确")

    print("\n" + "=" * 60)
    print("✅ 所有多语言测试通过！")
    print("=" * 60)
    print("\n总结:")
    print("  ✓ 中文描述正确")
    print("  ✓ 英文描述正确")
    print("  ✓ 语言可以动态切换")
    print("  ✓ 所有文件系统工具都支持双语")
    print("  ✓ 环境变量配置生效")


if __name__ == '__main__':
    test_tool_i18n()
