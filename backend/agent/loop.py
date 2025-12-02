# -*- coding: utf-8 -*-
"""
Agent main loop for executing tasks with LLM and tools
"""

import re
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from ..llm.client import OllamaClient
from .token_counter import TokenCounter
from .tools import ToolExecutor, RegistryToolExecutor, ToolConfirmation, ConfirmAction


class AgentLoop:
    """Main agent loop for task execution"""

    def __init__(self,
                 client: Optional[OllamaClient] = None,
                 tool_executor: Optional[ToolExecutor] = None,
                 project_root: Optional[str] = None,
                 confirmation_callback: Optional[Callable] = None,
                 tool_output_callback: Optional[Callable] = None):
        """
        Initialize agent loop

        Args:
            client: OllamaClient instance (injected dependency)
            tool_executor: ToolExecutor instance (injected dependency)
            project_root: Project root directory
            confirmation_callback: Callback function for user confirmation
            tool_output_callback: Callback function for tool output (tool_name, output, args)
        """
        self.client = client or OllamaClient()
        self.project_root = project_root or str(Path.cwd())

        # Initialize components
        self.token_counter = TokenCounter()

        # Initialize tool confirmation first (needed by tool executor)
        self.confirmation = ToolConfirmation()
        if confirmation_callback:
            self.confirmation.set_confirmation_callback(confirmation_callback)

        # Initialize tool executor (with confirmation manager for smart handling)
        # Pass self (agent) for agent-specific tools like compact_last
        self.tool_executor = tool_executor or RegistryToolExecutor(
            self.project_root,
            confirmation_manager=self.confirmation,
            agent=self
        )

        # Tool output callback
        self.tool_output_callback = tool_output_callback

        # State
        self.conversation_history: List[Dict[str, str]] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.active_files: List[str] = []

        # Configuration
        self.max_iterations = 20
        self.max_retries = 3
        self.stopped_due_to_max_retries = False

        # Active file (for VSCode integration)
        self.active_file: Optional[str] = None
    
    def set_project_root(self, root: str):
        """Set project root and reinitialize tools"""
        self.project_root = root
        if isinstance(self.tool_executor, RegistryToolExecutor):
            self.tool_executor.reinitialize(self.project_root)
    
    def set_active_file(self, file_path: str):
        """Set active file (from VSCode)"""
        self.active_file = file_path
    
    def set_max_retries(self, max_retries: int):
        """Set maximum retry count"""
        self.max_retries = max_retries

    def _clean_system_reminders(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        清理历史消息中的 <system-reminder> 标签，只保留最后一条用户消息中的。

        这样可以避免多轮对话中旧的 IDE 文件信息误导模型。
        """
        if not messages:
            return messages

        pattern = re.compile(r'<system-reminder>.*?</system-reminder>\s*', re.DOTALL)
        cleaned = []

        for i, msg in enumerate(messages):
            is_last_user_msg = (
                msg.get('role') == 'user' and
                i == len(messages) - 1
            )

            if is_last_user_msg:
                # 保留最后一条用户消息的 system-reminder
                cleaned.append(msg)
            elif msg.get('role') == 'user' and pattern.search(msg.get('content', '')):
                # 清理历史用户消息中的 system-reminder
                new_content = pattern.sub('', msg.get('content', '')).strip()
                cleaned.append({**msg, 'content': new_content})
            else:
                cleaned.append(msg)

        return cleaned

    def run(self, user_input: str, stream: bool = False, on_chunk=None) -> str:
        """
        Execute agent loop for user input

        Args:
            user_input: User's request
            stream: Enable streaming output (default: False)
            on_chunk: Optional callback function for streaming chunks

        Returns:
            Agent's final response
        """
        # Store stream mode for later use
        self._stream_mode = stream

        # Add user message
        user_message = {'role': 'user', 'content': user_input}
        self.conversation_history.append(user_message)

        # Update token count
        self.token_counter.update_usage(
            'recent_messages',
            self.token_counter.count_messages(self.conversation_history)
        )

        # System prompt is now in Modelfile (claude-qwen:latest)
        # No need to pass it dynamically
        # 清理历史消息中的 system-reminder，只保留最新的
        messages = self._clean_system_reminders(list(self.conversation_history))

        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1

            # Get tool schemas from executor
            tools = self.tool_executor.get_tool_schemas()

            # Check if context would exceed token limit
            current_tokens = self.token_counter.count_messages(messages)
            max_tokens = self.token_counter.max_tokens

            if current_tokens > max_tokens * 0.95:  # 超过 95%
                # 不调用 LLM，而是给出建议
                suggestion_msg = self._create_token_limit_suggestion(current_tokens, max_tokens)
                self.conversation_history.append({
                    'role': 'system',
                    'content': suggestion_msg
                })

                # 更新 messages 以包含建议
                messages = self._clean_system_reminders(list(self.conversation_history))

                # 继续循环，让 LLM 看到建议并重新规划
                continue

            # DEBUG: Log request
            import os
            if os.getenv('DEBUG_AGENT'):
                print(f"\n=== LLM REQUEST (iteration {iteration}) ===")
                import json
                print(f"Messages count: {len(messages)}")
                print(f"Last message: {messages[-1] if messages else 'none'}")
                print(f"Tools count: {len(tools)}")
                if tools:
                    print(f"First tool: {tools[0]['function']['name']}")
                print("=== END REQUEST ===\n")

            # Call LLM
            try:
                response = self.client.chat_with_tools(messages, tools, stream=stream, on_chunk=on_chunk)

                # DEBUG: Log raw response
                if os.getenv('DEBUG_AGENT'):
                    print(f"\n=== RAW LLM RESPONSE (iteration {iteration}) ===")
                    import json
                    print(json.dumps(response, indent=2, ensure_ascii=False))
                    print("=== END RAW RESPONSE ===\n")

            except Exception as e:
                error_msg = f"LLM call failed: {e}"
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': error_msg
                })
                return error_msg

            # Extract message
            assistant_message = response.get('message', {})
            content = assistant_message.get('content', '')

            # Parse tool calls
            tool_calls = self.client.parse_tool_calls(response)
            
            # No tool calls - conversation complete
            if not tool_calls:
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': content
                })
                return content
            
            # Execute tool calls
            self.tool_calls.extend(tool_calls)

            # Add assistant message with tool calls
            self.conversation_history.append({
                'role': 'assistant',
                'content': content,
                'tool_calls': tool_calls
            })

            # Display assistant's thinking before executing tools
            # 在流式模式下，内容已经被实时打印了，不需要再次显示
            if self.tool_output_callback and not self._stream_mode:
                try:
                    # Show assistant's content or a witty message
                    if content and content.strip():
                        self.tool_output_callback('__assistant_thinking__', content, {})
                    else:
                        self.tool_output_callback('__assistant_thinking__',
                                                 '💭 AI正在指挥做事，没功夫说话...', {})
                except Exception:
                    pass

            # Execute each tool
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']

                # Parse arguments
                try:
                    arguments = tool_call['function']['arguments']
                    if isinstance(arguments, str):
                        import json
                        arguments = json.loads(arguments)
                except Exception as e:
                    arguments = {}

                # Check if confirmation is needed
                tool_instance = self.tool_executor.registry.get(tool_name)
                if self.confirmation.needs_confirmation(tool_name, arguments):
                    # Show preview before asking user to confirm (only when confirmation needed)
                    if tool_instance and hasattr(tool_instance, 'get_diff_preview'):
                        try:
                            tool_instance.get_diff_preview(**arguments)
                        except Exception:
                            # Preview failed, continue with confirmation
                            pass

                    action = self.confirmation.confirm_tool_execution(tool_name, arguments)

                    if action == ConfirmAction.DENY:
                        # Close diff preview if it was shown
                        if tool_instance and hasattr(tool_instance, 'get_diff_preview'):
                            try:
                                from backend.rpc.client import is_vscode_mode
                                from backend.feature import is_feature_enabled
                                if is_vscode_mode() and is_feature_enabled("ide_integration.show_diff_before_edit"):
                                    from backend.tools.vscode_tools import vscode
                                    vscode.close_diff()
                            except Exception:
                                # Failed to close diff, continue
                                pass

                        # User denied - add error message and skip execution
                        result = {
                            'success': False,
                            'error': 'User denied tool execution',
                            'denied_by_user': True
                        }

                        # Add tool result to history
                        tool_message = {
                            'role': 'tool',
                            'content': self._format_tool_result(result),
                            'tool_call_id': tool_call.get('id', f'call_{iteration}')
                        }
                        self.conversation_history.append(tool_message)

                        # Stop execution - user wants to stop
                        final_msg = "Tool execution stopped by user."
                        self.conversation_history.append({
                            'role': 'assistant',
                            'content': final_msg
                        })
                        return final_msg

                # Execute tool via executor
                result = self.tool_executor.execute_tool(tool_name, arguments)

                # Close diff preview after execution to ensure clean state
                if tool_instance and hasattr(tool_instance, 'get_diff_preview'):
                    try:
                        from backend.rpc.client import is_vscode_mode
                        from backend.feature import is_feature_enabled
                        if is_vscode_mode() and is_feature_enabled("ide_integration.show_diff_before_edit"):
                            from backend.tools.vscode_tools import vscode
                            vscode.close_diff()
                    except Exception:
                        pass

                # Call tool output callback if provided
                if self.tool_output_callback:
                    try:
                        self.tool_output_callback(tool_name, str(result), arguments)
                    except Exception as e:
                        # Don't let callback errors break execution
                        import os
                        if os.getenv('DEBUG_AGENT'):
                            print(f"Tool output callback error: {e}")

                # DEBUG: Log tool results
                import os
                if os.getenv('DEBUG_AGENT'):
                    print(f"\n=== TOOL RESULT: {tool_name} ===")
                    print(f"Args: {arguments}")
                    result_str = str(result)[:500]  # First 500 chars
                    print(f"Result: {result_str}...")
                    print("=== END TOOL RESULT ===\n")

                # Track active files (using executor to check if file operation)
                if self.tool_executor.is_file_operation(tool_name):
                    file_path = arguments.get('path', '')
                    if file_path and file_path not in self.active_files:
                        self.active_files.append(file_path)

                # Add tool result to history
                tool_message = {
                    'role': 'tool',
                    'content': self._format_tool_result(result),
                    'tool_call_id': tool_call.get('id', f'call_{iteration}')
                }
                self.conversation_history.append(tool_message)

            # Update messages for next iteration
            # System prompt is in Modelfile, no need to pass it
            messages = self._clean_system_reminders(list(self.conversation_history))

            # Check if should compress
            if self.token_counter.should_compress(time.time()):
                self._compress_context()
        
        # Max iterations reached
        final_msg = f"Reached maximum iterations ({self.max_iterations}). Task may be incomplete."
        self.conversation_history.append({
            'role': 'assistant',
            'content': final_msg
        })
        return final_msg
    
    def _create_token_limit_suggestion(self, current_tokens: int, max_tokens: int) -> str:
        """创建 token 超限建议消息"""
        usage_pct = (current_tokens / max_tokens) * 100

        suggestion = f"""⚠️ Context Token Limit Alert

Current context size: {current_tokens:,} tokens ({usage_pct:.1f}% of {max_tokens:,} limit)

Your last request would exceed the token limit. Please use more targeted tools:

**Recommended Actions:**

1. **For file reading**: Use `line_range` parameter
   - Instead of: view_file(path="large_file.cpp")
   - Use: view_file(path="large_file.cpp", line_range=[1, 100])

2. **For code search**: Use `grep_search` instead of reading entire files
   - grep_search(pattern="function_name", path="directory")

3. **For directory listing**: Limit depth
   - list_dir(path=".", max_depth=2)

4. **Break down the task**: Work on smaller sections incrementally

Please reformulate your request with more specific, targeted tool calls.
"""
        return suggestion

    def _format_tool_result(self, result: Any) -> str:
        """Format tool result for LLM"""
        import json

        if isinstance(result, dict):
            # Truncate large content
            if 'content' in result:
                content = result['content']
                result = result.copy()
                result['content'] = self.token_counter.truncate_tool_result(content)

            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return str(result)
    
    def _compress_context(self):
        """Compress conversation history"""
        # Build must-keep information
        must_keep = f"""
Active files: {', '.join(self.active_files)}
Project structure: {self.project_root}
"""
        
        # Build compressible content
        compressible = f"{len(self.conversation_history)} messages"
        
        # Get current and target tokens
        current_tokens = self.token_counter.count_messages(self.conversation_history)
        target_tokens = self.token_counter.get_compression_target()
        
        try:
            # Call LLM to compress
            compression_result = self.client.compress_context(
                self.conversation_history,
                target_tokens,
                must_keep,
                compressible
            )
            
            # Apply compression
            keep_indices = compression_result.get('keep_message_indices', [])
            compressed_summary = compression_result.get('compressed_summary', '')
            
            # Build new history
            new_history = []
            
            # Add compressed summary
            if compressed_summary:
                new_history.append({
                    'role': 'system',
                    'content': f"[Compressed History]\n{compressed_summary}"
                })
            
            # Add kept messages
            for idx in keep_indices:
                if 0 <= idx < len(self.conversation_history):
                    new_history.append(self.conversation_history[idx])
            
            # Update history
            self.conversation_history = new_history
            
            # Update token count
            self.token_counter.update_usage(
                'compressed_history',
                self.token_counter.count_messages(new_history)
            )
            
            # Update last compression time
            self.token_counter.last_compression_time = time.time()
            
        except Exception as e:
            print(f"Warning: Context compression failed: {e}")
    
    def get_usage_report(self) -> str:
        """Get token usage report"""
        return self.token_counter.get_usage_report()
    
    def save_session(self, session_file: str):
        """Save current session to file"""
        import json
        from datetime import datetime
        
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'project_root': self.project_root,
            'active_files': self.active_files,
            'last_error': self.conversation_history[-1].get('content', '') if self.conversation_history else '',
            'attempted_fixes': [
                {
                    'tool': call['function']['name'],
                    'arguments': call['function'].get('arguments', {})
                }
                for call in self.tool_calls[-5:]  # Last 5 tool calls
            ],
            'compressed_context': self._get_context_summary(),
            'next_steps': self._suggest_next_steps()
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def _get_context_summary(self) -> str:
        """Get summary of current context"""
        summary_parts = [
            f"Files modified: {len(self.active_files)}",
            f"Tool calls: {len(self.tool_calls)}",
            f"Messages: {len(self.conversation_history)}"
        ]
        return '; '.join(summary_parts)
    
    def _suggest_next_steps(self) -> List[str]:
        """Suggest next steps based on current state"""
        suggestions = []
        
        # Check if there were compilation errors
        if any('error' in str(call).lower() for call in self.tool_calls[-3:]):
            suggestions.append("Review compilation errors manually")
            suggestions.append("Check if dependencies are properly configured")
        
        # Check if files were modified
        if self.active_files:
            suggestions.append(f"Review changes in: {', '.join(self.active_files[:3])}")
        
        # Default suggestion
        if not suggestions:
            suggestions.append("Verify the changes and test manually")
        
        return suggestions
