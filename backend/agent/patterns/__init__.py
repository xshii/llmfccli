# -*- coding: utf-8 -*-
"""
Agent 设计模式

包含以下模式实现：
- Pipeline: 消息处理管道
- Chain: 责任链模式（工具执行）
- Command: 命令模式（工具调用）
- Observer: 观察者模式（事件通知）
"""

from .pipeline import (
    MessageProcessor,
    MessagePipeline,
    CleanSystemReminders,
    TruncateLongContent,
)

from .chain import (
    ExecutionContext,
    ExecutionStatus,
    ExecutionHandler,
    PreviewHandler,
    ConfirmationHandler,
    ExecutionHandlerImpl,
    CallbackHandler,
    CleanupHandler,
    ToolExecutionChain,
)

from .command import (
    ToolCommand,
    CommandHistory,
    CommandFactory,
)

from .observer import (
    AgentEvent,
    EventData,
    EventEmitter,
    AgentEventBus,
    get_event_bus,
)

__all__ = [
    # Pipeline
    'MessageProcessor',
    'MessagePipeline',
    'CleanSystemReminders',
    'TruncateLongContent',
    # Chain
    'ExecutionContext',
    'ExecutionStatus',
    'ExecutionHandler',
    'PreviewHandler',
    'ConfirmationHandler',
    'ExecutionHandlerImpl',
    'CallbackHandler',
    'CleanupHandler',
    'ToolExecutionChain',
    # Command
    'ToolCommand',
    'CommandHistory',
    'CommandFactory',
    # Observer
    'AgentEvent',
    'EventData',
    'EventEmitter',
    'AgentEventBus',
    'get_event_bus',
]
