# -*- coding: utf-8 -*-
"""
Model 命令 - Ollama 模型管理
"""

from typing import List
from rich.console import Console

from .base import Command


class ModelCommand(Command):
    """Ollama 模型管理命令"""

    def __init__(self, console: Console, remote_commands):
        """
        初始化模型命令

        Args:
            console: Rich Console 实例
            remote_commands: RemoteCommands 实例
        """
        super().__init__(console)
        self.remote_commands = remote_commands

    @property
    def name(self) -> str:
        return "model"

    @property
    def description(self) -> str:
        return "管理 Ollama 模型"

    def execute(self, args: List[str]) -> bool:
        """
        处理 /model 子命令

        可用子命令:
        - /model list - 列出所有模型
        - /model create - 创建 claude-qwen 模型
        - /model show <name> - 显示模型详情
        - /model delete <name> - 删除模型
        - /model pull <name> - 拉取模型
        - /model health - 检查服务器健康状态
        """
        if len(args) < 1:
            self.console.print("[yellow]用法: /model <subcommand> [args][/yellow]")
            self.console.print("\n可用子命令:")
            self.console.print("  • list - 列出所有模型")
            self.console.print("  • create - 创建 claude-qwen 模型")
            self.console.print("  • show <name> - 显示模型详情")
            self.console.print("  • delete <name> - 删除模型")
            self.console.print("  • pull <name> - 拉取模型")
            self.console.print("  • health - 检查服务器健康状态")
            return True

        subcmd = args[0].lower()

        if subcmd == 'list':
            self.remote_commands.list_models()

        elif subcmd == 'create':
            self.remote_commands.create_model()

        elif subcmd == 'show':
            if len(args) < 2:
                self.console.print("[red]错误: 需要指定模型名称[/red]")
                self.console.print("用法: /model show <model_name>")
                return True
            self.remote_commands.show_model(args[1])

        elif subcmd == 'delete':
            if len(args) < 2:
                self.console.print("[red]错误: 需要指定模型名称[/red]")
                self.console.print("用法: /model delete <model_name>")
                return True
            confirm = '-y' in args or '--yes' in args
            self.remote_commands.delete_model(args[1], confirm=confirm)

        elif subcmd == 'pull':
            if len(args) < 2:
                self.console.print("[red]错误: 需要指定模型名称[/red]")
                self.console.print("用法: /model pull <model_name>")
                return True
            self.remote_commands.pull_model(args[1])

        elif subcmd == 'health':
            self.remote_commands.check_health()

        else:
            self.console.print(f"[yellow]未知子命令: {subcmd}[/yellow]")
            self.console.print("输入 /model 查看可用子命令")

        return True
