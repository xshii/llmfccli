"""
Test Case 4: 模块级集成测试生成

验证 Agent 能否：
1. 识别模块范围（多个文件）
2. 分析模块间依赖关系
3. 生成集成测试
4. 包含 mock 依赖
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


def test_integration_test_generation():
    """测试集成测试生成"""
    
    client = OllamaClient()
    agent = AgentLoop(client)
    
    project_root = os.path.join(os.path.dirname(__file__), 'fixtures/sample-cpp')
    agent.set_project_root(project_root)
    
    user_input = "为 HTTP 模块生成集成测试"
    
    response = agent.run(user_input)
    
    print("\n=== 验证点 ===")
    
    # 1. 检查是否搜索 HTTP 模块相关文件
    grep_calls = [tool for tool in agent.tool_calls if tool['name'] == 'grep_search']
    http_searches = [call for call in grep_calls if 'http' in str(call).lower()]
    assert len(http_searches) > 0, "应该搜索 HTTP 相关文件"
    
    # 2. 检查是否分析依赖关系
    dep_calls = [tool for tool in agent.tool_calls if tool['name'] == 'get_dependencies']
    assert len(dep_calls) > 0, "应该分析依赖关系"
    
    # 3. 检查是否识别到 HTTP 模块依赖 NetworkHandler
    view_calls = [tool for tool in agent.tool_calls if tool['name'] == 'view_file']
    viewed_files = [str(call) for call in view_calls]
    
    http_module_viewed = any('http_module' in f for f in viewed_files)
    network_viewed = any('network_handler' in f for f in viewed_files)
    
    assert http_module_viewed, "应该查看 HTTP 模块文件"
    assert network_viewed, "应该识别 NetworkHandler 依赖"
    
    # 4. 验证集成测试文件
    test_file_path = os.path.join(project_root, 'tests/integration/http_module_test.cpp')
    assert os.path.exists(test_file_path), f"集成测试文件应该存在: {test_file_path}"
    
    with open(test_file_path, 'r') as f:
        test_content = f.read()
    
    # 检查 GTest 框架
    assert '#include <gtest/gtest.h>' in test_content, "应该使用 GTest"
    
    # 检查是否包含 HTTP 模块
    assert '#include' in test_content and 'http_module.h' in test_content, \
        "应该包含 http_module.h"
    
    # 检查是否测试模块边界行为
    integration_keywords = ['request', 'response', 'connect', 'send']
    tested_behaviors = sum(1 for kw in integration_keywords if kw in test_content.lower())
    assert tested_behaviors >= 2, "应该测试至少 2 个模块边界行为"
    
    # 检查是否包含 Mock（可选，但推荐）
    has_mock = 'mock' in test_content.lower() or 'fake' in test_content.lower()
    
    print(f"✓ HTTP 模块搜索: {len(http_searches)} 次")
    print(f"✓ 依赖分析: {len(dep_calls)} 次")
    print("✓ 模块边界识别准确")
    print(f"✓ 测试文件创建: {test_file_path}")
    print(f"✓ 测试行为覆盖: {tested_behaviors} 个")
    if has_mock:
        print("✓ 包含 Mock 策略")
    
    return True


if __name__ == '__main__':
    try:
        test_integration_test_generation()
        print("\n[PASS] Test Case 4: 集成测试生成")
    except AssertionError as e:
        print(f"\n[FAIL] Test Case 4: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test Case 4: {e}")
        sys.exit(1)
