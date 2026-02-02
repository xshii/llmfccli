# -*- coding: utf-8 -*-
"""
单个用例交互式运行 - 实时显示对话
"""

import os
import sys
from typing import Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient
from backend.llm.config import load_yaml_config


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Run single benchmark case interactively')
    parser.add_argument('--model', '-m', type=str, default='glm-4.7-flash:latest',
                        help='Model name')
    parser.add_argument('case', nargs='?', default='simple_edit',
                        choices=['simple_edit', 'code_search', 'file_location', 'write_test'],
                        help='Case to run')

    args = parser.parse_args()

    # 用例定义
    CASES = {
        'simple_edit': """
在 network_handler.cpp 的 connect() 函数开头添加一行日志：
std::cout << "Connecting to server..." << std::endl;
""",
        'code_search': "找到项目中所有使用 NetworkHandler 类的地方，列出文件和行号",
        'file_location': """
在 network_handler.cpp 的 connect() 函数中添加连接超时和重试机制。
要求：超时时间 5 秒，最多重试 3 次，每次重试间隔 1 秒。
""",
        'write_test': """
为 src/parser/json_parser.cpp 中的 JsonParser 类编写单元测试。
要求：
1. 创建 test_json_parser.cpp
2. 使用 assert 测试 parse() 和 get_value() 方法
3. 不使用外部测试框架，直接 g++ 编译运行
4. 确保测试通过
""",
    }

    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')

    print(f"Model: {args.model}")
    print(f"Case: {args.case}")
    print(f"Project: {project_root}")
    print("=" * 60)

    # 创建 agent
    base_config = load_yaml_config().get('ollama', {})
    base_config['model'] = args.model
    client = OllamaClient(config=base_config)
    agent = AgentLoop(client)
    agent.set_project_root(project_root)

    # 设置流式输出回调
    def on_token(token: str):
        print(token, end='', flush=True)

    def on_tool_call(name: str, args: dict):
        print(f"\n>>> TOOL: {name}")
        for k, v in args.items():
            v_str = str(v)
            if len(v_str) > 100:
                v_str = v_str[:100] + '...'
            print(f"    {k}: {v_str}")

    def on_tool_result(name: str, result: str):
        result_str = str(result)
        if len(result_str) > 300:
            result_str = result_str[:300] + '...'
        print(f"<<< RESULT ({name}):\n{result_str}\n")

    # 注册回调
    if hasattr(agent, 'set_callbacks'):
        agent.set_callbacks(
            on_token=on_token,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result
        )

    user_input = CASES[args.case]
    print(f"USER: {user_input.strip()}")
    print("-" * 60)

    def on_chunk(chunk: str):
        print(chunk, end='', flush=True)

    # 设置工具输出回调
    def on_tool_output(tool_name: str, result: Any, args: Dict):
        print(f"\n>>> [{tool_name}] completed", flush=True)
        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + '...'
        print(f"    Result: {result_str}", flush=True)

    agent.tool_output_callback = on_tool_output

    try:
        response = agent.run(user_input, stream=True, on_chunk=on_chunk)
        print("\n" + "=" * 60)
        print(f"Tool calls: {len(agent.tool_calls)}")
        print(f"Iterations: {len([m for m in agent.conversation_history if m['role'] == 'assistant'])}")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        import traceback
        print(f"\nError: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
