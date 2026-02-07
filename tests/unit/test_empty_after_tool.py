# -*- coding: utf-8 -*-
"""
Unit test: 模型在工具调用后返回空内容的场景

复现场景（Ollama/Qwen3 已知 bug）:
  1. assistant: 空 content + tool_calls
  2. tool: 返回结果
  3. assistant: 空 content, 无 tool_calls  ← 之前会提示"没有回复"

修复后行为:
  - 当 feature flag `retry_on_empty_after_tool` 启用时，自动重试
"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.loop import AgentLoop
from backend.agent.tools.executor import MockToolExecutor
from backend.llm.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Mock LLM client that returns predefined responses in sequence"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.call_count = 0
        self.received_messages = []
        self.received_tools = []

    def chat(self, messages, tools=None, stream=False, on_chunk=None, **kwargs):
        return self._next_response(messages)

    def chat_with_tools(self, messages, tools, stream=False, on_chunk=None):
        self.received_tools.append(list(tools) if tools else [])
        return self._next_response(messages)

    def parse_tool_calls(self, response):
        message = response.get('message', {})
        tool_calls = message.get('tool_calls', [])
        if not tool_calls:
            return None
        for i, tc in enumerate(tool_calls):
            if 'id' not in tc:
                tc['id'] = f"{tc.get('function', {}).get('name', 'unknown')}_{i}"
        return tool_calls

    def compress_context(self, messages, target_tokens, must_keep, compressible):
        return {'keep_message_indices': [], 'compressed_summary': ''}

    def estimate_tokens(self, messages):
        return sum(len(m.get('content', '')) for m in messages) // 3

    def _next_response(self, messages):
        self.received_messages.append(list(messages))
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        self.call_count += 1
        return {'message': {'content': 'Fallback response'}}


class _MockRegistry:
    """Minimal mock for ToolRegistry.get()"""
    def get(self, name):
        return None


def _make_tool_executor():
    """Create a mock tool executor with a test tool"""
    executor = MockToolExecutor()
    executor.registry = _MockRegistry()
    executor.register_mock_tool(
        'view_file',
        {
            'type': 'function',
            'function': {
                'name': 'view_file',
                'description': 'View file content',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string'}
                    },
                    'required': ['path']
                }
            }
        },
        result={'content': 'file content here', 'total_lines': 10}
    )
    return executor


@patch('backend.utils.feature.FeatureFlags.is_enabled', return_value=True)
def test_empty_content_after_tool_retries(mock_feature):
    """
    测试: feature flag 启用时，assistant 空 content + tool_calls → tool → assistant 空 content
    期望: 自动重试，最终返回正常内容
    """
    callback_messages = []

    def tool_output_callback(event_type, message, metadata):
        callback_messages.append((event_type, message))

    responses = [
        # Round 1: assistant 空 content + tool_calls
        {
            'message': {
                'content': '',
                'tool_calls': [
                    {
                        'function': {
                            'name': 'view_file',
                            'arguments': '{"path": "test.cpp"}'
                        }
                    }
                ]
            }
        },
        # Round 2: Ollama bug — 工具执行后返回空 content
        {
            'message': {
                'content': ''
            }
        },
        # Round 3: 重试后模型正常文本回复
        {
            'message': {
                'content': 'The file contains a C++ class definition.'
            }
        },
    ]

    client = MockLLMClient(responses)
    executor = _make_tool_executor()

    agent = AgentLoop(
        client=client,
        tool_executor=executor,
        tool_output_callback=tool_output_callback,
    )

    result = agent.run("查看 test.cpp 文件")

    # 验证: 最终返回了正常内容
    assert result == 'The file contains a C++ class definition.', \
        f"Expected normal response, got: '{result}'"

    # 验证: LLM 被调用了 3 次
    assert client.call_count == 3, \
        f"Expected 3 LLM calls, got {client.call_count}"

    # 验证: 有重试提示回调
    retry_msgs = [msg for _, msg in callback_messages if '重试' in msg]
    assert len(retry_msgs) >= 1, \
        f"Expected retry message, got callbacks: {callback_messages}"

    print("✓ test_empty_content_after_tool_retries passed")


@patch('backend.utils.feature.FeatureFlags.is_enabled', return_value=True)
def test_normal_empty_response_without_prior_tool(mock_feature):
    """
    测试: 非工具执行后的空响应不应该触发重试
    """
    responses = [
        {'message': {'content': ''}},
    ]

    client = MockLLMClient(responses)
    executor = _make_tool_executor()

    agent = AgentLoop(
        client=client,
        tool_executor=executor,
    )

    result = agent.run("hello")

    assert result == '', f"Expected empty string, got: '{result}'"
    assert client.call_count == 1, \
        f"Expected 1 LLM call (no retry), got {client.call_count}"

    print("✓ test_normal_empty_response_without_prior_tool passed")


@patch('backend.utils.feature.FeatureFlags.is_enabled', return_value=True)
def test_nonempty_content_after_tool(mock_feature):
    """
    测试: 工具执行后有正常内容的响应，不应触发重试
    """
    responses = [
        {
            'message': {
                'content': '',
                'tool_calls': [
                    {
                        'function': {
                            'name': 'view_file',
                            'arguments': '{"path": "test.cpp"}'
                        }
                    }
                ]
            }
        },
        {
            'message': {
                'content': 'Here is the file content.'
            }
        },
    ]

    client = MockLLMClient(responses)
    executor = _make_tool_executor()

    agent = AgentLoop(
        client=client,
        tool_executor=executor,
    )

    result = agent.run("查看文件")

    assert result == 'Here is the file content.', \
        f"Expected normal response, got: '{result}'"
    assert client.call_count == 2, \
        f"Expected 2 LLM calls, got {client.call_count}"

    print("✓ test_nonempty_content_after_tool passed")


@patch('backend.utils.feature.FeatureFlags.is_enabled', return_value=False)
def test_feature_flag_disabled_no_retry(mock_feature):
    """
    测试: feature flag 关闭时，空响应不触发重试，直接返回空内容
    """
    responses = [
        {
            'message': {
                'content': '',
                'tool_calls': [
                    {
                        'function': {
                            'name': 'view_file',
                            'arguments': '{"path": "test.cpp"}'
                        }
                    }
                ]
            }
        },
        # Ollama bug — 空 content
        {
            'message': {
                'content': ''
            }
        },
    ]

    client = MockLLMClient(responses)
    executor = _make_tool_executor()

    agent = AgentLoop(
        client=client,
        tool_executor=executor,
    )

    result = agent.run("查看文件")

    # feature flag 关闭，空响应直接返回
    assert result == '', f"Expected empty string, got: '{result}'"
    assert client.call_count == 2, \
        f"Expected 2 LLM calls (no retry), got {client.call_count}"

    print("✓ test_feature_flag_disabled_no_retry passed")


if __name__ == '__main__':
    print("Testing empty content after tool execution...\n")

    test_empty_content_after_tool_retries()
    test_normal_empty_response_without_prior_tool()
    test_nonempty_content_after_tool()
    test_feature_flag_disabled_no_retry()

    print("\n✅ All tests passed!")
