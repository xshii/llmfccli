# -*- coding: utf-8 -*-
"""
OpenAI-compatible client for internal LLM services
"""

import json
import os
import re
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import yaml

from .base import BaseLLMClient


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
        if config is not None:
            self.config = config
        else:
            if config_path is None:
                project_root = Path(__file__).parent.parent.parent
                config_path = project_root / "config" / "llm.yaml"

            if config_path and Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = yaml.safe_load(f)
                self.config = full_config.get('openai', {})
            else:
                self.config = {}

        # Parse configuration
        self.base_url = self.config.get('base_url', 'https://api.openai.com/v1')
        self.api_key = self._resolve_api_key(self.config.get('api_key'))
        self.timeout = self.config.get('timeout', 300)
        self.stream_enabled = self.config.get('stream', True)

        # Model configuration
        models_config = self.config.get('models', {})
        self.model = models_config.get('main', 'gpt-4-turbo')

        # Generation parameters
        self.generation_params = self.config.get('generation', {
            'temperature': 0.1,
            'top_p': 0.9,
            'max_tokens': 4096
        })

        # Retry configuration
        self.retry_config = self.config.get('retry', {
            'max_attempts': 3,
            'backoff_factor': 2,
            'initial_delay': 1
        })

        # Initialize OpenAI client
        self.client = self._openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        # Track last request for debugging
        self.last_request_file = None
        self.last_conversation_file = None

    def _resolve_api_key(self, api_key_config: Optional[str]) -> str:
        """
        Resolve API key from config or environment

        Args:
            api_key_config: API key configuration string

        Returns:
            Resolved API key
        """
        if not api_key_config:
            # Try environment variable
            return os.getenv('OPENAI_API_KEY', '')

        # Check for environment variable reference: ${VAR_NAME}
        match = re.match(r'\$\{(\w+)\}', api_key_config)
        if match:
            env_var = match.group(1)
            return os.getenv(env_var, '')

        return api_key_config

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request to OpenAI-compatible API

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            stream: Enable streaming output
            on_chunk: Optional callback function called with each content chunk
            **kwargs: Override generation parameters

        Returns:
            Response dict with 'message' and optional 'tool_calls'
        """
        # Merge generation params with kwargs
        params = {**self.generation_params, **kwargs}

        # Build request parameters
        request_params = {
            'model': self.model,
            'messages': messages,
            'stream': stream,
            **params
        }

        # Add tools if provided
        if tools:
            request_params['tools'] = tools
            request_params['tool_choice'] = 'auto'

        # Retry logic
        max_attempts = self.retry_config['max_attempts']
        backoff_factor = self.retry_config['backoff_factor']
        initial_delay = self.retry_config['initial_delay']

        for attempt in range(max_attempts):
            try:
                # Log request
                self._log_request(request_params)

                if stream:
                    return self._stream_chat(request_params, on_chunk)
                else:
                    return self._sync_chat(request_params)

            except Exception as e:
                if attempt < max_attempts - 1:
                    delay = initial_delay * (backoff_factor ** attempt)
                    print(f"Request failed (attempt {attempt + 1}/{max_attempts}), "
                          f"retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    raise RuntimeError(f"Request failed after {max_attempts} attempts: {e}")

    def _sync_chat(self, request_params: Dict) -> Dict[str, Any]:
        """Synchronous chat request"""
        response = self.client.chat.completions.create(**request_params)

        result = {
            'message': {
                'content': response.choices[0].message.content or ''
            }
        }

        # Extract tool calls if present
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
        current_tool_call = None

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Collect content
            if delta.content:
                full_response += delta.content
                if on_chunk:
                    on_chunk(delta.content)

            # Collect tool calls
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    if tc_delta.index is not None:
                        # New tool call or continuation
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
        import os
        from datetime import datetime

        if not os.getenv('DEBUG_AGENT') and not os.getenv('DEBUG_LLM'):
            return

        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / 'logs'
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
        return self.chat(messages, tools=tools, stream=stream, on_chunk=on_chunk)

    def parse_tool_calls(self, response: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Extract tool calls from response

        Args:
            response: OpenAI response dict

        Returns:
            List of tool call dicts or None
        """
        message = response.get('message', {})
        tool_calls = message.get('tool_calls', [])

        if not tool_calls:
            return None

        # Ensure each tool call has required fields
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
        from .prompts import get_compression_prompt

        current_tokens = self.estimate_tokens(messages)

        compression_prompt = get_compression_prompt(
            current_tokens=current_tokens,
            target_tokens=target_tokens,
            must_keep=must_keep,
            compressible=compressible
        )

        compress_messages = [
            {'role': 'system', 'content': 'You are a context compression assistant.'},
            {'role': 'user', 'content': compression_prompt}
        ]

        # Use lower temperature for compression
        response = self.chat(compress_messages, temperature=0.3, stream=False)

        content = response['message']['content']
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse compression result: {e}\nContent: {content}")

    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Estimate token count for messages using character-based estimation

        Args:
            messages: List of message dicts

        Returns:
            Estimated token count (~4 chars per token for English)
        """
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        estimated_tokens = total_chars // 4  # ~4 chars per token for English
        estimated_tokens += len(messages) * 4  # Message overhead
        return estimated_tokens

    def set_model(self, model: str):
        """
        Set the model to use for requests

        Args:
            model: Model name (e.g., 'gpt-4-turbo', 'gpt-3.5-turbo')
        """
        self.model = model

    def list_models(self) -> List[str]:
        """
        List available models

        Returns:
            List of model names
        """
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            print(f"Failed to list models: {e}")
            return []
