# -*- coding: utf-8 -*-
"""
Test Case 6: 错误恢复测试

验证 Agent 能否：
1. 在编译错误修复失败 3 次后停止
2. 提示用户而非继续循环
3. 保存上下文到 .claude_session
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


def test_error_recovery():
    """测试错误恢复机制"""
    
    client = OllamaClient()
    agent = AgentLoop(client)
    
    project_root = os.path.join(os.path.dirname(__file__), 'fixtures/sample-cpp')
    agent.set_project_root(project_root)
    
    # 创建一个无法自动修复的复杂错误
    broken_file = os.path.join(project_root, 'src/broken.cpp')
    with open(broken_file, 'w', encoding='utf-8') as f:
        f.write("""
#include <iostream>

// 故意的复杂错误：缺少模板定义
template<typename T>
class Container;

void test() {
    Container<int> c;  // 链接错误：未定义的模板
    c.process();
}
""")
    
    user_input = "编译项目并修复所有错误"
    
    # 设置最大重试次数为 3
    agent.set_max_retries(3)
    
    response = agent.run(user_input)
    
    print("\n=== 验证点 ===")
    
    # 1. 检查编译尝试次数不超过 4 次（1 初始 + 3 重试）
    compile_attempts = len([
        tool for tool in agent.tool_calls 
        if tool['name'] in ['bash_run', 'cmake_build']
        and ('cmake' in str(tool) or 'make' in str(tool))
    ])
    
    assert compile_attempts <= 4, \
        f"编译尝试次数不应超过 4 次，实际: {compile_attempts}"
    
    # 2. 检查是否停止了循环
    assert agent.stopped_due_to_max_retries, \
        "应该因达到最大重试次数而停止"
    
    # 3. 检查是否保存了 session
    session_file = os.path.join(project_root, '.claude_session')
    assert os.path.exists(session_file), \
        f"应该保存 session 文件: {session_file}"

    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    # 验证 session 数据完整性
    assert 'timestamp' in session_data, "session 应包含时间戳"
    assert 'active_files' in session_data, "session 应包含活动文件"
    assert 'last_error' in session_data, "session 应包含最后错误"
    assert 'attempted_fixes' in session_data, "session 应包含尝试的修复"
    
    # 4. 检查是否提示了用户
    assert 'unable to fix' in response.lower() or 'failed' in response.lower(), \
        "应该提示用户修复失败"
    
    # 5. 验证没有死循环
    total_tool_calls = len(agent.tool_calls)
    assert total_tool_calls < 50, \
        f"工具调用总数过多，可能存在死循环: {total_tool_calls}"
    
    print(f"✓ 编译尝试: {compile_attempts} 次")
    print("✓ 正确停止循环")
    print(f"✓ 保存 session: {session_file}")
    print("✓ 提示用户失败信息")
    print("✓ 避免了死循环")
    
    # 清理
    os.remove(broken_file)
    if os.path.exists(session_file):
        os.remove(session_file)
    
    return True


if __name__ == '__main__':
    try:
        test_error_recovery()
        print("\n[PASS] Test Case 6: 错误恢复")
    except AssertionError as e:
        print(f"\n[FAIL] Test Case 6: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test Case 6: {e}")
        sys.exit(1)
