#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PromptToolAdapter - prompt-based tool calling simulation
"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.llm.tool_adapter import (
    format_tools_for_prompt,
    inject_tools_into_messages,
    parse_tool_calls_from_text,
    format_tool_result_for_prompt,
    PromptToolAdapter,
)


# Sample tool definitions for testing
SAMPLE_TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'view_file',
            'description': 'Read file contents with optional line range',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'File path relative to project root'
                    },
                    'line_range': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'Optional [start, end] line numbers'
                    }
                },
                'required': ['path']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'grep_search',
            'description': 'Search for pattern in files',
            'parameters': {
                'type': 'object',
                'properties': {
                    'pattern': {
                        'type': 'string',
                        'description': 'Search pattern (regex supported)'
                    },
                    'path': {
                        'type': 'string',
                        'description': 'Directory to search in'
                    }
                },
                'required': ['pattern']
            }
        }
    }
]


def test_format_tools_for_prompt():
    """Test formatting tool definitions for prompt"""
    print("Testing format_tools_for_prompt...")

    formatted = format_tools_for_prompt(SAMPLE_TOOLS)

    assert 'view_file' in formatted, "Should contain view_file"
    assert 'grep_search' in formatted, "Should contain grep_search"
    assert 'path' in formatted, "Should contain path parameter"
    assert '(required)' in formatted, "Should mark required params"
    assert '(optional)' in formatted, "Should mark optional params"

    print(f"  ✓ Formatted {len(SAMPLE_TOOLS)} tools")
    print(f"  ✓ Output length: {len(formatted)} chars")


def test_inject_tools_into_messages():
    """Test injecting tools into messages"""
    print("\nTesting inject_tools_into_messages...")

    # Test with no system message
    messages = [
        {'role': 'user', 'content': 'Hello'}
    ]

    injected = inject_tools_into_messages(messages, SAMPLE_TOOLS)

    assert len(injected) == 2, "Should have system + user message"
    assert injected[0]['role'] == 'system', "First should be system"
    assert 'view_file' in injected[0]['content'], "Should contain tool names"

    print("  ✓ Injected tools into messages without system prompt")

    # Test with existing system message
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Hello'}
    ]

    injected = inject_tools_into_messages(messages, SAMPLE_TOOLS)

    assert len(injected) == 2, "Should still have 2 messages"
    assert 'helpful assistant' in injected[0]['content'], "Should keep original"
    assert 'view_file' in injected[0]['content'], "Should append tools"

    print("  ✓ Injected tools into existing system prompt")


def test_parse_tool_calls_from_text_single():
    """Test parsing single tool call from text"""
    print("\nTesting parse_tool_calls_from_text (single)...")

    text = """I'll read the file for you.

```tool_call
{
  "name": "view_file",
  "arguments": {
    "path": "src/main.cpp"
  }
}
```

Let me check that file."""

    clean_text, tool_calls = parse_tool_calls_from_text(text)

    assert len(tool_calls) == 1, f"Should have 1 tool call, got {len(tool_calls)}"
    assert tool_calls[0]['function']['name'] == 'view_file', "Should be view_file"

    args = json.loads(tool_calls[0]['function']['arguments'])
    assert args['path'] == 'src/main.cpp', "Path should be src/main.cpp"

    assert 'tool_call' not in clean_text, "Clean text should not have tool_call block"
    assert "I'll read the file" in clean_text, "Should keep other text"

    print(f"  ✓ Parsed tool call: {tool_calls[0]['function']['name']}")
    print(f"  ✓ Arguments: {args}")
    print(f"  ✓ Clean text length: {len(clean_text)} chars")


def test_parse_tool_calls_from_text_multiple():
    """Test parsing multiple tool calls from text"""
    print("\nTesting parse_tool_calls_from_text (multiple)...")

    text = """I need to search and then read the file.

```tool_call
{
  "name": "grep_search",
  "arguments": {
    "pattern": "class NetworkHandler",
    "path": "src"
  }
}
```

Then I'll view the file:

```tool_call
{
  "name": "view_file",
  "arguments": {
    "path": "src/network.cpp",
    "line_range": [1, 50]
  }
}
```

Let me analyze the results."""

    clean_text, tool_calls = parse_tool_calls_from_text(text)

    assert len(tool_calls) == 2, f"Should have 2 tool calls, got {len(tool_calls)}"
    assert tool_calls[0]['function']['name'] == 'grep_search', "First should be grep_search"
    assert tool_calls[1]['function']['name'] == 'view_file', "Second should be view_file"

    # Check IDs are unique
    ids = [tc['id'] for tc in tool_calls]
    assert len(set(ids)) == 2, "IDs should be unique"

    print(f"  ✓ Parsed {len(tool_calls)} tool calls")
    print(f"  ✓ Tool names: {[tc['function']['name'] for tc in tool_calls]}")
    print(f"  ✓ IDs: {ids}")


def test_parse_tool_calls_no_tools():
    """Test parsing text with no tool calls"""
    print("\nTesting parse_tool_calls_from_text (no tools)...")

    text = "This is just a regular response without any tool calls."

    clean_text, tool_calls = parse_tool_calls_from_text(text)

    assert len(tool_calls) == 0, "Should have no tool calls"
    assert clean_text == text, "Clean text should be unchanged"

    print("  ✓ Correctly handled text with no tool calls")


def test_parse_tool_calls_invalid_json():
    """Test parsing with invalid JSON in tool_call block"""
    print("\nTesting parse_tool_calls_from_text (invalid JSON)...")

    text = """Let me try:

```tool_call
{
  "name": "view_file",
  "arguments": {invalid json here}
}
```

That didn't work."""

    clean_text, tool_calls = parse_tool_calls_from_text(text)

    # Should gracefully skip invalid JSON
    assert len(tool_calls) == 0, "Should skip invalid tool calls"

    print("  ✓ Gracefully handled invalid JSON")


def test_format_tool_result():
    """Test formatting tool results"""
    print("\nTesting format_tool_result_for_prompt...")

    # Test with dict result
    result = {
        'success': True,
        'content': 'file contents here...',
        'lines': 100
    }

    formatted = format_tool_result_for_prompt('view_file', result)

    assert 'view_file' in formatted, "Should contain tool name"
    assert 'success' in formatted, "Should contain result"

    print(f"  ✓ Formatted dict result: {len(formatted)} chars")

    # Test with string result
    formatted_str = format_tool_result_for_prompt('grep_search', 'Found 5 matches')

    assert 'grep_search' in formatted_str, "Should contain tool name"
    assert '5 matches' in formatted_str, "Should contain result"

    print(f"  ✓ Formatted string result: {len(formatted_str)} chars")


class MockLLMClient:
    """Mock LLM client for testing PromptToolAdapter"""

    def __init__(self):
        self.last_messages = None
        self.response_text = ""

    def set_response(self, text):
        """Set the response text for next chat call"""
        self.response_text = text

    def chat(self, messages, tools=None, stream=False, on_chunk=None, **kwargs):
        """Mock chat that returns configured response"""
        self.last_messages = messages
        return {
            'message': {
                'content': self.response_text
            }
        }

    def format_tool_result(self, tool_call_id, result):
        return {
            'role': 'tool',
            'content': json.dumps(result),
            'tool_call_id': tool_call_id
        }

    def estimate_tokens(self, messages):
        return sum(len(m.get('content', '')) for m in messages) // 4

    def compress_context(self, messages, target_tokens, must_keep, compressible):
        return {'compressed': True}

    @property
    def backend_name(self):
        return 'mock'


def test_prompt_tool_adapter():
    """Test PromptToolAdapter wrapper"""
    print("\nTesting PromptToolAdapter...")

    mock_client = MockLLMClient()
    adapter = PromptToolAdapter(mock_client)

    # Set mock response with tool call
    mock_client.set_response("""I'll check the file.

```tool_call
{
  "name": "view_file",
  "arguments": {"path": "test.cpp"}
}
```
""")

    # Call with tools
    messages = [{'role': 'user', 'content': 'Show me test.cpp'}]
    response = adapter.chat(messages, tools=SAMPLE_TOOLS)

    # Check response
    assert 'message' in response, "Should have message"
    assert 'tool_calls' in response['message'], "Should have tool_calls"

    tool_calls = response['message']['tool_calls']
    assert len(tool_calls) == 1, f"Should have 1 tool call, got {len(tool_calls)}"
    assert tool_calls[0]['function']['name'] == 'view_file', "Should be view_file"

    # Check that tools were injected into messages
    assert mock_client.last_messages is not None
    system_content = mock_client.last_messages[0]['content']
    assert 'view_file' in system_content, "Should inject tools into system prompt"

    print(f"  ✓ Adapter correctly wrapped client")
    print(f"  ✓ Parsed tool call from response")
    print(f"  ✓ Injected tools into messages")


def test_prompt_tool_adapter_parse_tool_calls():
    """Test parse_tool_calls method of adapter"""
    print("\nTesting PromptToolAdapter.parse_tool_calls...")

    mock_client = MockLLMClient()
    adapter = PromptToolAdapter(mock_client)

    # Response with tool calls
    response = {
        'message': {
            'content': 'Some text',
            'tool_calls': [
                {
                    'id': 'call_1',
                    'function': {'name': 'view_file', 'arguments': '{}'}
                }
            ]
        }
    }

    tool_calls = adapter.parse_tool_calls(response)
    assert tool_calls is not None, "Should return tool calls"
    assert len(tool_calls) == 1, "Should have 1 tool call"

    # Response without tool calls
    response_no_tools = {
        'message': {
            'content': 'Just text'
        }
    }

    tool_calls_empty = adapter.parse_tool_calls(response_no_tools)
    assert tool_calls_empty is None, "Should return None when no tools"

    print("  ✓ parse_tool_calls works correctly")


def test_prompt_tool_adapter_backend_name():
    """Test backend_name property"""
    print("\nTesting PromptToolAdapter.backend_name...")

    mock_client = MockLLMClient()
    adapter = PromptToolAdapter(mock_client)

    assert 'prompt_adapter' in adapter.backend_name, "Should indicate adapter"
    assert 'mock' in adapter.backend_name, "Should include wrapped client name"

    print(f"  ✓ Backend name: {adapter.backend_name}")


def run_all_tests():
    """Run all tool adapter tests"""
    print("=" * 60)
    print("PromptToolAdapter Unit Tests")
    print("=" * 60)

    test_format_tools_for_prompt()
    test_inject_tools_into_messages()
    test_parse_tool_calls_from_text_single()
    test_parse_tool_calls_from_text_multiple()
    test_parse_tool_calls_no_tools()
    test_parse_tool_calls_invalid_json()
    test_format_tool_result()
    test_prompt_tool_adapter()
    test_prompt_tool_adapter_parse_tool_calls()
    test_prompt_tool_adapter_backend_name()

    print("\n" + "=" * 60)
    print("✓ All PromptToolAdapter tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
