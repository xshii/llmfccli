# -*- coding: utf-8 -*-
"""
TodoManager - 单例模式管理任务列表状态
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Literal
from enum import Enum
import threading


class TodoStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """单个任务项"""
    content: str                    # 任务描述（祈使语气）
    status: TodoStatus              # 任务状态
    active_form: str = ""           # 进行时态描述（用于显示）

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'content': self.content,
            'status': self.status.value,
            'activeForm': self.active_form or self.content
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TodoItem':
        """从字典创建"""
        return cls(
            content=data.get('content', ''),
            status=TodoStatus(data.get('status', 'pending')),
            active_form=data.get('activeForm', data.get('content', ''))
        )


class TodoManager:
    """
    任务管理器 - 单例模式

    核心规则：
    1. 同一时间只能有一个 in_progress 任务
    2. 完成后立即标记 completed（不批量标记）
    3. 任务列表对用户可见，提供实时进度
    """

    _instance: Optional['TodoManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._todos: List[TodoItem] = []
        self._on_change_callbacks: List[Callable[['TodoManager'], None]] = []
        self._initialized = True

    @property
    def todos(self) -> List[TodoItem]:
        """获取所有任务（只读副本）"""
        return self._todos.copy()

    @property
    def current_task(self) -> Optional[TodoItem]:
        """获取当前进行中的任务"""
        for todo in self._todos:
            if todo.status == TodoStatus.IN_PROGRESS:
                return todo
        return None

    @property
    def pending_count(self) -> int:
        """待处理任务数"""
        return sum(1 for t in self._todos if t.status == TodoStatus.PENDING)

    @property
    def completed_count(self) -> int:
        """已完成任务数"""
        return sum(1 for t in self._todos if t.status == TodoStatus.COMPLETED)

    @property
    def total_count(self) -> int:
        """总任务数"""
        return len(self._todos)

    @property
    def progress_percent(self) -> int:
        """完成进度百分比"""
        if self.total_count == 0:
            return 0
        return int(self.completed_count / self.total_count * 100)

    def set_todos(self, todos: List[dict]) -> dict:
        """
        设置完整的任务列表（替换现有列表）

        Args:
            todos: 任务列表，每个任务包含 content, status, activeForm

        Returns:
            操作结果
        """
        # 验证：同一时间只能有一个 in_progress
        in_progress_count = sum(1 for t in todos if t.get('status') == 'in_progress')
        if in_progress_count > 1:
            return {
                'success': False,
                'error': '同一时间只能有一个 in_progress 任务'
            }

        # 转换为 TodoItem
        self._todos = [TodoItem.from_dict(t) for t in todos]

        # 触发回调
        self._notify_change()

        return {
            'success': True,
            'total': self.total_count,
            'completed': self.completed_count,
            'pending': self.pending_count,
            'in_progress': 1 if in_progress_count else 0,
            'progress': self.progress_percent
        }

    def add_todo(self, content: str, active_form: str = "",
                 status: TodoStatus = TodoStatus.PENDING) -> dict:
        """添加单个任务"""
        # 如果要添加 in_progress，先检查是否已有
        if status == TodoStatus.IN_PROGRESS:
            if self.current_task:
                return {
                    'success': False,
                    'error': f'已有进行中的任务: {self.current_task.content}'
                }

        todo = TodoItem(
            content=content,
            status=status,
            active_form=active_form or content
        )
        self._todos.append(todo)
        self._notify_change()

        return {
            'success': True,
            'index': len(self._todos) - 1,
            'total': self.total_count
        }

    def update_status(self, index: int, status: TodoStatus) -> dict:
        """更新任务状态"""
        if index < 0 or index >= len(self._todos):
            return {
                'success': False,
                'error': f'无效的任务索引: {index}'
            }

        # 如果要设为 in_progress，先检查
        if status == TodoStatus.IN_PROGRESS:
            current = self.current_task
            if current and self._todos.index(current) != index:
                return {
                    'success': False,
                    'error': f'已有进行中的任务: {current.content}'
                }

        self._todos[index].status = status
        self._notify_change()

        return {
            'success': True,
            'progress': self.progress_percent
        }

    def clear(self):
        """清空所有任务"""
        self._todos.clear()
        self._notify_change()

    def on_change(self, callback: Callable[['TodoManager'], None]):
        """注册变更回调"""
        self._on_change_callbacks.append(callback)

    def _notify_change(self):
        """通知所有监听者"""
        for callback in self._on_change_callbacks:
            try:
                callback(self)
            except Exception:
                pass  # 静默忽略回调错误

    def get_display_text(self, max_width: int = 60) -> str:
        """
        获取用于显示的文本

        Returns:
            格式化的任务列表文本
        """
        if not self._todos:
            return ""

        lines = []

        # 进度条
        progress = self.progress_percent
        bar_width = 20
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        lines.append(f"[{bar}] {progress}% ({self.completed_count}/{self.total_count})")

        # 当前任务
        current = self.current_task
        if current:
            active_text = current.active_form or current.content
            if len(active_text) > max_width - 4:
                active_text = active_text[:max_width - 7] + "..."
            lines.append(f"▸ {active_text}")

        return "\n".join(lines)

    def get_full_display(self) -> List[str]:
        """获取完整的任务列表显示"""
        lines = []

        for i, todo in enumerate(self._todos):
            if todo.status == TodoStatus.COMPLETED:
                icon = "✓"
                style = "dim"
            elif todo.status == TodoStatus.IN_PROGRESS:
                icon = "▸"
                style = "bold"
            else:
                icon = "○"
                style = ""

            lines.append({
                'icon': icon,
                'text': todo.content,
                'style': style,
                'status': todo.status.value
            })

        return lines


# 全局单例获取函数
def get_todo_manager() -> TodoManager:
    """获取 TodoManager 单例"""
    return TodoManager()
