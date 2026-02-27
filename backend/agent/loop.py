# -*- coding: utf-8 -*-
"""
Agent main loop for executing tasks with LLM and tools

使用设计模式:
- Pipeline: 消息处理
- Chain of Responsibility: 工具执行
- Command: 工具调用记录
- Observer: 事件通知
"""

import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..llm import BaseLLMClient, create_client
from ..llm.prompts import get_system_prompt
from .token_counter import TokenCounter
from .tools import (
    ConfirmAction,
    RegistryToolExecutor,
    ToolConfirmation,
    ToolExecutor,
)
from .patterns import (
    # Pipeline
    MessagePipeline,
    # Chain
    ExecutionContext,
    ToolExecutionChain,
    PreviewHandler,
    ConfirmationHandler,
    ExecutionHandlerImpl,
    CallbackHandler,
    CleanupHandler,
    # Command
    CommandHistory,
    CommandFactory,
    # Observer
    AgentEvent,
    get_event_bus,
)


class AgentLoop:
    """Main agent loop for task execution"""

    def __init__(self,
                 client: Optional[BaseLLMClient] = None,
                 tool_executor: Optional[ToolExecutor] = None,
                 project_root: Optional[str] = None,
                 confirmation_callback: Optional[Callable] = None,
                 tool_output_callback: Optional[Callable] = None,
                 backend: Optional[str] = None):
        """
        Initialize agent loop

        Args:
            client: LLM client instance
            tool_executor: ToolExecutor instance
            project_root: Project root directory
            confirmation_callback: Callback function for user confirmation
            tool_output_callback: Callback function for tool output
            backend: LLM backend to use ('ollama' or 'openai')
        """
        self.client = client or create_client(backend=backend, task='main_agent')
        self.project_root = project_root or str(Path.cwd())

        # Initialize components
        self.token_counter = TokenCounter()

        # Initialize tool confirmation
        self.confirmation = ToolConfirmation()
        if confirmation_callback:
            self.confirmation.set_confirmation_callback(confirmation_callback)

        # Initialize tool executor
        self.tool_executor = tool_executor or RegistryToolExecutor(
            self.project_root,
            confirmation_manager=self.confirmation,
            agent=self
        )

        # Tool output callback
        self.tool_output_callback = tool_output_callback

        # State
        self.conversation_history: List[Dict[str, str]] = []
        self.active_files: List[str] = []

        # Configuration
        self.max_iterations = 20
        self.max_retries = 3
        self.stopped_due_to_max_retries = False

        # Active file (for VSCode integration)
        self.active_file: Optional[str] = None

        # === 设计模式组件 ===

        # 消息处理管道
        self.message_pipeline = MessagePipeline.default()

        # 命令历史
        self.command_history = CommandHistory()

        # 事件总线
        self.events = get_event_bus()

        # 工具执行链（延迟初始化，需要 cleanup 函数）
        self._execution_chain: Optional[ToolExecutionChain] = None

    @property
    def execution_chain(self) -> ToolExecutionChain:
        """获取工具执行链（延迟初始化）"""
        if self._execution_chain is None:
            self._execution_chain = self._create_execution_chain()
        return self._execution_chain

    def _create_execution_chain(self) -> ToolExecutionChain:
        """创建工具执行链"""
        chain = ToolExecutionChain()

        # 1. 预览处理器
        chain.add(PreviewHandler(
            should_preview=lambda name: self._should_show_preview(name)
        ))

        # 2. 确认处理器
        chain.add(ConfirmationHandler(
            self.confirmation,
            on_deny=self._on_tool_denied
        ))

        # 3. 执行处理器
        chain.add(ExecutionHandlerImpl(self.tool_executor))

        # 4. 回调处理器
        if self.tool_output_callback:
            chain.add(CallbackHandler(self.tool_output_callback))

        # 5. 清理处理器
        chain.add(CleanupHandler(self._cleanup_after_tool))

        return chain

    def _should_show_preview(self, tool_name: str) -> bool:
        """判断是否应该显示预览"""
        try:
            from backend.rpc.client import is_vscode_mode
            from backend.utils.feature import is_feature_enabled
            return (is_vscode_mode() and
                    is_feature_enabled("ide_integration.show_diff_before_edit"))
        except Exception:
            return False

    def _on_tool_denied(self, ctx: ExecutionContext, reason: str):
        """工具被拒绝时的回调"""
        self.events.emit(AgentEvent.TOOL_DENIED,
                        tool_name=ctx.tool_name,
                        reason=reason)
        self._cleanup_after_tool(ctx)

    def _cleanup_after_tool(self, ctx: ExecutionContext):
        """工具执行后清理"""
        if ctx.metadata.get('preview_shown'):
            try:
                from backend.rpc.client import is_vscode_mode
                if is_vscode_mode():
                    from backend.tools.vscode_tools import vscode
                    vscode.close_diff()

                    # accept 后打开修改的文件
                    if ctx.error is None and ctx.arguments.get('path'):
                        vscode.open_file(ctx.arguments['path'])
            except Exception:
                pass

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

    # 向后兼容：保留 tool_calls 属性
    @property
    def tool_calls(self) -> List[Dict[str, Any]]:
        """获取工具调用历史（向后兼容）"""
        return [
            {
                'function': {
                    'name': cmd.tool_name,
                    'arguments': cmd.arguments
                },
                'id': cmd.tool_call_id
            }
            for cmd in self.command_history.commands
        ]

    def run(self, user_input: str, stream: bool = False, on_chunk=None) -> str:
        """
        Execute agent loop for user input

        Args:
            user_input: User's request
            stream: Enable streaming output
            on_chunk: Callback for streaming chunks

        Returns:
            Agent's final response
        """
        self._stream_mode = stream

        # 发送循环开始事件
        self.events.emit(AgentEvent.LOOP_STARTED, user_input=user_input)

        # 添加用户消息
        user_message = {'role': 'user', 'content': user_input}
        self.conversation_history.append(user_message)

        # 更新 token 计数
        self.token_counter.update_usage(
            'recent_messages',
            self.token_counter.count_messages(self.conversation_history)
        )

        # 使用管道处理消息
        messages = self.message_pipeline.process(list(self.conversation_history))

        # 注入 system prompt 作为第一条消息（pipeline 之后，避免被清理或截断）
        system_msg = {'role': 'system', 'content': get_system_prompt(self.project_root)}
        messages = [system_msg] + messages

        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            self.events.emit(AgentEvent.ITERATION_STARTED, iteration=iteration)

            # 检查 Token 限制
            current_tokens = self.token_counter.count_messages(messages)
            max_tokens = self.token_counter.max_tokens

            if current_tokens > max_tokens * 0.95:
                self.events.emit(AgentEvent.TOKEN_LIMIT_WARNING,
                               current=current_tokens, max=max_tokens)
                suggestion = self._create_token_limit_suggestion(current_tokens, max_tokens)
                self.conversation_history.append({'role': 'system', 'content': suggestion})
                messages = self.message_pipeline.process(list(self.conversation_history))
                continue

            # 获取工具 schemas
            tools = self.tool_executor.get_tool_schemas()

            # 调用 LLM
            try:
                self.events.emit(AgentEvent.LLM_REQUEST,
                               message_count=len(messages), tool_count=len(tools))

                response = self.client.chat_with_tools(
                    messages, tools, stream=stream, on_chunk=on_chunk
                )

                self.events.emit(AgentEvent.LLM_RESPONSE, response=response)

            except Exception as e:
                error_msg = f"LLM call failed: {e}"
                self.events.emit(AgentEvent.LLM_ERROR, error=str(e))
                self.conversation_history.append({'role': 'assistant', 'content': error_msg})
                return error_msg

            # 解析响应
            assistant_message = response.get('message', {})
            content = assistant_message.get('content', '')
            tool_calls = self.client.parse_tool_calls(response)

            # 无工具调用
            if not tool_calls:
                result = self._handle_no_tool_calls(content, iteration)
                if result is not None:
                    self.events.emit(AgentEvent.LOOP_ENDED, response=result)
                    return result
                messages = self.message_pipeline.process(list(self.conversation_history))
                continue

            # 有工具调用
            self.conversation_history.append({
                'role': 'assistant',
                'content': content,
                'tool_calls': tool_calls
            })

            # 显示助手思考（非流式模式）
            self._emit_assistant_thinking(content)

            # 使用命令模式和责任链执行工具
            for tool_call in tool_calls:
                command = CommandFactory.from_tool_call(tool_call)

                # 创建执行上下文
                ctx = ExecutionContext(
                    tool_name=command.tool_name,
                    arguments=command.arguments,
                    tool_call_id=command.tool_call_id,
                    tool_instance=self.tool_executor.registry.get(command.tool_name)
                )

                # 通过责任链执行
                self.events.emit(AgentEvent.TOOL_EXECUTING,
                               tool_name=command.tool_name, arguments=command.arguments)

                ctx = self.execution_chain.execute(ctx)

                # 记录命令
                command.result = ctx.result
                command.executed = True
                command.success = ctx.error is None
                command.error = ctx.error
                self.command_history.add(command)

                self.events.emit(AgentEvent.TOOL_EXECUTED,
                               tool_name=command.tool_name, result=ctx.result)

                # 跟踪活动文件
                if self.tool_executor.is_file_operation(command.tool_name):
                    file_path = command.arguments.get('path', '')
                    if file_path and file_path not in self.active_files:
                        self.active_files.append(file_path)

                # 添加工具结果到历史
                tool_message = {
                    'role': 'tool',
                    'content': self._format_tool_result(ctx.result),
                    'tool_call_id': command.tool_call_id
                }
                self.conversation_history.append(tool_message)

                # 如果被拒绝，中断当前工具调用循环
                if ctx.result and isinstance(ctx.result, dict) and ctx.result.get('denied_by_user'):
                    break

            # 更新消息
            messages = self.message_pipeline.process(list(self.conversation_history))

            # 检查是否需要压缩
            if self.token_counter.should_compress(time.time()):
                self._compress_context()

            self.events.emit(AgentEvent.ITERATION_ENDED, iteration=iteration)

        # 达到最大迭代
        final_msg = f"Reached maximum iterations ({self.max_iterations}). Task may be incomplete."
        self.conversation_history.append({'role': 'assistant', 'content': final_msg})
        self.events.emit(AgentEvent.LOOP_ENDED, response=final_msg, max_iterations=True)
        return final_msg

    def _handle_no_tool_calls(self, content: str, iteration: int) -> Optional[str]:
        """处理无工具调用的情况"""
        from backend.utils.feature import is_feature_enabled

        # 空响应重试：工具执行后模型返回空内容时自动重试（通过开关控制）
        if not content and iteration < self.max_iterations - 1:
            retry_enabled = is_feature_enabled("agent_behavior.retry_on_empty_after_tool")
            if retry_enabled:
                last_msg = self.conversation_history[-1] if self.conversation_history else None
                if last_msg and last_msg.get('role') == 'tool':
                    self.events.emit(
                        AgentEvent.NO_TOOL_CALLS, content=content, auto_continue=True
                    )
                    if self.tool_output_callback:
                        self.tool_output_callback(
                            '__no_tool_calls__',
                            '⚠️ 模型在工具执行后返回空内容，正在重试...',
                            {}
                        )
                    return None  # 继续循环

        # 检查是否启用自动 continue 功能
        auto_continue_enabled = is_feature_enabled("agent_behavior.auto_continue_on_incomplete")

        if auto_continue_enabled:
            continue_keywords = [
                "I'll", "I will", "Let me", "Now I", "Next I", "let's", "Let's",
                "I need to", "I should", "I'm going to", "need to check",
                "First", "Then", "After", "Before", "Step", "start by",
                "需要", "现在", "接下来", "让我", "我来", "查看", "检查",
                "首先", "然后", "接着", "第一", "第二", "步骤"
            ]
            # 检查是否以冒号结尾（可能是列表开头）或任务未完成的迹象
            ends_with_list_intro = content.rstrip().endswith(':') if content else False
            seems_incomplete = any(kw in content for kw in continue_keywords) if content else False
            seems_incomplete = seems_incomplete or ends_with_list_intro

            if seems_incomplete and iteration < self.max_iterations - 1:
                # 通知用户模型没有使用工具，正在自动继续
                self.events.emit(AgentEvent.NO_TOOL_CALLS, content=content, auto_continue=True)
                if self.tool_output_callback:
                    self.tool_output_callback(
                        '__no_tool_calls__',
                        '⚠️ 模型未使用工具，自动提示继续...',
                        {}
                    )
                self.conversation_history.append({'role': 'assistant', 'content': content})
                self.conversation_history.append({
                    'role': 'user',
                    'content': 'Continue. Use tools to complete the task.'
                })
                return None  # 继续循环

        # 通知用户模型没有使用工具
        self.events.emit(AgentEvent.NO_TOOL_CALLS, content=content, auto_continue=False)
        if self.tool_output_callback and not content:
            self.tool_output_callback(
                '__no_tool_calls__',
                '⚠️ 模型未使用工具且无响应内容',
                {}
            )

        # 任务完成
        self.conversation_history.append({'role': 'assistant', 'content': content or ''})
        return content or ''

    def _emit_assistant_thinking(self, content: str):
        """发送助手思考事件"""
        if self.tool_output_callback and not self._stream_mode:
            try:
                if content and content.strip():
                    self.tool_output_callback('__assistant_thinking__', content, {})
                    self.events.emit(AgentEvent.ASSISTANT_THINKING, content=content)
                else:
                    msg = '💭 AI正在指挥做事，没功夫说话...'
                    self.tool_output_callback('__assistant_thinking__', msg, {})
            except Exception:
                pass

    def _create_token_limit_suggestion(self, current_tokens: int, max_tokens: int) -> str:
        """创建 token 超限建议消息"""
        usage_pct = (current_tokens / max_tokens) * 100
        return f"""⚠️ Context Token Limit Alert

Current context size: {current_tokens:,} tokens ({usage_pct:.1f}% of {max_tokens:,} limit)

**Recommended Actions:**
1. Use `line_range` parameter for file reading
2. Use `grep_search` instead of reading entire files
3. Limit directory listing depth
4. Break down the task into smaller sections
"""

    def _format_tool_result(self, result: Any) -> str:
        """Format tool result for LLM"""
        import json
        if isinstance(result, dict):
            if 'content' in result:
                result = result.copy()
                result['content'] = self.token_counter.truncate_tool_result(result['content'])
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    def _compress_context(self):
        """Compress conversation history"""
        must_keep = f"Active files: {', '.join(self.active_files)}\nProject: {self.project_root}"
        compressible = f"{len(self.conversation_history)} messages"
        target_tokens = self.token_counter.get_compression_target()

        try:
            compression_result = self.client.compress_context(
                self.conversation_history, target_tokens, must_keep, compressible
            )

            keep_indices = compression_result.get('keep_message_indices', [])
            compressed_summary = compression_result.get('compressed_summary', '')

            new_history = []
            if compressed_summary:
                new_history.append({
                    'role': 'system',
                    'content': f"[Compressed History]\n{compressed_summary}"
                })

            for idx in keep_indices:
                if 0 <= idx < len(self.conversation_history):
                    new_history.append(self.conversation_history[idx])

            self.conversation_history = new_history
            self.token_counter.update_usage(
                'compressed_history',
                self.token_counter.count_messages(new_history)
            )
            self.token_counter.last_compression_time = time.time()

            self.events.emit(AgentEvent.CONTEXT_COMPRESSED,
                           original_count=len(self.conversation_history),
                           new_count=len(new_history))

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
            'command_history': self.command_history.summary(),
            'last_commands': [cmd.to_dict() for cmd in self.command_history.get_last(5)],
            'compressed_context': self._get_context_summary(),
            'next_steps': self._suggest_next_steps()
        }

        with open(session_file, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def _get_context_summary(self) -> str:
        """Get summary of current context"""
        summary = self.command_history.summary()
        return f"Tools: {summary['executed']}, Success: {summary['successful']}, Failed: {summary['failed']}"

    def _suggest_next_steps(self) -> List[str]:
        """Suggest next steps based on current state"""
        suggestions = []

        failed = self.command_history.get_failed()
        if failed:
            suggestions.append("Review failed tool calls")
            suggestions.append("Check error messages and adjust parameters")

        if self.active_files:
            suggestions.append(f"Review changes in: {', '.join(self.active_files[:3])}")

        if not suggestions:
            suggestions.append("Verify the changes and test manually")

        return suggestions
