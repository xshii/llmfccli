# -*- coding: utf-8 -*-
"""
责任链模式 (Chain of Responsibility) - 工具执行
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ExecutionStatus(Enum):
    """执行状态"""
    CONTINUE = "continue"  # 继续下一个处理器
    STOP = "stop"          # 停止链，返回结果
    SKIP = "skip"          # 跳过当前工具，继续下一个


@dataclass
class ExecutionContext:
    """执行上下文"""
    tool_name: str
    arguments: Dict[str, Any]
    tool_call_id: str
    tool_instance: Any = None
    result: Any = None
    status: ExecutionStatus = ExecutionStatus.CONTINUE
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def stop_with_result(self, result: Any):
        """停止链并返回结果"""
        self.result = result
        self.status = ExecutionStatus.STOP

    def stop_with_error(self, error: str):
        """停止链并返回错误"""
        self.error = error
        self.result = {'success': False, 'error': error}
        self.status = ExecutionStatus.STOP

    def skip(self):
        """跳过当前工具"""
        self.status = ExecutionStatus.SKIP


class ExecutionHandler(ABC):
    """执行处理器基类"""

    def __init__(self):
        self.next_handler: Optional['ExecutionHandler'] = None

    def set_next(self, handler: 'ExecutionHandler') -> 'ExecutionHandler':
        """设置下一个处理器"""
        self.next_handler = handler
        return handler

    @abstractmethod
    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        """处理执行上下文"""
        pass

    def _next(self, ctx: ExecutionContext) -> ExecutionContext:
        """调用下一个处理器"""
        if ctx.status != ExecutionStatus.CONTINUE:
            return ctx
        if self.next_handler:
            return self.next_handler.handle(ctx)
        return ctx


class PreviewHandler(ExecutionHandler):
    """预览处理器 - 显示 diff 预览"""

    def __init__(self, should_preview: Callable[[str], bool] = None):
        super().__init__()
        self.should_preview = should_preview or (lambda _: True)

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        if not self.should_preview(ctx.tool_name):
            return self._next(ctx)

        tool = ctx.tool_instance
        if tool and hasattr(tool, 'get_diff_preview'):
            try:
                result = tool.get_diff_preview(**ctx.arguments, interactive=True)
                if result and result.get('shown'):
                    ctx.metadata['preview_shown'] = True
                    if result.get('accepted') is not None:
                        # Interactive mode: user made a decision
                        ctx.metadata['diff_accepted'] = result['accepted']
                        if not result['accepted']:
                            ctx.stop_with_error(
                                'User rejected changes in diff preview. '
                                'Adjust parameters or ask for clarification.'
                            )
                            ctx.result['denied_by_user'] = True
                            return ctx
            except Exception:
                # 预览失败，继续执行
                pass

        return self._next(ctx)


class ConfirmationHandler(ExecutionHandler):
    """确认处理器 - 处理用户确认"""

    def __init__(self, confirmation_manager, on_deny: Callable[[ExecutionContext, str], None] = None):
        super().__init__()
        self.confirmation = confirmation_manager
        self.on_deny = on_deny

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        # Skip CLI confirmation if user already accepted via diff preview
        if ctx.metadata.get('diff_accepted') is True:
            return self._next(ctx)

        if not self.confirmation.needs_confirmation(ctx.tool_name, ctx.arguments):
            return self._next(ctx)

        confirm_result = self.confirmation.confirm(
            ctx.tool_name, ctx.arguments
        )

        # 导入在这里避免循环依赖
        from ..tools import ConfirmAction

        if confirm_result.action == ConfirmAction.DENY:
            reason = confirm_result.reason or 'User declined'
            error_msg = f'User declined: {reason}. Adjust parameters or ask for clarification.'

            if self.on_deny:
                self.on_deny(ctx, reason)

            ctx.stop_with_error(error_msg)
            ctx.result['denied_by_user'] = True
            return ctx

        return self._next(ctx)


class ExecutionHandlerImpl(ExecutionHandler):
    """执行处理器 - 实际执行工具"""

    def __init__(self, executor):
        super().__init__()
        self.executor = executor

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        try:
            result = self.executor.execute_tool(ctx.tool_name, ctx.arguments)
            ctx.result = result
        except Exception as e:
            ctx.stop_with_error(str(e))

        return self._next(ctx)


class CallbackHandler(ExecutionHandler):
    """回调处理器 - 调用输出回调"""

    def __init__(self, callback: Callable[[str, Any, Dict], None] = None):
        super().__init__()
        self.callback = callback

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        if self.callback and ctx.result is not None:
            try:
                self.callback(ctx.tool_name, ctx.result, ctx.arguments)
            except Exception:
                # 回调错误不影响执行
                pass

        return self._next(ctx)


class CleanupHandler(ExecutionHandler):
    """清理处理器 - 清理资源（如关闭 diff 预览）"""

    def __init__(self, cleanup_func: Callable[[ExecutionContext], None] = None):
        super().__init__()
        self.cleanup_func = cleanup_func

    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        if self.cleanup_func:
            try:
                self.cleanup_func(ctx)
            except Exception:
                pass

        return self._next(ctx)


class ToolExecutionChain:
    """工具执行链"""

    def __init__(self):
        self.head: Optional[ExecutionHandler] = None
        self.tail: Optional[ExecutionHandler] = None

    def add(self, handler: ExecutionHandler) -> 'ToolExecutionChain':
        """添加处理器到链"""
        if self.head is None:
            self.head = handler
            self.tail = handler
        else:
            self.tail.set_next(handler)
            self.tail = handler
        return self

    def execute(self, ctx: ExecutionContext) -> ExecutionContext:
        """执行链"""
        if self.head:
            return self.head.handle(ctx)
        return ctx

    @classmethod
    def create(
        cls,
        executor,
        confirmation_manager=None,
        output_callback=None,
        cleanup_func=None
    ) -> 'ToolExecutionChain':
        """创建标准执行链"""
        chain = cls()

        # 1. 预览
        chain.add(PreviewHandler())

        # 2. 确认
        if confirmation_manager:
            chain.add(ConfirmationHandler(confirmation_manager))

        # 3. 执行
        chain.add(ExecutionHandlerImpl(executor))

        # 4. 回调
        if output_callback:
            chain.add(CallbackHandler(output_callback))

        # 5. 清理
        if cleanup_func:
            chain.add(CleanupHandler(cleanup_func))

        return chain
