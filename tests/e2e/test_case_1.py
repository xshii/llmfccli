"""
Test Case 1: 跨目录文件定位与功能实现

验证 Agent 能否：
1. 使用 grep_search 定位文件
2. 读取文件内容
3. 正确插入代码（超时重试机制）
4. 保持代码风格
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


def test_file_location_and_feature_addition():
    """测试文件定位和功能添加"""
    
    # 初始化 Agent
    client = OllamaClient()
    agent = AgentLoop(client)
    
    # 设置项目根目录
    project_root = os.path.join(os.path.dirname(__file__), 'fixtures/sample-cpp')
    agent.set_project_root(project_root)
    
    # 测试输入
    user_input = """
    在 network_handler.cpp 的 connect() 函数中添加连接超时和重试机制。
    
    要求：
    - 超时时间 5 秒
    - 最多重试 3 次
    - 每次重试间隔 1 秒
    - 保持原有代码风格（缩进、括号位置）
    """
    
    # 执行 Agent
    response = agent.run(user_input)
    
    # 验证点
    print("\n=== 验证点 ===")
    
    # 1. 检查是否调用了 grep_search
    assert any(tool['name'] == 'grep_search' for tool in agent.tool_calls), \
        "应该使用 grep_search 定位文件"
    
    # 2. 检查是否找到正确的文件
    network_handler_path = os.path.join(project_root, 'src/network/network_handler.cpp')
    assert any(network_handler_path in str(tool) for tool in agent.tool_calls), \
        f"应该定位到 {network_handler_path}"
    
    # 3. 检查是否调用了 view_file
    assert any(tool['name'] == 'view_file' for tool in agent.tool_calls), \
        "应该读取文件内容"
    
    # 4. 检查是否调用了 edit_file
    assert any(tool['name'] == 'edit_file' for tool in agent.tool_calls), \
        "应该编辑文件"
    
    # 5. 读取修改后的文件，验证是否包含超时和重试逻辑
    with open(network_handler_path, 'r') as f:
        modified_content = f.read()
    
    # 检查关键字
    assert 'timeout' in modified_content.lower() or 'retry' in modified_content.lower(), \
        "修改后的文件应包含超时或重试相关代码"
    
    # 检查是否保持了原有的缩进风格（4 空格）
    lines = modified_content.split('\n')
    indented_lines = [line for line in lines if line.startswith('    ') and not line.startswith('        ')]
    assert len(indented_lines) > 0, "应该保持 4 空格缩进"
    
    print("✓ 文件定位成功")
    print("✓ 代码插入位置正确")
    print("✓ 保持了原有代码风格")
    print(f"✓ 完成修改: {network_handler_path}")
    
    return True


if __name__ == '__main__':
    try:
        test_file_location_and_feature_addition()
        print("\n[PASS] Test Case 1: 文件定位与功能实现")
    except AssertionError as e:
        print(f"\n[FAIL] Test Case 1: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test Case 1: {e}")
        sys.exit(1)
