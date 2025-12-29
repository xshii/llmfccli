# -*- coding: utf-8 -*-
"""
TodoWrite Tool - 任务列表管理工具

用于创建和管理结构化任务列表，向用户展示进度。
"""

from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool, ToolResult
from backend.todo import get_todo_manager


class TodoItemParam(BaseModel):
    """单个任务参数"""
    content: str = Field(description="Task description in imperative form (e.g., 'Fix the bug')")
    status: Literal["pending", "in_progress", "completed"] = Field(
        description="Task status: pending (not started), in_progress (currently working), completed (finished)"
    )
    activeForm: str = Field(
        description="Present continuous form for display (e.g., 'Fixing the bug')"
    )


class TodoWriteParams(BaseModel):
    """TodoWrite 工具参数"""
    todos: List[TodoItemParam] = Field(
        description="The complete todo list. Each item has content, status, and activeForm."
    )


class TodoWriteTool(BaseTool):
    """
    任务列表管理工具

    使用场景：
    1. 复杂多步骤任务（3个以上步骤）
    2. 需要仔细规划的任务
    3. 用户提供多个任务时
    4. 开始工作前的计划阶段

    核心规则：
    - 同一时间只能有一个 in_progress 任务
    - 完成后立即标记 completed（不批量标记）
    - 任务描述使用祈使语气，activeForm 使用进行时态
    """

    @property
    def name(self) -> str:
        return "todo_write"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                "Create and manage a structured task list to track progress. "
                "Use for: (1) Multi-step tasks (3+ steps); (2) Complex implementations; "
                "(3) Multiple user requests; (4) Planning before work. "
                "Rules: Only ONE task can be in_progress at a time. "
                "Mark tasks completed IMMEDIATELY after finishing (don't batch). "
                "Use imperative form for content, present continuous for activeForm."
            ),
            'zh': (
                "创建和管理结构化任务列表以跟踪进度。"
                "适用于：(1) 多步骤任务（3步以上）；(2) 复杂实现；"
                "(3) 多个用户请求；(4) 工作前规划。"
                "规则：同一时间只能有一个 in_progress 任务。"
                "完成后立即标记 completed（不批量标记）。"
                "content 使用祈使语气，activeForm 使用进行时态。"
            )
        }

    @property
    def category(self) -> str:
        return "agent"

    @property
    def priority(self) -> int:
        # 高优先级，鼓励 LLM 使用
        return 85

    @property
    def parameters_model(self):
        return TodoWriteParams

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'todos': {
                'en': (
                    "Complete todo list. Each item must have: "
                    "content (imperative, e.g., 'Run tests'), "
                    "status ('pending'|'in_progress'|'completed'), "
                    "activeForm (present continuous, e.g., 'Running tests'). "
                    "Only ONE item can be in_progress."
                ),
                'zh': (
                    "完整的任务列表。每个任务必须包含："
                    "content（祈使语气，如'运行测试'）、"
                    "status（'pending'|'in_progress'|'completed'）、"
                    "activeForm（进行时态，如'正在运行测试'）。"
                    "只能有一个 in_progress。"
                )
            }
        }

    def execute(self, todos: List[Dict[str, Any]]) -> ToolResult:
        """
        执行任务列表更新

        Args:
            todos: 任务列表
        """
        manager = get_todo_manager()

        # 转换参数格式
        todo_list = []
        for item in todos:
            if isinstance(item, dict):
                todo_list.append(item)
            else:
                # Pydantic model
                todo_list.append({
                    'content': item.content,
                    'status': item.status,
                    'activeForm': item.activeForm
                })

        result = manager.set_todos(todo_list)

        if result['success']:
            current = manager.current_task
            current_text = f", 当前: {current.content}" if current else ""
            return ToolResult.success(
                f"任务列表已更新: {result['completed']}/{result['total']} 完成{current_text}"
            )
        else:
            return ToolResult.fail(result.get('error', '更新失败'))
