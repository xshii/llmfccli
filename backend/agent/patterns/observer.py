# -*- coding: utf-8 -*-
"""
观察者模式 (Observer Pattern) - 事件通知
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AgentEvent(Enum):
    """Agent 事件类型"""
    # 生命周期事件
    LOOP_STARTED = "loop_started"
    LOOP_ENDED = "loop_ended"
    ITERATION_STARTED = "iteration_started"
    ITERATION_ENDED = "iteration_ended"

    # LLM 事件
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"
    LLM_CHUNK = "llm_chunk"

    # 工具事件
    TOOL_CALL_RECEIVED = "tool_call_received"
    TOOL_PREVIEW_SHOWN = "tool_preview_shown"
    TOOL_CONFIRMATION_REQUIRED = "tool_confirmation_required"
    TOOL_CONFIRMED = "tool_confirmed"
    TOOL_DENIED = "tool_denied"
    TOOL_EXECUTING = "tool_executing"
    TOOL_EXECUTED = "tool_executed"
    TOOL_ERROR = "tool_error"
    NO_TOOL_CALLS = "no_tool_calls"  # 模型未使用工具

    # 上下文事件
    TOKEN_LIMIT_WARNING = "token_limit_warning"
    CONTEXT_COMPRESSED = "context_compressed"

    # 助手事件
    ASSISTANT_THINKING = "assistant_thinking"
    ASSISTANT_RESPONSE = "assistant_response"


@dataclass
class EventData:
    """事件数据"""
    event: AgentEvent
    timestamp: datetime
    data: Dict[str, Any]

    @classmethod
    def create(cls, event: AgentEvent, **kwargs) -> 'EventData':
        return cls(event=event, timestamp=datetime.now(), data=kwargs)


class EventEmitter:
    """事件发射器"""

    def __init__(self):
        self._listeners: Dict[AgentEvent, List[Callable]] = defaultdict(list)
        self._once_listeners: Dict[AgentEvent, List[Callable]] = defaultdict(list)
        self._all_listeners: List[Callable] = []

    def on(self, event: AgentEvent, callback: Callable) -> 'EventEmitter':
        """注册事件监听器"""
        self._listeners[event].append(callback)
        return self

    def once(self, event: AgentEvent, callback: Callable) -> 'EventEmitter':
        """注册一次性事件监听器"""
        self._once_listeners[event].append(callback)
        return self

    def on_all(self, callback: Callable) -> 'EventEmitter':
        """注册监听所有事件"""
        self._all_listeners.append(callback)
        return self

    def off(self, event: AgentEvent, callback: Callable) -> 'EventEmitter':
        """移除事件监听器"""
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)
        if callback in self._once_listeners[event]:
            self._once_listeners[event].remove(callback)
        return self

    def off_all(self, event: Optional[AgentEvent] = None) -> 'EventEmitter':
        """移除所有监听器"""
        if event:
            self._listeners[event].clear()
            self._once_listeners[event].clear()
        else:
            self._listeners.clear()
            self._once_listeners.clear()
            self._all_listeners.clear()
        return self

    def emit(self, event: AgentEvent, **kwargs) -> None:
        """发射事件"""
        event_data = EventData.create(event, **kwargs)

        # 调用所有事件监听器
        for callback in self._all_listeners:
            try:
                callback(event_data)
            except Exception:
                pass

        # 调用特定事件监听器
        for callback in self._listeners[event]:
            try:
                callback(event_data)
            except Exception:
                pass

        # 调用一次性监听器
        once_callbacks = self._once_listeners[event].copy()
        self._once_listeners[event].clear()
        for callback in once_callbacks:
            try:
                callback(event_data)
            except Exception:
                pass

    def listener_count(self, event: Optional[AgentEvent] = None) -> int:
        """获取监听器数量"""
        if event:
            return len(self._listeners[event]) + len(self._once_listeners[event])
        total = len(self._all_listeners)
        for listeners in self._listeners.values():
            total += len(listeners)
        for listeners in self._once_listeners.values():
            total += len(listeners)
        return total


class AgentEventBus(EventEmitter):
    """Agent 事件总线"""

    _instance: Optional['AgentEventBus'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    # 便捷方法
    def emit_tool_executed(self, tool_name: str, result: Any, arguments: Dict):
        """发射工具执行完成事件"""
        self.emit(
            AgentEvent.TOOL_EXECUTED,
            tool_name=tool_name,
            result=result,
            arguments=arguments
        )

    def emit_llm_response(self, content: str, tool_calls: List = None):
        """发射 LLM 响应事件"""
        self.emit(
            AgentEvent.LLM_RESPONSE,
            content=content,
            tool_calls=tool_calls or []
        )

    def emit_assistant_thinking(self, content: str):
        """发射助手思考事件"""
        self.emit(AgentEvent.ASSISTANT_THINKING, content=content)

    def emit_token_warning(self, current: int, max_tokens: int):
        """发射 Token 警告事件"""
        self.emit(
            AgentEvent.TOKEN_LIMIT_WARNING,
            current_tokens=current,
            max_tokens=max_tokens,
            usage_pct=current / max_tokens * 100
        )


def get_event_bus() -> AgentEventBus:
    """获取全局事件总线"""
    return AgentEventBus()
