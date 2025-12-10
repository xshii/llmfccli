# -*- coding: utf-8 -*-
"""
Ollama client for Qwen3 model
"""

import json
import time
import subprocess
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import yaml

from .base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """Ollama client for interacting with Qwen3 model"""

    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize Ollama client

        Args:
            config_path: Path to llm.yaml or ollama.yaml config file
            config: Direct config dict (takes precedence over config_path)
        """
        # Load configuration
        if config is not None:
            # Use provided config directly
            self.config = config
        else:
            if config_path is None:
                # Try llm.yaml first, fallback to ollama.yaml
                project_root = Path(__file__).parent.parent.parent
                llm_config_path = project_root / "config" / "llm.yaml"
                ollama_config_path = project_root / "config" / "ollama.yaml"

                if llm_config_path.exists():
                    config_path = llm_config_path
                elif ollama_config_path.exists():
                    config_path = ollama_config_path
                else:
                    config_path = None

            if config_path and Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = yaml.safe_load(f)
                self.config = full_config.get('ollama', {})
            else:
                # Use default config if file not found
                self.config = {
                    'base_url': 'http://localhost:11434',
                    'model': 'qwen3',
                    'timeout': 300,
                    'stream': False,
                    'generation': {
                        'temperature': 0.1,
                        'top_p': 0.9,
                        'top_k': 40,
                        'num_ctx': 131072,
                        'repeat_penalty': 1.1,
                        'num_predict': 4096
                    },
                    'retry': {
                        'max_attempts': 3,
                        'backoff_factor': 2,
                        'initial_delay': 1
                    }
                }

        self.base_url = self.config.get('base_url', 'http://localhost:11434')
        self.model = self.config.get('model') or self.config.get('models', {}).get('main', 'qwen3')
        self.timeout = self.config.get('timeout', 300)
        self.generation_params = self.config.get('generation', {})
        self.retry_config = self.config.get('retry', {
            'max_attempts': 3,
            'backoff_factor': 2,
            'initial_delay': 1
        })
        self.stream_enabled = self.config.get('stream', False)

        # Track last request/conversation file for debugging
        self.last_request_file = None
        self.last_conversation_file = None

        # Warm up model on initialization
        self._warmup()

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat request to Qwen3 using curl

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            stream: Enable streaming output (default: False)
            on_chunk: Optional callback function called with each content chunk
            **kwargs: Override generation parameters

        Returns:
            Response dict with 'message' and optional 'tool_calls'
        """
        # Merge generation params with kwargs
        params = {**self.generation_params, **kwargs}

        # Prepare request
        data = {
            'model': self.model,
            'messages': messages,
            'stream': stream,
        }

        if params:
            data['options'] = params

        if tools:
            data['tools'] = tools

        # Retry logic
        max_attempts = self.retry_config['max_attempts']
        backoff_factor = self.retry_config['backoff_factor']
        initial_delay = self.retry_config['initial_delay']

        for attempt in range(max_attempts):
            try:
                # Write JSON to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                    temp_file = f.name

                curl_cmd = ['curl', '-s', '-N', '--noproxy', 'localhost',
                           f'{self.base_url}/api/chat', '-d', f'@{temp_file}']

                # Save request to logs
                import os
                from datetime import datetime
                import pathlib

                project_root = pathlib.Path(__file__).parent.parent.parent
                log_dir = project_root / 'logs'
                log_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                request_file = log_dir / f'request_{timestamp}.json'
                with open(temp_file, 'r', encoding='utf-8') as f:
                    request_data = json.load(f)
                with open(request_file, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(request_data, f, ensure_ascii=False, indent=2)

                self.last_request_file = str(request_file)

                if os.getenv('DEBUG_AGENT'):
                    print(f"\n=== CURL REQUEST ===")
                    print(f"Saved to: {request_file}")
                    print(f"=== END CURL REQUEST ===\n")

                if os.getenv('DEBUG_AGENT') or os.getenv('DEBUG_LLM'):
                    print(f"\033[90mExecuting: curl -s -N \"{self.base_url}/api/chat\" -d @{temp_file}\033[0m")

                # Stream response
                process = subprocess.Popen(
                    curl_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                full_response = ""
                tool_calls = []
                stop_tokens = ['<|endoftext|>', '<|im_end|>']
                raw_lines = []

                for line in process.stdout:
                    if os.getenv('DEBUG_AGENT'):
                        raw_lines.append(line)
                    if line.strip():
                        try:
                            chunk = json.loads(line)

                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                full_response += content

                                if on_chunk and content:
                                    on_chunk(content.replace('\r', ''))

                                should_stop = False
                                for token in stop_tokens:
                                    if token in full_response:
                                        full_response = full_response.split(token)[0]
                                        should_stop = True
                                        break

                                if should_stop:
                                    process.kill()
                                    break

                            if 'message' in chunk and 'tool_calls' in chunk['message']:
                                tool_calls.extend(chunk['message']['tool_calls'])
                            elif 'tool_calls' in chunk:
                                tool_calls.extend(chunk['tool_calls'])

                        except:
                            pass

                process.wait()

                # Save conversation log
                if log_dir and request_file:
                    combined_file = log_dir / request_file.name.replace('request_', 'conversation_')

                    with open(combined_file, 'w', encoding='utf-8', newline='\n') as f:
                        f.write("=" * 80 + "\n")
                        f.write("REQUEST\n")
                        f.write("=" * 80 + "\n")
                        with open(request_file, 'r', encoding='utf-8') as req:
                            f.write(req.read())

                        f.write("\n\n" + "=" * 80 + "\n")
                        f.write("RESPONSE\n")
                        f.write("=" * 80 + "\n")
                        raw_response = ''.join(raw_lines)
                        try:
                            response_json = json.loads(raw_response)
                            f.write(json.dumps(response_json, indent=2, ensure_ascii=False))
                        except:
                            f.write(raw_response)

                        stderr_output = process.stderr.read() if process.stderr else ''
                        if stderr_output:
                            f.write("\n\n" + "=" * 80 + "\n")
                            f.write("STDERR\n")
                            f.write("=" * 80 + "\n")
                            f.write(stderr_output)

                    self.last_conversation_file = str(combined_file)
                    self.last_request_file = None

                    try:
                        request_file.unlink()
                    except:
                        pass

                if os.getenv('DEBUG_AGENT'):
                    print(f"\n=== RAW CURL OUTPUT ({len(raw_lines)} lines) ===")
                    for i, line in enumerate(raw_lines[:10]):
                        print(f"Line {i}: {line[:200]}")
                    print("=== END RAW CURL OUTPUT ===\n")

                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass

                result = {
                    'message': {
                        'content': full_response.replace('\r', '').strip()
                    }
                }

                if tool_calls:
                    result['message']['tool_calls'] = tool_calls

                return result

            except Exception as e:
                if attempt < max_attempts - 1:
                    delay = initial_delay * (backoff_factor ** attempt)
                    print(f"Request failed (attempt {attempt + 1}/{max_attempts}), "
                          f"retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    raise RuntimeError(f"Request failed after {max_attempts} attempts: {e}")

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
            stream: Enable streaming output (default: False)
            on_chunk: Optional callback function called with each content chunk

        Returns:
            Response with potential tool_calls
        """
        return self.chat(messages, tools=tools, stream=stream, on_chunk=on_chunk)

    def parse_tool_calls(self, response: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Extract tool calls from response and ensure each has a unique id

        Args:
            response: Ollama response dict

        Returns:
            List of tool call dicts or None
        """
        message = response.get('message', {})
        tool_calls = message.get('tool_calls', [])

        if not tool_calls:
            tool_calls = response.get('tool_calls', [])

        if not tool_calls:
            return None

        for i, tool_call in enumerate(tool_calls):
            if 'id' not in tool_call:
                func_name = tool_call.get('function', {}).get('name', 'unknown')
                tool_call['id'] = f"{func_name}_{i}"

        return tool_calls

    def compress_context(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int,
        must_keep: str,
        compressible: str
    ) -> Dict[str, Any]:
        """
        Use Qwen3 to compress conversation history

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

        response = self.chat(compress_messages, temperature=0.3)

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
        Estimate token count for messages

        Args:
            messages: List of message dicts

        Returns:
            Estimated token count
        """
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        estimated_tokens = total_chars // 3
        estimated_tokens += len(messages) * 10
        return estimated_tokens

    def check_model_available(self) -> bool:
        """
        Check if model is available in Ollama

        Returns:
            True if model is available
        """
        try:
            import subprocess
            result = subprocess.run(
                ['curl', '-s', f'{self.base_url}/api/tags'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                model_names = [m['name'] for m in data.get('models', [])]
                base_name = self.model.split(':')[0]
                return any(base_name in name for name in model_names)
            return False
        except Exception as e:
            print(f"Failed to check model availability: {e}")
            return False

    def _warmup(self):
        """Warm up model by sending a simple request"""
        try:
            print(f"正在预热模型 {self.model}...")
            self.chat([{'role': 'user', 'content': 'hi'}], temperature=0.1)
            self.last_conversation_file = None
            self.last_request_file = None
            print(f"✓ 模型 {self.model} 预热就绪")
        except Exception as e:
            print(f"警告: 模型预热失败: {e}")
