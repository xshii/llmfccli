"""
Test Case 5: 上下文保持测试

验证 Agent 能否：
1. 记住前一轮创建的类结构
2. 在后续轮次中基于之前的上下文继续工作
3. 正确维护对话历史
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


def test_context_preservation():
    """测试上下文保持"""
    
    client = OllamaClient()
    agent = AgentLoop(client)
    
    project_root = os.path.join(os.path.dirname(__file__), 'fixtures/sample-cpp')
    agent.set_project_root(project_root)
    
    # 第 1 轮：创建 DataProcessor 类
    round1_input = """
    创建一个 DataProcessor 类，包含以下功能：
    - process(data) 方法处理数据
    - validate(data) 方法验证数据
    
    文件路径: src/data/data_processor.h 和 src/data/data_processor.cpp
    """
    
    response1 = agent.run(round1_input)
    
    # 验证第 1 轮
    header_path = os.path.join(project_root, 'src/data/data_processor.h')
    impl_path = os.path.join(project_root, 'src/data/data_processor.cpp')
    
    assert os.path.exists(header_path), "应该创建头文件"
    assert os.path.exists(impl_path), "应该创建实现文件"
    
    with open(header_path, 'r') as f:
        header_content = f.read()
    
    assert 'class DataProcessor' in header_content, "应该包含 DataProcessor 类"
    assert 'process' in header_content, "应该包含 process 方法"
    assert 'validate' in header_content, "应该包含 validate 方法"
    
    print("\n=== 第 1 轮验证 ===")
    print("✓ 创建 DataProcessor 类成功")
    print(f"✓ 头文件: {header_path}")
    print(f"✓ 实现文件: {impl_path}")
    
    # 第 2 轮：添加线程安全
    round2_input = "为 DataProcessor 类添加线程安全，使用互斥锁保护 process 和 validate 方法"
    
    response2 = agent.run(round2_input)
    
    # 验证第 2 轮
    with open(header_path, 'r') as f:
        updated_header = f.read()
    
    with open(impl_path, 'r') as f:
        updated_impl = f.read()
    
    # 检查是否添加了线程安全机制
    has_mutex = 'mutex' in updated_header.lower() or 'std::mutex' in updated_header
    has_lock = 'lock' in updated_impl.lower() or 'lock_guard' in updated_impl
    
    assert has_mutex, "应该在头文件中声明 mutex"
    assert has_lock, "应该在实现中使用锁"
    
    # 关键：检查是否仍然保留了原有的方法
    assert 'process' in updated_header, "应该保留 process 方法"
    assert 'validate' in updated_header, "应该保留 validate 方法"
    
    print("\n=== 第 2 轮验证 ===")
    print("✓ Agent 记住了第 1 轮创建的类结构")
    print("✓ 成功添加线程安全机制")
    print("✓ 保留了原有方法")
    print("✓ 上下文保持正常")
    
    # 验证对话历史
    assert len(agent.conversation_history) >= 4, \
        "对话历史应该至少包含 4 条消息（2 轮 user + 2 轮 assistant）"
    
    # 检查第 2 轮的上下文中是否包含第 1 轮的信息
    context_has_round1_info = any(
        'DataProcessor' in str(msg) 
        for msg in agent.conversation_history[-3:-1]  # 第 1 轮的消息
    )
    
    assert context_has_round1_info, "上下文应该包含第 1 轮的信息"
    
    print("✓ 对话历史维护正确")
    
    return True


if __name__ == '__main__':
    try:
        test_context_preservation()
        print("\n[PASS] Test Case 5: 上下文保持")
    except AssertionError as e:
        print(f"\n[FAIL] Test Case 5: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test Case 5: {e}")
        sys.exit(1)
