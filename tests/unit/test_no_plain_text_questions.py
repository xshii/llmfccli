# -*- coding: utf-8 -*-
"""
Test: 验证模型不会用纯文本询问"下一步建议"

这个测试确保模型遵循工具优先原则：
- 任务完成后直接停止
- 如需询问，必须使用 propose_options 工具
- 不能用纯文本输出"接下来"、"下一步"、"还需要什么"等提问
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


# 禁止出现的短语（表示纯文本提问）
FORBIDDEN_PHRASES = [
    "下一步",
    "接下来",
    "还需要",
    "您想",
    "您希望",
    "帮您",
    "需要我",
    "我可以帮",
    "what next",
    "need help",
    "anything else",
]


def test_no_plain_text_questions():
    """测试：完成简单任务后不应该有纯文本提问"""

    # 初始化 Agent
    client = OllamaClient()
    agent = AgentLoop(client)

    # 设置项目根目录
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    agent.set_project_root(project_root)

    # 简单任务：查看文件
    user_input = "查看 src/main.cpp 文件的前 20 行"

    # 执行 Agent
    response = agent.run(user_input)

    print(f"\n=== Agent Response ===")
    print(f"Response: {response}")
    print(f"\nTool calls made: {len(agent.tool_calls)}")

    # 验证：检查响应中是否包含禁止的短语
    response_lower = response.lower()
    found_forbidden = []

    for phrase in FORBIDDEN_PHRASES:
        if phrase in response_lower:
            found_forbidden.append(phrase)

    # 断言：不应该包含任何禁止短语
    if found_forbidden:
        print(f"\n❌ 发现禁止的纯文本提问短语: {found_forbidden}")
        print(f"\n完整响应:\n{response}")
        raise AssertionError(
            f"模型在响应中使用了纯文本提问，违反工具优先原则。"
            f"发现的短语: {found_forbidden}\n"
            f"应该使用 propose_options 工具或直接结束。"
        )

    # 验证：检查是否正确调用了工具
    tool_names = [call.get('function', {}).get('name') for call in agent.tool_calls]
    assert 'view_file' in tool_names, "应该调用 view_file 工具"

    # 验证：不应该调用 propose_options（任务很明确）
    propose_calls = [name for name in tool_names if name == 'propose_options']
    assert len(propose_calls) == 0, \
        f"任务明确，不应该调用 propose_options。调用了 {len(propose_calls)} 次"

    print("\n✅ 验证通过：模型没有使用纯文本提问")
    print("✅ 验证通过：正确调用工具完成任务")
    print("✅ 验证通过：任务完成后直接停止")

    return True


def test_clear_task_no_propose_options():
    """测试：明确的任务不应该调用 propose_options"""

    client = OllamaClient()
    agent = AgentLoop(client)

    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    agent.set_project_root(project_root)

    # 明确的任务
    user_input = "在 src/main.cpp 中添加一行注释：// This is main function"

    response = agent.run(user_input)

    print(f"\n=== Test 2: Clear Task ===")
    print(f"Response: {response[:200]}")

    # 检查工具调用
    tool_names = [call.get('function', {}).get('name') for call in agent.tool_calls]
    propose_calls = [name for name in tool_names if name == 'propose_options']

    # 断言：任务明确，不应该调用 propose_options
    assert len(propose_calls) == 0, \
        f"任务明确（添加注释），不应该调用 propose_options。调用了 {len(propose_calls)} 次"

    # 检查是否有禁止短语
    found_forbidden = [phrase for phrase in FORBIDDEN_PHRASES if phrase in response.lower()]
    assert not found_forbidden, \
        f"发现禁止的纯文本提问短语: {found_forbidden}"

    print("✅ 验证通过：明确任务不调用 propose_options")
    print("✅ 验证通过：无纯文本提问")

    return True


if __name__ == '__main__':
    try:
        print("\n" + "=" * 60)
        print("  测试：验证无纯文本提问")
        print("=" * 60)

        # 运行测试 1
        test_no_plain_text_questions()

        # 运行测试 2
        test_clear_task_no_propose_options()

        print("\n" + "=" * 60)
        print("[PASS] 所有测试通过")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        print("\n修复建议：")
        print("1. 重新加载模型: bash scripts/reload_model.sh")
        print("2. 检查 Modelfile: grep '禁止纯文本提问' config/modelfiles/claude-qwen.modelfile")
        print("3. 降低 temperature: 修改 Modelfile 中的 temperature 到 0.3-0.4")
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
