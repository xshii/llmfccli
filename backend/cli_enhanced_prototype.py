#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced CLI Prototype - 命令置顶 + 折叠输出

演示如何实现：
1. 命令始终置顶
2. Tool 输出可折叠
3. Ctrl+E 展开/折叠

运行: python backend/cli_enhanced_prototype.py
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich.console import Group


class EnhancedCLI:
    """增强版 CLI 原型"""

    def __init__(self):
        self.console = Console()
        self.command = ""
        self.tool_outputs = []  # [(tool_name, output, collapsed)]
        self.last_toggle_index = 0

    def add_tool_output(self, tool_name: str, output: str, args: dict = None, auto_collapse: bool = True):
        """添加工具输出

        Args:
            tool_name: 工具名称
            output: 输出内容
            args: 工具参数（可选）
            auto_collapse: 是否自动折叠长输出
        """
        # 超过 20 行自动折叠
        lines = output.count('\n')
        should_collapse = auto_collapse and lines > 20

        self.tool_outputs.append({
            'tool': tool_name,
            'output': output,
            'args': args or {},
            'collapsed': should_collapse,
            'lines': lines
        })

    def toggle_output(self, index: int):
        """切换指定输出的折叠状态"""
        if 0 <= index < len(self.tool_outputs):
            self.tool_outputs[index]['collapsed'] = not self.tool_outputs[index]['collapsed']

    def toggle_last_output(self):
        """切换最后一个输出的折叠状态"""
        if self.tool_outputs:
            self.toggle_output(len(self.tool_outputs) - 1)

    def render(self):
        """渲染整个界面"""
        elements = []

        # 1. 命令区（置顶）
        command_panel = Panel(
            Text(f"> {self.command}", style="cyan bold"),
            title="[bold blue]Current Command[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
        elements.append(command_panel)

        # 2. 工具输出区
        if not self.tool_outputs:
            elements.append(Text("\n[dim]等待执行...[/dim]\n"))

        for i, tool_data in enumerate(self.tool_outputs):
            tool_name = tool_data['tool']
            output = tool_data['output']
            args = tool_data['args']
            collapsed = tool_data['collapsed']
            lines = tool_data['lines']

            # 格式化参数显示
            args_str = ""
            if args:
                # 限制参数显示长度
                args_display = []
                for key, value in args.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    args_display.append(f"{key}={repr(value_str)}")
                args_str = f"({', '.join(args_display)})"

            if collapsed:
                # 折叠状态
                collapse_text = Text()
                collapse_text.append("▶ ", style="yellow")
                collapse_text.append(f"[{tool_name}]", style="cyan bold")
                if args_str:
                    collapse_text.append(args_str, style="cyan dim")
                collapse_text.append(f" ({lines} lines) ", style="dim")
                collapse_text.append("[Ctrl+E to expand]", style="dim italic")
                elements.append(collapse_text)
            else:
                # 展开状态
                # 限制显示长度
                display_output = output
                if len(output) > 2000:
                    display_output = output[:2000] + f"\n\n... ({len(output) - 2000} more chars)"

                # 标题包含参数
                title = f"[bold green]▼ {tool_name}[/bold green]"
                if args_str:
                    title = f"[bold green]▼ {tool_name}[/bold green][dim]{args_str}[/dim]"

                output_panel = Panel(
                    display_output,
                    title=title,
                    border_style="green",
                    padding=(0, 1)
                )
                elements.append(output_panel)

        # 3. 提示栏
        help_text = Text()
        help_text.append("\n")
        help_text.append("命令: ", style="bold yellow")
        help_text.append("/expand", style="cyan")
        help_text.append(" 展开 | ", style="dim")
        help_text.append("/collapse", style="cyan")
        help_text.append(" 折叠 | ", style="dim")
        help_text.append("/toggle", style="cyan")
        help_text.append(" 切换 | ", style="dim")
        help_text.append("/exit", style="cyan")
        help_text.append(" 退出", style="dim")
        elements.append(help_text)

        return Group(*elements)

    def run_demo(self):
        """运行演示"""
        self.console.print("[bold cyan]Enhanced CLI 原型演示[/bold cyan]\n")

        # 模拟执行流程
        self.command = "帮我编译项目并修复错误"

        with Live(self.render(), console=self.console, refresh_per_second=4) as live:
            time.sleep(1)

            # 模拟 Tool 1: bash_run (短输出)
            self.add_tool_output(
                "bash_run",
                "$ cmake --build build\n[ 10%] Building CXX object...\n[ 20%] Building CXX object...\n✓ Build complete",
                args={"command": "cmake --build build"},
                auto_collapse=False
            )
            live.update(self.render())
            time.sleep(2)

            # 模拟 Tool 2: bash_run (长输出，自动折叠)
            long_output = "\n".join([f"Line {i}: Some compilation output..." for i in range(50)])
            self.add_tool_output(
                "bash_run",
                long_output,
                args={"command": "make -j8", "cwd": "/home/user/project"},
                auto_collapse=True
            )
            live.update(self.render())
            time.sleep(2)

            # 模拟 Tool 3: edit_file
            self.add_tool_output(
                "edit_file",
                "File: src/main.cpp\nEdited lines: 45-67\n\nChanges:\n  - Added error handling\n  - Fixed memory leak",
                args={"file_path": "src/main.cpp", "old_str": "return nullptr;", "new_str": "throw std::runtime_error(\"...\");"},
                auto_collapse=False
            )
            live.update(self.render())
            time.sleep(2)

            # 演示交互
            self.console.print("\n[yellow]现在可以输入斜杠命令:[/yellow]")
            self.console.print("  • '/expand' - 展开最后一个折叠的输出")
            self.console.print("  • '/collapse' - 折叠最后一个展开的输出")
            self.console.print("  • '/toggle' - 切换最后一个输出状态")
            self.console.print("  • '/exit' - 退出")

        # 简单的交互循环
        while True:
            try:
                user_input = input("\n> ").strip()

                if user_input == '/exit' or user_input == '/quit':
                    break
                elif user_input == '/expand':
                    # 展开最后一个折叠的输出
                    for i in range(len(self.tool_outputs) - 1, -1, -1):
                        if self.tool_outputs[i]['collapsed']:
                            self.toggle_output(i)
                            self.console.print(f"[green]✓ 展开了输出 #{i + 1}[/green]")
                            break
                    else:
                        self.console.print("[yellow]没有折叠的输出[/yellow]")
                    with Live(self.render(), console=self.console, refresh_per_second=1) as live:
                        time.sleep(0.5)
                elif user_input == '/collapse':
                    # 折叠最后一个展开的输出
                    for i in range(len(self.tool_outputs) - 1, -1, -1):
                        if not self.tool_outputs[i]['collapsed']:
                            self.toggle_output(i)
                            self.console.print(f"[green]✓ 折叠了输出 #{i + 1}[/green]")
                            break
                    else:
                        self.console.print("[yellow]没有展开的输出[/yellow]")
                    with Live(self.render(), console=self.console, refresh_per_second=1) as live:
                        time.sleep(0.5)
                elif user_input == '/toggle':
                    self.toggle_last_output()
                    self.console.print("[green]✓ 切换了最后一个输出状态[/green]")
                    with Live(self.render(), console=self.console, refresh_per_second=1) as live:
                        time.sleep(0.5)
                elif user_input.startswith('/'):
                    self.console.print(f"[yellow]未知命令: {user_input}[/yellow]")
                    self.console.print("输入 '/exit' 退出")
                else:
                    if user_input:
                        self.console.print(f"[dim]普通输入: {user_input}[/dim]")

            except (KeyboardInterrupt, EOFError):
                break

        self.console.print("\n[cyan]再见![/cyan]")


def main():
    """主函数"""
    cli = EnhancedCLI()
    cli.run_demo()


if __name__ == '__main__':
    main()
