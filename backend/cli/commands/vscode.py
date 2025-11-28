# -*- coding: utf-8 -*-
"""
VSCode 集成命令
"""

import subprocess
import shutil
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .base import Command


class VSCodeCommand(Command):
    """VSCode 集成命令"""

    def __init__(self, console: Console):
        """
        初始化 VSCode 命令

        Args:
            console: Rich Console 实例
        """
        super().__init__(console)

    @property
    def name(self) -> str:
        return "vscode"

    @property
    def aliases(self) -> List[str]:
        return ["testvs"]

    @property
    def description(self) -> str:
        return "VSCode 集成功能"

    @property
    def category(self) -> str:
        return "vscode"

    @property
    def usage(self) -> str:
        return "/vscode [test]"

    def execute(self, args: List[str]) -> bool:
        """执行 VSCode 相关命令"""
        # 如果是通过 testvs 别名调用
        if len(args) > 0 and args[0] == 'test':
            self.test_integration()
        else:
            self.open_in_vscode()
        return True

    def test_integration(self):
        """测试 VSCode extension 集成"""
        from backend.tools import vscode
        from backend.rpc.client import is_vscode_mode

        self.console.print("\n[cyan]═══════════════════════════════════════[/cyan]")
        self.console.print("[cyan bold]  VSCode Extension 集成测试[/cyan bold]")
        self.console.print("[cyan]═══════════════════════════════════════[/cyan]\n")

        # 检查通信模式
        mode = "VSCode RPC" if is_vscode_mode() else "Mock"
        self.console.print(f"[dim]通信模式: {mode}[/dim]\n")

        # 创建结果表格
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("测试项", style="white", width=30)
        table.add_column("状态", style="green", width=10)
        table.add_column("结果", style="dim", width=50)

        # 测试 1: 获取当前文件
        try:
            file_info = vscode.get_active_file()
            table.add_row(
                "1. 获取当前文件",
                "[green]✓[/green]",
                f"路径: {file_info['path']}\n行数: {file_info['lineCount']}"
            )
        except Exception as e:
            table.add_row("1. 获取当前文件", "[red]✗[/red]", str(e))

        # 测试 2: 获取选中文本
        try:
            selection = vscode.get_selection()
            table.add_row(
                "2. 获取选中文本",
                "[green]✓[/green]",
                f"文本: {selection['text'][:30]}...\n"
                f"位置: L{selection['start']['line']}-L{selection['end']['line']}"
            )
        except Exception as e:
            table.add_row("2. 获取选中文本", "[red]✗[/red]", str(e))

        # 测试 3: 显示 diff
        try:
            modified = """#include <iostream>
#include <string>

int main() {
    std::string name = "Claude";
    std::cout << "Hello " << name << std::endl;
    return 0;
}
"""
            result = vscode.show_diff(
                title="测试修改",
                original_path="/path/to/project/src/main.cpp",
                modified_content=modified
            )
            table.add_row(
                "3. 显示 Diff 对比",
                "[green]✓[/green]",
                result.get("message", "Diff displayed")
            )
        except Exception as e:
            table.add_row("3. 显示 Diff 对比", "[red]✗[/red]", str(e))

        # 测试 4: 应用修改
        try:
            result = vscode.apply_changes(
                path="/path/to/project/src/main.cpp",
                old_str='std::cout << "Hello World" << std::endl;',
                new_str='std::cout << "Hello Claude" << std::endl;'
            )
            table.add_row(
                "4. 应用代码修改",
                "[green]✓[/green]",
                result.get("message", "Changes applied")
            )
        except Exception as e:
            table.add_row("4. 应用代码修改", "[red]✗[/red]", str(e))

        # 测试 5: 打开文件
        try:
            result = vscode.open_file(
                path="/path/to/project/src/network.cpp",
                line=42,
                column=10
            )
            table.add_row(
                "5. 打开文件",
                "[green]✓[/green]",
                result.get("message", "File opened")
            )
        except Exception as e:
            table.add_row("5. 打开文件", "[red]✗[/red]", str(e))

        # 测试 6: 获取工作区路径
        try:
            workspace = vscode.get_workspace_folder()
            table.add_row(
                "6. 获取工作区路径",
                "[green]✓[/green]",
                f"路径: {workspace}"
            )
        except Exception as e:
            table.add_row("6. 获取工作区路径", "[red]✗[/red]", str(e))

        # 显示结果
        self.console.print(table)

        # 显示示例数据
        if not is_vscode_mode():
            self.console.print("\n[cyan]Mock 数据示例:[/cyan]")
            self.console.print(Panel(
                f"[bold]当前文件:[/bold]\n"
                f"{vscode.MOCK_DATA['active_file']['path']}\n\n"
                f"[bold]文件内容:[/bold]\n"
                f"[dim]{vscode.MOCK_DATA['active_file']['content']}[/dim]\n\n"
                f"[bold]选中文本:[/bold]\n"
                f"{vscode.MOCK_DATA['selection']['text']}",
                title="Mock 数据",
                border_style="cyan"
            ))
        else:
            self.console.print("\n[green]✓ 使用真实 VSCode 数据[/green]")

        # 显示下一步
        self.console.print("\n[yellow]下一步:[/yellow]")
        self.console.print("  1. 实现 VSCode extension 通信协议（JSON-RPC）")
        self.console.print("  2. 添加 IPC 或 Socket 通信模式")
        self.console.print("  3. 在 VSCode extension 中实现对应的命令处理")
        self.console.print("  4. 测试实际的 extension 对接\n")

    def open_in_vscode(self, project_root: str = "."):
        """在 VSCode 中打开当前项目"""
        self.console.print("\n[cyan]打开 VSCode...[/cyan]")

        # 检查 code 命令是否可用
        if not shutil.which('code'):
            self.console.print("[red]错误: 未找到 'code' 命令[/red]")
            self.console.print("[yellow]请确保已安装 VSCode 并添加到 PATH[/yellow]")
            self.console.print("[dim]安装方法: VSCode → Command Palette → 'Shell Command: Install code command in PATH'[/dim]")
            return

        # 检查 extension 是否安装
        try:
            result = subprocess.run(
                ['code', '--list-extensions'],
                capture_output=True,
                text=True,
                timeout=5
            )
            extensions = result.stdout.lower()
            extension_installed = 'claude-qwen' in extensions
        except Exception:
            extension_installed = False

        if not extension_installed:
            self.console.print("[yellow]⚠ Claude-Qwen extension 未安装[/yellow]")
            self.console.print("\n[dim]安装方法:[/dim]")
            self.console.print("  cd vscode-extension")
            self.console.print("  npm install && npm run package")
            self.console.print("  code --install-extension claude-qwen-0.1.0.vsix\n")

            response = input("是否继续打开 VSCode? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                return

        # 打开 VSCode
        try:
            self.console.print(f"[dim]执行: code {project_root}[/dim]")
            subprocess.run(
                ['code', project_root],
                check=True,
                timeout=10
            )
            self.console.print("[green]✓ VSCode 已打开[/green]")

            if extension_installed:
                self.console.print("\n[cyan]提示:[/cyan]")
                self.console.print("  在 VSCode 中按 Ctrl+Shift+P")
                self.console.print("  输入: 'Claude-Qwen: Start'")
                self.console.print("  开始使用 AI 助手")
        except subprocess.TimeoutExpired:
            self.console.print("[yellow]⚠ VSCode 启动超时，但可能已在后台运行[/yellow]")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")
