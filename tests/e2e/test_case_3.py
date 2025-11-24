# -*- coding: utf-8 -*-
"""
Test Case 3: 基于打开文件的 UT 生成

验证 Agent 能否：
1. 获取 VSCode 当前活动文件
2. 分析函数签名（public 接口）
3. 生成符合 GTest 规范的测试
4. 覆盖边界条件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


def test_unit_test_generation():
    """测试单元测试生成"""
    
    client = OllamaClient()
    agent = AgentLoop(client)
    
    project_root = os.path.join(os.path.dirname(__file__), 'fixtures/sample-cpp')
    agent.set_project_root(project_root)
    
    # 模拟 VSCode 当前打开 json_parser.cpp
    active_file = os.path.join(project_root, 'src/parser/json_parser.cpp')
    agent.set_active_file(active_file)
    
    user_input = "为当前文件生成单元测试"
    
    response = agent.run(user_input)
    
    print("\n=== 验证点 ===")
    
    # 1. 检查是否调用了 get_active_file
    assert any(tool['name'] == 'get_active_file' for tool in agent.tool_calls), \
        "应该调用 get_active_file"
    
    # 2. 检查是否分析了代码结构
    parse_calls = [tool for tool in agent.tool_calls 
                   if tool['name'] in ['parse_cpp', 'find_functions']]
    assert len(parse_calls) > 0, "应该分析代码结构"
    
    # 3. 检查是否创建了测试文件
    create_calls = [tool for tool in agent.tool_calls if tool['name'] == 'create_file']
    test_file_created = any('test' in str(call).lower() for call in create_calls)
    assert test_file_created, "应该创建测试文件"
    
    # 4. 验证测试文件内容
    test_file_path = os.path.join(project_root, 'tests/parser/json_parser_test.cpp')
    assert os.path.exists(test_file_path), f"测试文件应该存在: {test_file_path}"

    with open(test_file_path, 'r', encoding='utf-8') as f:
        test_content = f.read()
    
    # 检查 GTest 框架使用
    assert '#include <gtest/gtest.h>' in test_content, "应该包含 GTest 头文件"
    assert 'TEST(' in test_content or 'TEST_F(' in test_content, "应该包含 GTest 测试用例"
    
    # 检查是否测试了主要函数
    assert 'parse' in test_content.lower(), "应该测试 parse() 函数"
    assert 'validate' in test_content.lower(), "应该测试 validate() 函数"
    
    # 检查边界条件测试
    boundary_keywords = ['empty', 'null', 'invalid', 'edge']
    has_boundary_tests = any(keyword in test_content.lower() for keyword in boundary_keywords)
    assert has_boundary_tests, "应该包含边界条件测试"
    
    print("✓ 获取活动文件成功")
    print("✓ 代码结构分析准确")
    print(f"✓ 测试文件创建: {test_file_path}")
    print("✓ 符合 GTest 规范")
    print("✓ 覆盖关键函数")
    print("✓ 包含边界条件测试")
    
    return True


if __name__ == '__main__':
    try:
        test_unit_test_generation()
        print("\n[PASS] Test Case 3: 单元测试生成")
    except AssertionError as e:
        print(f"\n[FAIL] Test Case 3: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test Case 3: {e}")
        sys.exit(1)
