# -*- coding: utf-8 -*-
"""
OpenAI-compatible client for internal LLM services
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import BaseLLMClient
from .config import load_llm_config, resolve_env_var, get_project_root
from .retry import RetryConfig, with_retry
from .compression import compress_context, estimate_tokens_english


class OpenAIClient(BaseLLMClient):
    """OpenAI-compatible client for internal/public LLM services"""

    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize OpenAI-compatible client

        Args:
            config_path: Path to llm.yaml config file
            config: Direct config dict (takes precedence over config_path)
        """
        # Lazy import openai
        try:
            import openai
            self._openai = openai
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAIClient. "
                "Install it with: pip install openai"
            )

        # Load configuration
        self.config = load_llm_config(config_path, config, section='openai')

        # 验证必需配置
        self.base_url = self.config.get('base_url')
        if not self.base_url:
            raise ValueError("配置缺少 base_url")

        self.api_key = resolve_env_var(self.config.get('api_key'))
        if not self.api_key:
            # Try environment variable
            self.api_key = os.getenv('OPENAI_API_KEY', '')
        if not self.api_key:
            raise ValueError("配置缺少 api_key")

        self.timeout = self.config.get('timeout', 300)
        self.stream_enabled = self.config.get('stream', True)

        # Model configuration
        self.model = self.config.get('model') or self.config.get('models', {}).get('main')
        if not self.model:
            raise ValueError("配置缺少 model")

        # Generation parameters
        self.generation_params = self.config.get('generation', {
            'temperature': 0.1,
            'top_p': 0.9,
            'max_tokens': 4096
        })

        # Retry configuration
        self.retry_config = RetryConfig.from_dict(
            self.config.get('retry', {})
        )

        # Initialize OpenAI client
        self.client = self._openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        # Track last request for debugging
        self.last_request_file = None
        self.last_conversation_file = None

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to OpenAI-compatible API"""
        params = {**self.generation_params, **kwargs}

        request_params = {
            'model': self.model,
            'messages': messages,
            'stream': stream,
            **params
        }

        if tools:
            request_params['tools'] = tools
            request_params['tool_choice'] = 'auto'

        def do_request():
            self._log_request(request_params)
            if stream:
                return self._stream_chat(request_params, on_chunk)
            else:
                return self._sync_chat(request_params)

        return with_retry(do_request, self.retry_config)

    def _sync_chat(self, request_params: Dict) -> Dict[str, Any]:
        """Synchronous chat request"""
        response = self.client.chat.completions.create(**request_params)

        result = {
            'message': {
                'content': response.choices[0].message.content or ''
            }
        }

        if response.choices[0].message.tool_calls:
            tool_calls = []
            for tc in response.choices[0].message.tool_calls:
                tool_calls.append({
                    'id': tc.id,
                    'type': 'function',
                    'function': {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                })
            result['message']['tool_calls'] = tool_calls

        return result

    def _stream_chat(
        self,
        request_params: Dict,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Streaming chat request"""
        stream = self.client.chat.completions.create(**request_params)

        full_response = ""
        tool_calls = []

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                full_response += delta.content
                if on_chunk:
                    on_chunk(delta.content)

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    if tc_delta.index is not None:
                        while len(tool_calls) <= tc_delta.index:
                            tool_calls.append({
                                'id': '',
                                'type': 'function',
                                'function': {'name': '', 'arguments': ''}
                            })

                        current = tool_calls[tc_delta.index]

                        if tc_delta.id:
                            current['id'] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                current['function']['name'] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                current['function']['arguments'] += tc_delta.function.arguments

        result = {
            'message': {
                'content': full_response.strip()
            }
        }

        if tool_calls:
            result['message']['tool_calls'] = tool_calls

        return result

    def _log_request(self, request_params: Dict):
        """Log request to file for debugging"""
        from datetime import datetime

        if not os.getenv('DEBUG_AGENT') and not os.getenv('DEBUG_LLM'):
            return

        log_dir = get_project_root() / 'logs'
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        request_file = log_dir / f'openai_request_{timestamp}.json'

        with open(request_file, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(request_params, f, ensure_ascii=False, indent=2, default=str)

        self.last_request_file = str(request_file)
        print(f"\033[90m[OpenAI] Request saved to: {request_file}\033[0m")

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Chat with function calling support"""
        return self.chat(messages, tools=tools, stream=stream, on_chunk=on_chunk)

    def parse_tool_calls(self, response: Dict[str, Any]) -> Optional[List[Dict]]:
        """Extract tool calls from response"""
        message = response.get('message', {})
        tool_calls = message.get('tool_calls', [])

        if not tool_calls:
            return None

        for i, tool_call in enumerate(tool_calls):
            if 'id' not in tool_call or not tool_call['id']:
                func_name = tool_call.get('function', {}).get('name', 'unknown')
                tool_call['id'] = f"call_{func_name}_{i}"

        return tool_calls

    def compress_context(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int,
        must_keep: str,
        compressible: str
    ) -> Dict[str, Any]:
        """Use LLM to compress conversation history"""
        def chat_func(msgs):
            return self.chat(msgs, temperature=0.3, stream=False)

        return compress_context(
            messages, target_tokens, must_keep, compressible,
            chat_func, estimate_tokens_english
        )

    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages"""
        return estimate_tokens_english(messages)

    def set_model(self, model: str):
        """Set the model to use for requests"""
        self.model = model

    def list_models(self) -> List[str]:
        """List available models"""
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            print(f"Failed to list models: {e}")
            return []
