# -*- coding: utf-8 -*-
"""
可复用的交互式 CLI 基类

提供通用的交互式命令行功能，可被不同模块继承使用。
"""

import cmd
import sys
from typing import Optional, Dict, Callable, Any
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown


class InteractiveShellBase(cmd.Cmd):
    """
    交互式 Shell 基类

    提供通用功能：
    - 命令解析和执行
    - 帮助系统
    - 自动补全
    - 历史记录
    - 错误处理
    - Rich 格式化输出

    子类需要实现：
    - intro: 欢迎信息
    - prompt: 命令提示符
    - do_* 方法：具体命令实现
    """

    # 子类需要设置这些属性
    intro = "Interactive Shell - Type 'help' or '?' to list commands."
    prompt = '> '

    def __init__(self):
        """初始化交互式 Shell"""
        super().__init__()
        self.console = Console()

        # 显示欢迎信息
        if self.intro:
            self.console.print(self.intro, style="cyan")

    # ==================== 通用方法 ====================

    def print_table(self, title: str, columns: list, rows: list):
        """
        打印表格

        Args:
            title: 表格标题
            columns: 列定义 [(名称, 样式), ...]
            rows: 行数据 [[值1, 值2, ...], ...]
        """
        table = Table(title=title)

        for col_name, col_style in columns:
            table.add_column(col_name, style=col_style)

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def print_panel(self, content: str, title: str = "", style: str = "cyan"):
        """
        打印面板

        Args:
            content: 面板内容
            title: 面板标题
            style: 边框样式
        """
        self.console.print(Panel(content, title=title, border_style=style))

    def print_markdown(self, text: str):
        """
        打印 Markdown 格式文本

        Args:
            text: Markdown 文本
        """
        self.console.print(Markdown(text))

    def print_success(self, message: str):
        """打印成功信息"""
        self.console.print(f"[green]✓ {message}[/green]")

    def print_error(self, message: str):
        """打印错误信息"""
        self.console.print(f"[red]✗ {message}[/red]")

    def print_warning(self, message: str):
        """打印警告信息"""
        self.console.print(f"[yellow]⚠ {message}[/yellow]")

    def print_info(self, message: str):
        """打印信息"""
        self.console.print(f"[cyan]ℹ {message}[/cyan]")

    # ==================== 命令实现 ====================

    def do_clear(self, arg):
        """
        清屏

        Usage: clear
        """
        self.console.clear()

    def do_exit(self, arg):
        """
        退出交互式 Shell

        Usage: exit
        """
        self.console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
        return True

    def do_quit(self, arg):
        """
        退出交互式 Shell

        Usage: quit
        """
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """处理 Ctrl+D"""
        self.console.print()
        return self.do_exit(arg)

    # ==================== 帮助系统 ====================

    def do_help(self, arg):
        """
        显示帮助信息

        Usage: help [command]
        """
        if arg:
            # 显示特定命令的帮助
            super().do_help(arg)
        else:
            # 显示通用帮助（子类可以覆盖）
            self._show_general_help()

    def _show_general_help(self):
        """显示通用帮助信息（子类可以覆盖）"""
        help_text = """
## Available Commands

Type 'help <command>' for detailed help on a command.

### Common Commands
- **help**        - Show this help message
- **clear**       - Clear the screen
- **exit/quit**   - Exit the shell

### Tips
- Use TAB for command completion
- Press Ctrl+D or type 'exit' to quit
- Type '?' for command list
"""
        self.print_markdown(help_text)

    # ==================== 错误处理 ====================

    def emptyline(self):
        """空行不重复上一条命令"""
        pass

    def default(self, line):
        """处理未知命令"""
        self.print_error(f"Unknown command: {line}")
        self.console.print("Type 'help' to see available commands")

    def cmdloop(self, intro=None):
        """
        覆盖 cmdloop 以提供更好的错误处理
        """
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            self.console.print("\n[cyan]Interrupted. Type 'exit' to quit.[/cyan]")
            self.cmdloop(intro="")

    # ==================== 工具方法 ====================

    def parse_args(self, arg: str) -> tuple:
        """
        解析命令参数

        Args:
            arg: 参数字符串

        Returns:
            (位置参数列表, 选项字典)
        """
        parts = arg.strip().split()

        positional = []
        options = {}

        i = 0
        while i < len(parts):
            part = parts[i]

            if part.startswith('-'):
                # 选项
                key = part.lstrip('-')

                # 检查是否有值
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    options[key] = parts[i + 1]
                    i += 2
                else:
                    options[key] = True
                    i += 1
            else:
                # 位置参数
                positional.append(part)
                i += 1

        return positional, options

    def confirm(self, prompt: str = "Continue?", default: bool = True) -> bool:
        """
        请求用户确认

        Args:
            prompt: 提示信息
            default: 默认值

        Returns:
            用户是否确认
        """
        suffix = " (Y/n): " if default else " (y/N): "

        try:
            response = input(prompt + suffix).strip().lower()

            if not response:
                return default

            return response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            self.console.print()
            return False


class CommandRegistry:
    """
    命令注册器

    用于注册和管理可用命令，支持动态添加命令。
    """

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.descriptions: Dict[str, str] = {}

    def register(self, name: str, func: Callable, description: str = ""):
        """
        注册命令

        Args:
            name: 命令名称
            func: 命令处理函数
            description: 命令描述
        """
        self.commands[name] = func
        self.descriptions[name] = description

    def get(self, name: str) -> Optional[Callable]:
        """获取命令处理函数"""
        return self.commands.get(name)

    def list_commands(self) -> Dict[str, str]:
        """列出所有命令及其描述"""
        return self.descriptions.copy()


def create_interactive_shell(
    prompt: str,
    intro: str,
    commands: Dict[str, Callable],
    shell_class: type = InteractiveShellBase
) -> InteractiveShellBase:
    """
    工厂函数：创建自定义交互式 Shell

    Args:
        prompt: 命令提示符
        intro: 欢迎信息
        commands: 命令字典 {命令名: 处理函数}
        shell_class: Shell 基类

    Returns:
        配置好的 Shell 实例

    Example:
        >>> def cmd_hello(shell, arg):
        ...     shell.console.print("Hello!")
        >>>
        >>> commands = {'hello': cmd_hello}
        >>> shell = create_interactive_shell(
        ...     prompt='(my-cli) ',
        ...     intro='Welcome!',
        ...     commands=commands
        ... )
        >>> shell.cmdloop()
    """

    # 动态创建 Shell 类
    class CustomShell(shell_class):
        pass

    # 设置属性
    CustomShell.prompt = prompt
    CustomShell.intro = intro

    # 动态添加命令方法
    for cmd_name, cmd_func in commands.items():
        method_name = f'do_{cmd_name}'

        # 创建包装函数
        def make_method(func):
            def method(self, arg):
                return func(self, arg)
            return method

        setattr(CustomShell, method_name, make_method(cmd_func))

    return CustomShell()


# ==================== 使用示例 ====================

if __name__ == '__main__':
    """
    示例：创建简单的交互式 Shell
    """

    class DemoShell(InteractiveShellBase):
        intro = """
╔═══════════════════════════════════════════════════════════╗
║                    Demo Interactive Shell                ║
╚═══════════════════════════════════════════════════════════╝

Type 'help' or '?' to list commands.
"""
        prompt = '(demo) '

        def do_hello(self, arg):
            """Say hello

            Usage: hello [name]
            """
            name = arg.strip() or "World"
            self.print_success(f"Hello, {name}!")

        def do_table(self, arg):
            """Show example table

            Usage: table
            """
            self.print_table(
                title="Example Table",
                columns=[("Name", "cyan"), ("Value", "green")],
                rows=[
                    ["Item 1", "100"],
                    ["Item 2", "200"],
                    ["Item 3", "300"]
                ]
            )

    # 运行 Demo Shell
    shell = DemoShell()
    shell.cmdloop()
