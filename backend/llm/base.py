# -*- coding: utf-8 -*-
"""
Abstract base class for LLM clients
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients (Ollama, OpenAI, etc.)"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request to LLM

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            stream: Enable streaming output
            on_chunk: Optional callback function called with each content chunk
            **kwargs: Override generation parameters

        Returns:
            Response dict with 'message' and optional 'tool_calls'
        """
        pass

    @abstractmethod
    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Chat with function calling support

        Args:
            messages: Conversation history
            tools: Tool definitions in OpenAI format
            stream: Enable streaming output
            on_chunk: Optional callback function called with each content chunk

        Returns:
            Response with potential tool_calls
        """
        pass

    @abstractmethod
    def parse_tool_calls(self, response: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Extract tool calls from response

        Args:
            response: LLM response dict

        Returns:
            List of tool call dicts or None
        """
        pass

    @abstractmethod
    def compress_context(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int,
        must_keep: str,
        compressible: str
    ) -> Dict[str, Any]:
        """
        Use LLM to compress conversation history

        Args:
            messages: Full conversation history
            target_tokens: Target token count after compression
            must_keep: Description of content that must be kept
            compressible: Description of content that can be compressed

        Returns:
            Compression result dict
        """
        pass

    @abstractmethod
    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Estimate token count for messages

        Args:
            messages: List of message dicts

        Returns:
            Estimated token count
        """
        pass

    def format_tool_result(self, tool_call_id: str, result: Any) -> Dict[str, str]:
        """
        Format tool execution result for next chat turn

        Args:
            tool_call_id: ID of the tool call
            result: Tool execution result

        Returns:
            Message dict for tool result
        """
        import json
        return {
            'role': 'tool',
            'content': json.dumps(result, ensure_ascii=False),
            'tool_call_id': tool_call_id
        }

    @property
    def backend_name(self) -> str:
        """Return backend name for logging"""
        return self.__class__.__name__.replace('Client', '').lower()
