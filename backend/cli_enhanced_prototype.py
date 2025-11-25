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

    def add_tool_output(self, tool_name: str, output: str, auto_collapse: bool = True):
        """添加工具输出"""
        # 超过 20 行自动折叠
        lines = output.count('\n')
        should_collapse = auto_collapse and lines > 20

        self.tool_outputs.append({
            'tool': tool_name,
            'output': output,
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
            collapsed = tool_data['collapsed']
            lines = tool_data['lines']

            if collapsed:
                # 折叠状态
                collapse_text = Text()
                collapse_text.append("▶ ", style="yellow")
                collapse_text.append(f"[{tool_name}] ", style="cyan")
                collapse_text.append(f"({lines} lines) ", style="dim")
                collapse_text.append("[Ctrl+E to expand]", style="dim italic")
                elements.append(collapse_text)
            else:
                # 展开状态
                # 限制显示长度
                display_output = output
                if len(output) > 2000:
                    display_output = output[:2000] + f"\n\n... ({len(output) - 2000} more chars)"

                output_panel = Panel(
                    display_output,
                    title=f"[bold green]▼ {tool_name}[/bold green]",
                    border_style="green",
                    padding=(0, 1)
                )
                elements.append(output_panel)

        # 3. 提示栏
        help_text = Text()
        help_text.append("\n")
        help_text.append("提示: ", style="bold yellow")
        help_text.append("输入 'toggle' 切换最后一个输出 | ", style="dim")
        help_text.append("输入 'quit' 退出", style="dim")
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
                auto_collapse=False
            )
            live.update(self.render())
            time.sleep(2)

            # 模拟 Tool 2: bash_run (长输出，自动折叠)
            long_output = "\n".join([f"Line {i}: Some compilation output..." for i in range(50)])
            self.add_tool_output("bash_run", long_output, auto_collapse=True)
            live.update(self.render())
            time.sleep(2)

            # 模拟 Tool 3: edit_file
            self.add_tool_output(
                "edit_file",
                "File: src/main.cpp\nEdited lines: 45-67\n\nChanges:\n  - Added error handling\n  - Fixed memory leak",
                auto_collapse=False
            )
            live.update(self.render())
            time.sleep(2)

            # 演示交互
            self.console.print("\n[yellow]现在可以输入命令:[/yellow]")
            self.console.print("  • 'toggle' - 切换最后一个输出")
            self.console.print("  • 'quit' - 退出")

        # 简单的交互循环
        while True:
            try:
                user_input = input("\n> ").strip().lower()

                if user_input == 'quit':
                    break
                elif user_input == 'toggle':
                    self.toggle_last_output()
                    with Live(self.render(), console=self.console, refresh_per_second=1) as live:
                        time.sleep(0.5)
                else:
                    self.console.print(f"[yellow]未知命令: {user_input}[/yellow]")

            except (KeyboardInterrupt, EOFError):
                break

        self.console.print("\n[cyan]再见![/cyan]")


def main():
    """主函数"""
    cli = EnhancedCLI()
    cli.run_demo()


if __name__ == '__main__':
    main()
