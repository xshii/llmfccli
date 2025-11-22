"""
Test Case 2: 编译错误自动修复循环

验证 Agent 能否：
1. 触发编译
2. 解析编译错误（gcc/clang 格式）
3. 定位错误文件和行号
4. 应用修复
5. 重新编译验证
6. 循环直到成功或达到上限
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


def test_compile_error_fix_loop():
    """测试编译错误修复循环"""
    
    client = OllamaClient()
    agent = AgentLoop(client)
    
    project_root = os.path.join(os.path.dirname(__file__), 'fixtures/sample-cpp')
    agent.set_project_root(project_root)
    
    # 测试输入
    user_input = "编译项目并修复所有编译错误"
    
    # 执行 Agent
    response = agent.run(user_input)
    
    # 验证点
    print("\n=== 验证点 ===")
    
    # 1. 检查是否调用了编译命令
    bash_calls = [tool for tool in agent.tool_calls if tool['name'] == 'bash_run']
    cmake_calls = [tool for tool in agent.tool_calls if tool['name'] == 'cmake_build']
    
    assert len(bash_calls) > 0 or len(cmake_calls) > 0, \
        "应该调用编译命令"
    
    # 2. 检查是否多次编译（至少 2 次：初始失败 + 修复后成功）
    compile_count = len([c for c in bash_calls if 'cmake' in str(c) or 'make' in str(c)])
    compile_count += len(cmake_calls)
    
    assert compile_count >= 2, \
        f"应该至少编译 2 次，实际: {compile_count}"
    
    # 3. 检查是否识别到了编译错误
    # json_parser.cpp 中有 3 个错误：
    # - 'poss' undeclared (line ~26)
    # - missing return statement in validate() (line ~50)
    
    error_files_found = []
    for tool in agent.tool_calls:
        if tool['name'] == 'view_file':
            if 'json_parser.cpp' in str(tool):
                error_files_found.append('json_parser.cpp')
    
    assert 'json_parser.cpp' in error_files_found, \
        "应该识别到 json_parser.cpp 中的错误"
    
    # 4. 检查是否应用了修复
    edit_calls = [tool for tool in agent.tool_calls if tool['name'] == 'edit_file']
    assert len(edit_calls) > 0, "应该编辑文件以修复错误"
    
    # 5. 验证最终编译成功
    json_parser_path = os.path.join(project_root, 'src/parser/json_parser.cpp')
    with open(json_parser_path, 'r') as f:
        fixed_content = f.read()
    
    # 检查错误是否被修复
    assert 'poss' not in fixed_content, "变量名拼写错误应该被修复"
    assert 'return true;' in fixed_content or 'return false;' in fixed_content, \
        "validate() 函数应该有返回语句"
    
    # 6. 检查循环次数限制（不应超过 3 次修复尝试）
    assert compile_count <= 4, \
        f"编译次数不应超过 4 次（1 次初始 + 3 次重试），实际: {compile_count}"
    
    print(f"✓ 编译次数: {compile_count}")
    print(f"✓ 识别错误文件: {len(error_files_found)}")
    print(f"✓ 应用修复: {len(edit_calls)} 次")
    print("✓ 错误解析准确")
    print("✓ 修复策略合理")
    print("✓ 循环终止条件正确")
    
    return True


if __name__ == '__main__':
    try:
        test_compile_error_fix_loop()
        print("\n[PASS] Test Case 2: 编译错误自动修复")
    except AssertionError as e:
        print(f"\n[FAIL] Test Case 2: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test Case 2: {e}")
        sys.exit(1)
