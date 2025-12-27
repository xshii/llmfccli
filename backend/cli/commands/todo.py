# -*- coding: utf-8 -*-
"""
Todo Command - 查看和管理任务列表
"""

from typing import List
from rich.console import Console
from rich.table import Table

from .base import BaseCommand


class TodoCommand(BaseCommand):
    """查看和管理任务列表"""

    def __init__(self, console: Console, **dependencies):
        super().__init__(console, **dependencies)

    @property
    def name(self) -> str:
        return "todo"

    @property
    def description(self) -> str:
        return "查看当前任务列表"

    @property
    def category(self) -> str:
        return "session"

    @property
    def usage(self) -> str:
        return "/todo [list|clear]"

    def execute(self, args: List[str]) -> bool:
        """
        处理 /todo 命令

        子命令:
        - /todo 或 /todo list - 显示任务列表
        - /todo clear - 清空任务列表
        """
        from backend.todo import get_todo_manager

        manager = get_todo_manager()
        subcmd = args[0] if args else 'list'

        if subcmd == 'list':
            self._show_todo_list(manager)

        elif subcmd == 'clear':
            manager.clear()
            self.console.print("[green]✓ 任务列表已清空[/green]")

        else:
            # 默认显示列表
            self._show_todo_list(manager)

        return True

    def _show_todo_list(self, manager):
        """显示任务列表"""
        todos = manager.todos

        if not todos:
            self.console.print("[dim]暂无任务[/dim]")
            self.console.print("[dim]Agent 执行复杂任务时会自动创建任务列表[/dim]")
            return

        # 进度概览
        progress = manager.progress_percent
        bar_width = 30
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        self.console.print(f"\n[bold]任务进度[/bold]: [{bar}] {progress}%")
        self.console.print(
            f"[dim]完成: {manager.completed_count} | "
            f"进行中: {1 if manager.current_task else 0} | "
            f"待处理: {manager.pending_count}[/dim]\n"
        )

        # 任务列表
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("状态", width=6)
        table.add_column("任务", max_width=60)

        for i, todo in enumerate(todos, 1):
            if todo.status.value == 'completed':
                status = "[green]✓[/green]"
                style = "dim"
            elif todo.status.value == 'in_progress':
                status = "[cyan]▸[/cyan]"
                style = "bold"
            else:
                status = "[dim]○[/dim]"
                style = ""

            content = todo.content
            if style == "dim":
                content = f"[dim]{content}[/dim]"
            elif style == "bold":
                content = f"[bold]{content}[/bold]"

            table.add_row(str(i), status, content)

        self.console.print(table)
