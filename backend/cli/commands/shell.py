# -*- coding: utf-8 -*-
"""
Shell 命令 - 本地 shell 命令执行
"""

from typing import List
from rich.console import Console

from .base import Command
from ...utils.shell_session import PersistentShellSession


class CmdCommand(Command):
    """执行本地 shell 命令（持久化会话）"""

    def __init__(self, console: Console, shell_session: PersistentShellSession):
        super().__init__(console)
        self.shell_session = shell_session

    @property
    def name(self) -> str:
        return "cmd"

    @property
    def description(self) -> str:
        return "执行本地 shell 命令（持久化会话，cd 等命令会保留状态）"

    @property
    def category(self) -> str:
        return "shell"

    @property
    def usage(self) -> str:
        return "/cmd <command>"

    def execute(self, args: List[str]) -> bool:
        if len(args) == 0:
            self.console.print("[yellow]用法: /cmd <command>[/yellow]")
            self.console.print("示例: /cmd ls -la")
            self.console.print("[dim]提示: 持久化会话，cd 等命令会保留状态[/dim]")
            return True

        cmd_to_run = ' '.join(args)
        self.console.print(f"[cyan]执行命令:[/cyan] {cmd_to_run}")

        def on_stdout(line: str):
            self.console.print(line)

        def on_stderr(line: str):
            self.console.print(f"[red]{line}[/red]")

        success, error = self.shell_session.execute_streaming(
            cmd_to_run,
            on_stdout=on_stdout,
            on_stderr=on_stderr
        )

        if error:
            self.console.print(f"[red]{error}[/red]")

        if success:
            self.console.print(f"[green]✓ 命令执行成功[/green]")
        else:
            self.console.print(f"[red]✗ 命令执行失败[/red]")

        return True


class CmdClearCommand(Command):
    """重置 shell 会话"""

    def __init__(self, console: Console, shell_session: PersistentShellSession, project_root: str):
        super().__init__(console)
        self.shell_session = shell_session
        self.project_root = project_root

    @property
    def name(self) -> str:
        return "cmdclear"

    @property
    def description(self) -> str:
        return "重置 shell 会话到初始状态"

    @property
    def category(self) -> str:
        return "shell"

    def execute(self, args: List[str]) -> bool:
        self.console.print("[yellow]重置 shell 会话...[/yellow]")
        self.shell_session.reset()
        self.console.print(f"[green]✓ Shell 会话已重置到初始目录: {self.project_root}[/green]")
        return True
