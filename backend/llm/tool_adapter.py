# -*- coding: utf-8 -*-
"""
Tool calling adapter for models without native function calling support

For models that don't support native tool/function calling (like older OpenAI models,
some open-source models), this adapter simulates tool calling through prompts.
"""

import json
import re
from typing import List, Dict, Any, Optional


# Prompt template for simulating tool calls
TOOL_CALL_SYSTEM_PROMPT = """You are an AI assistant with access to tools. When you need to use a tool, output a JSON block in the following format:

```tool_call
{
  "name": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

You can call multiple tools by outputting multiple ```tool_call``` blocks.

Available tools:
{tool_descriptions}

Important:
- Only use the tools listed above
- Always use the exact parameter names as specified
- If you don't need to use any tool, just respond normally without tool_call blocks
"""

TOOL_RESULT_TEMPLATE = """Tool `{tool_name}` returned:
```
{result}
```
"""


def format_tools_for_prompt(tools: List[Dict]) -> str:
    """
    Format tool definitions for inclusion in system prompt

    Args:
        tools: List of tool definitions in OpenAI format

    Returns:
        Formatted string describing available tools
    """
    descriptions = []
    for tool in tools:
        if tool.get('type') != 'function':
            continue

        func = tool.get('function', {})
        name = func.get('name', 'unknown')
        desc = func.get('description', 'No description')
        params = func.get('parameters', {})

        # Format parameters
        props = params.get('properties', {})
        required = params.get('required', [])

        param_strs = []
        for param_name, param_info in props.items():
            param_type = param_info.get('type', 'any')
            param_desc = param_info.get('description', '')
            is_required = param_name in required
            req_str = " (required)" if is_required else " (optional)"
            param_strs.append(f"    - {param_name}: {param_type}{req_str} - {param_desc}")

        params_formatted = "\n".join(param_strs) if param_strs else "    (no parameters)"

        descriptions.append(f"""
### {name}
{desc}

Parameters:
{params_formatted}
""")

    return "\n".join(descriptions)


def inject_tools_into_messages(
    messages: List[Dict[str, str]],
    tools: List[Dict]
) -> List[Dict[str, str]]:
    """
    Inject tool descriptions into messages for prompt-based tool calling

    Args:
        messages: Original messages
        tools: Tool definitions

    Returns:
        Modified messages with tool descriptions in system prompt
    """
    if not tools:
        return messages

    tool_descriptions = format_tools_for_prompt(tools)
    tool_system_prompt = TOOL_CALL_SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions)

    # Check if first message is system prompt
    new_messages = list(messages)

    if new_messages and new_messages[0].get('role') == 'system':
        # Append to existing system prompt
        new_messages[0] = {
            'role': 'system',
            'content': new_messages[0]['content'] + "\n\n" + tool_system_prompt
        }
    else:
        # Insert new system prompt
        new_messages.insert(0, {
            'role': 'system',
            'content': tool_system_prompt
        })

    return new_messages


def parse_tool_calls_from_text(text: str) -> tuple[str, List[Dict]]:
    """
    Parse tool calls from model's text response

    Args:
        text: Model's response text

    Returns:
        Tuple of (clean_text, tool_calls)
        - clean_text: Text with tool_call blocks removed
        - tool_calls: List of parsed tool calls
    """
    tool_calls = []
    clean_text = text

    # Pattern to match ```tool_call ... ``` blocks
    pattern = r'```tool_call\s*\n?(.*?)\n?```'
    matches = re.findall(pattern, text, re.DOTALL)

    for i, match in enumerate(matches):
        try:
            # Parse JSON
            tool_data = json.loads(match.strip())

            # Build tool call in standard format
            tool_call = {
                'id': f"prompt_call_{i}",
                'type': 'function',
                'function': {
                    'name': tool_data.get('name', 'unknown'),
                    'arguments': json.dumps(tool_data.get('arguments', {}), ensure_ascii=False)
                }
            }
            tool_calls.append(tool_call)

        except json.JSONDecodeError:
            # Failed to parse, skip this block
            continue

    # Remove tool_call blocks from text
    clean_text = re.sub(pattern, '', text, flags=re.DOTALL).strip()

    return clean_text, tool_calls


def format_tool_result_for_prompt(tool_name: str, result: Any) -> str:
    """
    Format tool result for inclusion in next message

    Args:
        tool_name: Name of the tool that was called
        result: Tool execution result

    Returns:
        Formatted string for model context
    """
    if isinstance(result, dict):
        result_str = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        result_str = str(result)

    return TOOL_RESULT_TEMPLATE.format(tool_name=tool_name, result=result_str)


class PromptToolAdapter:
    """
    Adapter that wraps an LLM client to add prompt-based tool calling

    Use this when the underlying model doesn't support native function calling.

    Example:
        from backend.llm import OpenAIClient
        from backend.llm.tool_adapter import PromptToolAdapter

        # Wrap a client that doesn't support native tools
        base_client = OpenAIClient(config={'models': {'main': 'gpt-3.5-turbo-instruct'}})
        client = PromptToolAdapter(base_client)

        # Now use like normal - tools will be simulated via prompts
        response = client.chat_with_tools(messages, tools)
    """

    def __init__(self, client):
        """
        Initialize adapter

        Args:
            client: Base LLM client to wrap
        """
        self.client = client
        self._pending_tool_results = []

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_chunk=None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request with prompt-based tool calling

        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            stream: Enable streaming (note: tool parsing happens after stream completes)
            on_chunk: Streaming callback
            **kwargs: Additional parameters

        Returns:
            Response dict with 'message' and optional 'tool_calls'
        """
        # Inject any pending tool results
        if self._pending_tool_results:
            tool_results_text = "\n".join(self._pending_tool_results)
            messages = list(messages)
            messages.append({
                'role': 'user',
                'content': f"Tool execution results:\n{tool_results_text}\n\nPlease continue based on these results."
            })
            self._pending_tool_results = []

        # Inject tools into messages if provided
        if tools:
            messages = inject_tools_into_messages(messages, tools)

        # Call underlying client WITHOUT tools (we're simulating via prompt)
        response = self.client.chat(messages, tools=None, stream=stream, on_chunk=on_chunk, **kwargs)

        # Parse tool calls from response text
        content = response.get('message', {}).get('content', '')
        clean_content, tool_calls = parse_tool_calls_from_text(content)

        # Update response
        result = {
            'message': {
                'content': clean_content
            }
        }

        if tool_calls:
            result['message']['tool_calls'] = tool_calls

        return result

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        stream: bool = False,
        on_chunk=None
    ) -> Dict[str, Any]:
        """Chat with tool support"""
        return self.chat(messages, tools=tools, stream=stream, on_chunk=on_chunk)

    def parse_tool_calls(self, response: Dict[str, Any]) -> Optional[List[Dict]]:
        """Extract tool calls from response"""
        message = response.get('message', {})
        tool_calls = message.get('tool_calls', [])
        return tool_calls if tool_calls else None

    def add_tool_result(self, tool_name: str, result: Any):
        """
        Add a tool result to be included in next request

        Args:
            tool_name: Name of the tool
            result: Tool execution result
        """
        formatted = format_tool_result_for_prompt(tool_name, result)
        self._pending_tool_results.append(formatted)

    def format_tool_result(self, tool_call_id: str, result: Any) -> Dict[str, str]:
        """Format tool result for conversation history"""
        return self.client.format_tool_result(tool_call_id, result)

    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count"""
        return self.client.estimate_tokens(messages)

    def compress_context(self, messages, target_tokens, must_keep, compressible):
        """Compress context"""
        return self.client.compress_context(messages, target_tokens, must_keep, compressible)

    @property
    def backend_name(self) -> str:
        """Return backend name"""
        return f"prompt_adapter({self.client.backend_name})"
