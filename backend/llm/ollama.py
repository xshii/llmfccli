# -*- coding: utf-8 -*-
"""
Ollama client for Qwen3 model
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .base import BaseLLMClient
from .config import load_llm_config, get_project_root
from .retry import RetryConfig, with_retry
from .compression import compress_context, estimate_tokens_chinese


class OllamaClient(BaseLLMClient):
    """Ollama client for interacting with Qwen3 model"""

    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize Ollama client

        Args:
            config_path: Path to llm.yaml config file
            config: Direct config dict (takes precedence over config_path)
        """
        # Load configuration
        self.config = load_llm_config(config_path, config, section='ollama')

        # 验证必需配置
        self.base_url = self.config.get('base_url')
        if not self.base_url:
            raise ValueError("配置缺少 base_url")

        self.model = self.config.get('model') or self.config.get('models', {}).get('main')
        if not self.model:
            raise ValueError("配置缺少 model")

        self.timeout = self.config.get('timeout', 300)
        self.generation_params = self.config.get('generation', {})
        self.retry_config = RetryConfig.from_dict(
            self.config.get('retry', {})
        )
        self.stream_enabled = self.config.get('stream', False)
        self.think_enabled = self.config.get('think', False)  # 思考模式（GLM-4.7）

        # Session-based logging
        self._session_request_file: Optional[Path] = None
        self._session_conversation_file: Optional[Path] = None
        self._request_count = 0

        # Initialize log directory
        self._log_dir = get_project_root() / 'logs'
        self._log_dir.mkdir(exist_ok=True)

        # Start new session
        self.start_new_session()

        # Track last request/conversation file for debugging
        self.last_request_file = None
        self.last_conversation_file = None

        # Warm up model on initialization
        self._warmup()

    def start_new_session(self):
        """开始新的日志会话"""
        from datetime import datetime

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._session_request_file = self._log_dir / f'session_{timestamp}_requests.jsonl'
        self._session_conversation_file = self._log_dir / f'session_{timestamp}_conversations.log'
        self._request_count = 0

        with open(self._session_conversation_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f"# Session started at {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

    def _get_current_model(self) -> str:
        """获取当前应使用的模型"""
        try:
            from backend.roles import get_role_manager
            role_manager = get_role_manager()
            role_model = role_manager.get_model()
            if role_manager.check_role_model_exists():
                return role_model
            return self.model
        except Exception:
            return self.model

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Qwen3 using curl"""
        params = {**self.generation_params, **kwargs}
        current_model = self._get_current_model()

        data = {
            'model': current_model,
            'messages': messages,
            'stream': stream,
        }

        if params:
            data['options'] = params
        if tools:
            data['tools'] = tools
        if self.think_enabled:
            data['think'] = True

        def do_request():
            return self._execute_curl_request(data, on_chunk)

        return with_retry(do_request, self.retry_config)

    def _execute_curl_request(
        self,
        data: Dict,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Execute curl request to Ollama"""
        import tempfile
        from datetime import datetime

        # Write JSON to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            temp_file = f.name

        curl_cmd = ['curl', '-s', '-N', '--noproxy', 'localhost',
                   '-w', '\n{"http_code":%{http_code}}',  # 输出 HTTP 状态码
                   f'{self.base_url}/api/chat', '-d', f'@{temp_file}']

        # Log request
        self._request_count += 1
        request_timestamp = datetime.now().isoformat()

        with open(temp_file, 'r', encoding='utf-8') as f:
            request_data = json.load(f)

        if self._session_request_file:
            with open(self._session_request_file, 'a', encoding='utf-8', newline='\n') as f:
                log_entry = {
                    'request_id': self._request_count,
                    'timestamp': request_timestamp,
                    'data': request_data
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            self.last_request_file = str(self._session_request_file)

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

                        for token in stop_tokens:
                            if token in full_response:
                                full_response = full_response.split(token)[0]
                                process.kill()
                                break

                    if 'message' in chunk and 'tool_calls' in chunk['message']:
                        tool_calls.extend(chunk['message']['tool_calls'])
                    elif 'tool_calls' in chunk:
                        tool_calls.extend(chunk['tool_calls'])
                except json.JSONDecodeError:
                    # 检查是否是 HTTP 状态码行
                    if '"http_code"' in line:
                        try:
                            status = json.loads(line)
                            http_code = status.get('http_code', 200)
                            if http_code >= 400:
                                raise Exception(f"Ollama API error: HTTP {http_code}")
                        except json.JSONDecodeError:
                            pass

        process.wait()

        # Log conversation
        if self._session_conversation_file:
            self._log_conversation(request_data, request_timestamp, raw_lines, full_response, process)

        # Clean up
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

    def _log_conversation(self, request_data, timestamp, raw_lines, full_response, process):
        """Log conversation to file"""
        with open(self._session_conversation_file, 'a', encoding='utf-8', newline='\n') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"REQUEST #{self._request_count} @ {timestamp}\n")
            f.write(f"{'='*80}\n")
            f.write(json.dumps(request_data, ensure_ascii=False, indent=2))

            f.write(f"\n\n{'-'*40}\n")
            f.write("RESPONSE\n")
            f.write(f"{'-'*40}\n")
            raw_response = ''.join(raw_lines)
            try:
                response_json = json.loads(raw_response)
                f.write(json.dumps(response_json, indent=2, ensure_ascii=False))
            except:
                f.write(raw_response if raw_response else full_response)

            stderr_output = process.stderr.read() if process.stderr else ''
            if stderr_output:
                f.write(f"\n\n{'-'*40}\n")
                f.write("STDERR\n")
                f.write(f"{'-'*40}\n")
                f.write(stderr_output)

            f.write("\n\n")

        self.last_conversation_file = str(self._session_conversation_file)

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
        """Use Qwen3 to compress conversation history"""
        def chat_func(msgs):
            return self.chat(msgs, temperature=0.3)

        return compress_context(
            messages, target_tokens, must_keep, compressible,
            chat_func, estimate_tokens_chinese
        )

    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages"""
        return estimate_tokens_chinese(messages)

    def check_model_available(self) -> bool:
        """Check if model is available in Ollama"""
        try:
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
            self.start_new_session()
            self.last_conversation_file = None
            self.last_request_file = None
            print(f"✓ 模型 {self.model} 预热就绪")
        except Exception as e:
            print(f"警告: 模型预热失败: {e}")
