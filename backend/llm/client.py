"""
Ollama client wrapper for Qwen3 model
"""

import json
import time
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml


class OllamaClient:
    """Ollama client for interacting with Qwen3 model"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Ollama client
        
        Args:
            config_path: Path to ollama.yaml config file
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "ollama.yaml"
        
        config_path = Path(config_path).resolve()
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            # Use default config if file not found
            config = {
                'ollama': {
                    'base_url': 'http://localhost:11434',
                    'model': 'qwen3',
                    'timeout': 300,
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
            }
        
        self.config = config['ollama']
        self.base_url = self.config['base_url']
        self.model = self.config['model']
        self.timeout = self.config['timeout']
        self.generation_params = self.config['generation']
        self.retry_config = self.config['retry']
        
        # Warm up model on initialization
        self._warmup()
        
    def chat(self, messages: List[Dict[str, str]], 
             tools: Optional[List[Dict]] = None,
             **kwargs) -> Dict[str, Any]:
        """
        Send chat request to Qwen3 using curl
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            **kwargs: Override generation parameters
            
        Returns:
            Response dict with 'message' and optional 'tool_calls'
        """
        import subprocess
        import json
        
        # Merge generation params with kwargs
        params = {**self.generation_params, **kwargs}
        
        # Prepare request
        data = {
            'model': self.model,
            'messages': messages,
            'options': params,
            'stream': False,
            'stop': ['<|endoftext|>', '<|im_end|>', 'Human:', '\nHuman:']
        }
        
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
                
                curl_cmd = ['curl', '-s', '-N', '--noproxy', 'localhost', f'{self.base_url}/api/chat', '-d', f'@{temp_file}']

                # DEBUG: Save request to logs
                import os
                from datetime import datetime
                log_dir = None
                request_file = None
                if os.getenv('DEBUG_AGENT'):
                    # Create logs directory
                    import pathlib
                    project_root = pathlib.Path(__file__).parent.parent.parent
                    log_dir = project_root / 'logs'
                    log_dir.mkdir(exist_ok=True)

                    # Save request
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    request_file = log_dir / f'request_{timestamp}.json'
                    with open(temp_file, 'r') as f:
                        request_data = json.load(f)
                    with open(request_file, 'w', encoding='utf-8') as f:
                        json.dump(request_data, f, ensure_ascii=False, indent=2)

                    print(f"\n=== CURL REQUEST ===")
                    print(f"Saved to: {request_file}")
                    print(f"=== END CURL REQUEST ===\n")

                print(f"\nExecuting: curl -s -N \"{self.base_url}/api/chat\" -d @{temp_file}\n")
                
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

                # DEBUG: Raw response collection
                import os as os_check
                raw_lines = []

                for line in process.stdout:
                    if os_check.getenv('DEBUG_AGENT'):
                        raw_lines.append(line)
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            
                            # Collect content
                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                full_response += content
                                
                                # Check for stop tokens
                                should_stop = False
                                for token in stop_tokens:
                                    if token in full_response:
                                        full_response = full_response.split(token)[0]
                                        should_stop = True
                                        break
                                
                                if should_stop:
                                    process.kill()
                                    break
                            
                            # Collect tool_calls
                            if 'message' in chunk and 'tool_calls' in chunk['message']:
                                tool_calls.extend(chunk['message']['tool_calls'])
                            elif 'tool_calls' in chunk:
                                tool_calls.extend(chunk['tool_calls'])
                                
                        except:
                            pass
                
                process.wait()

                # DEBUG: Save request+response together
                if os_check.getenv('DEBUG_AGENT'):
                    if log_dir and request_file:
                        # Combine request and response in one file
                        combined_file = log_dir / request_file.name.replace('request_', 'conversation_')

                        with open(combined_file, 'w', encoding='utf-8') as f:
                            f.write("=" * 80 + "\n")
                            f.write("REQUEST\n")
                            f.write("=" * 80 + "\n")
                            # Read and write request
                            with open(request_file, 'r') as req:
                                f.write(req.read())

                            f.write("\n\n" + "=" * 80 + "\n")
                            f.write("RESPONSE\n")
                            f.write("=" * 80 + "\n")
                            # Format response as indented JSON
                            raw_response = ''.join(raw_lines)
                            try:
                                response_json = json.loads(raw_response)
                                f.write(json.dumps(response_json, indent=2, ensure_ascii=False))
                            except:
                                # If not valid JSON, write raw
                                f.write(raw_response)

                            # Save stderr if any
                            stderr_output = process.stderr.read() if process.stderr else ''
                            if stderr_output:
                                f.write("\n\n" + "=" * 80 + "\n")
                                f.write("STDERR\n")
                                f.write("=" * 80 + "\n")
                                f.write(stderr_output)

                        # Delete separate request file
                        try:
                            request_file.unlink()
                        except:
                            pass

                    print(f"\n=== RAW CURL OUTPUT ({len(raw_lines)} lines) ===")
                    for i, line in enumerate(raw_lines[:10]):  # First 10 lines only
                        print(f"Line {i}: {line[:200]}")  # First 200 chars
                    print("=== END RAW CURL OUTPUT ===\n")

                # Clean up temp file
                import os
                try:
                    os.unlink(temp_file)
                except:
                    pass

                # Return in expected format
                result = {
                    'message': {
                        'content': full_response.strip()
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
    
    def chat_with_tools(self, messages: List[Dict[str, str]], 
                       tools: List[Dict]) -> Dict[str, Any]:
        """
        Chat with function calling support
        
        Args:
            messages: Conversation history
            tools: Tool definitions in OpenAI format
            
        Returns:
            Response with potential tool_calls
        """
        response = self.chat(messages, tools=tools)
        return response
    
    def parse_tool_calls(self, response: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        Extract tool calls from response
        
        Args:
            response: Ollama response dict
            
        Returns:
            List of tool call dicts or None
        """
        # Check in message first
        message = response.get('message', {})
        tool_calls = message.get('tool_calls', [])
        
        # If not in message, check at root level
        if not tool_calls:
            tool_calls = response.get('tool_calls', [])
        
        if not tool_calls:
            return None
        
        return tool_calls
    
    def compress_context(self, messages: List[Dict[str, str]], 
                        target_tokens: int,
                        must_keep: str,
                        compressible: str) -> Dict[str, Any]:
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
        
        # Request compression
        compress_messages = [
            {'role': 'system', 'content': 'You are a context compression assistant.'},
            {'role': 'user', 'content': compression_prompt}
        ]
        
        response = self.chat(compress_messages, temperature=0.3)
        
        # Parse JSON response
        content = response['message']['content']
        try:
            # Try to extract JSON from markdown code blocks if present
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
        # Simple estimation: ~4 chars per token for English, ~2 for Chinese
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        
        # Assume mixed content, use 3 chars per token
        estimated_tokens = total_chars // 3
        
        # Add overhead for role and structure
        estimated_tokens += len(messages) * 10
        
        return estimated_tokens
    
    def check_model_available(self) -> bool:
        """
        Check if Qwen3 model is available in Ollama
        
        Returns:
            True if model is available
        """
        try:
            models = self.client.list()
            model_names = [m['name'] for m in models.get('models', [])]
            # Check if any model contains the base name
            base_name = self.model.split(':')[0]
            return any(base_name in name for name in model_names)
        except Exception as e:
            print(f"Failed to check model availability: {e}")
            return False
    
    def pull_model(self):
        """Pull Qwen3 model if not available"""
        print(f"Pulling model {self.model}...")
        try:
            self.client.pull(self.model)
            print(f"Model {self.model} pulled successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to pull model {self.model}: {e}")
    
    def _warmup(self):
        """Warm up model by sending a simple request"""
        try:
            print(f"Warming up model {self.model}...")
            self.chat([{'role': 'user', 'content': 'hi'}], temperature=0.1)
            print(f"✓ Model {self.model} loaded and ready")
        except Exception as e:
            print(f"Warning: Model warmup failed: {e}")
    
    def format_tool_result(self, tool_call_id: str, result: Any) -> Dict[str, str]:
        """
        Format tool execution result for next chat turn
        
        Args:
            tool_call_id: ID of the tool call
            result: Tool execution result
            
        Returns:
            Message dict for tool result
        """
        return {
            'role': 'tool',
            'content': json.dumps(result, ensure_ascii=False),
            'tool_call_id': tool_call_id
        }


# Utility function for creating tool definitions
def create_tool_definition(name: str, description: str, 
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create tool definition in OpenAI function calling format
    
    Args:
        name: Tool name
        description: Tool description
        parameters: JSON schema for parameters
        
    Returns:
        Tool definition dict
    """
    return {
        'type': 'function',
        'function': {
            'name': name,
            'description': description,
            'parameters': parameters
        }
    }


# Example tool definitions
EXAMPLE_TOOLS = [
    create_tool_definition(
        name='view_file',
        description='Read file contents with optional line range',
        parameters={
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
    ),
    create_tool_definition(
        name='grep_search',
        description='Search for pattern in files',
        parameters={
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'Search pattern (regex supported)'
                },
                'scope': {
                    'type': 'string',
                    'description': 'Search scope directory'
                }
            },
            'required': ['pattern']
        }
    )
]
