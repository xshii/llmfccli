# -*- coding: utf-8 -*-
"""
Command-line interface for Claude-Qwen
"""

import sys
import os
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.console import Group

from .agent.loop import AgentLoop
from .llm.client import OllamaClient
from .utils.precheck import PreCheck
from .agent.tool_confirmation import ConfirmAction
from .remotectl.commands import RemoteCommands


class CLI:
    """Interactive CLI for Claude-Qwen"""
    
    def __init__(self, project_root: Optional[str] = None, skip_precheck: bool = False):
        """Initialize CLI

        Args:
            project_root: Project root directory
            skip_precheck: Skip environment pre-check (for testing)
        """
        self.console = Console()
        self.project_root = project_root or str(Path.cwd())

        # Check if in VSCode integration mode
        self.vscode_mode = os.getenv('VSCODE_INTEGRATION', '').lower() == 'true'

        # Initialize RPC client if in VSCode mode
        if self.vscode_mode:
            self._init_rpc_client()

        # Run pre-check unless explicitly skipped
        if not skip_precheck:
            self._run_precheck()

        # Initialize agent
        self.client = OllamaClient()
        self.agent = AgentLoop(
            client=self.client,
            project_root=self.project_root,
            confirmation_callback=self._confirm_tool_execution,
            tool_output_callback=self.add_tool_output
        )

        # Setup prompt session
        history_file = Path.home() / '.claude_qwen_history'
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )

        # Initialize remote commands (for /model commands)
        self.remote_commands = RemoteCommands(self.console)

        # Tool output management (for enhanced display)
        self.current_command = ""
        self.command_start_time = None
        self.tool_outputs = []  # [{'tool', 'output', 'args', 'collapsed', 'lines'}]

    def _init_rpc_client(self):
        """Initialize JSON-RPC client for VSCode communication"""
        from backend.rpc.client import get_client

        try:
            rpc_client = get_client()
            self.console.print("[dim]✓ RPC 客户端已启动（VSCode 集成模式）[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]⚠ RPC 客户端启动失败: {e}[/yellow]")

    def add_tool_output(self, tool_name: str, output: str, args: dict = None, auto_collapse: bool = True):
        """Add tool output with automatic collapse for long outputs

        Args:
            tool_name: Tool name
            output: Output content
            args: Tool arguments (optional)
            auto_collapse: Auto-collapse if output >20 lines
        """
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
        """Toggle collapse state of specific output"""
        if 0 <= index < len(self.tool_outputs):
            self.tool_outputs[index]['collapsed'] = not self.tool_outputs[index]['collapsed']

    def toggle_last_output(self):
        """Toggle collapse state of last output"""
        if self.tool_outputs:
            self.toggle_output(len(self.tool_outputs) - 1)

    def display_tool_outputs_summary(self):
        """Display summary of all tool outputs"""
        if not self.tool_outputs:
            return

        elements = []

        # Calculate execution time
        import time
        elapsed_time = ""
        if self.command_start_time:
            elapsed = time.time() - self.command_start_time
            if elapsed < 60:
                elapsed_time = f" [dim]({elapsed:.1f}s)[/dim]"
            else:
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                elapsed_time = f" [dim]({minutes}m {seconds}s)[/dim]"

        # Get token usage
        token_info = ""
        if hasattr(self.agent, 'token_counter'):
            total_tokens = self.agent.token_counter.usage.get('total', 0)
            max_tokens = self.agent.token_counter.max_tokens

            # Format tokens in K (thousands)
            if total_tokens >= 1000:
                total_str = f"{total_tokens/1000:.1f}K"
            else:
                total_str = str(total_tokens)

            if max_tokens >= 1000:
                max_str = f"{max_tokens/1000:.0f}K"
            else:
                max_str = str(max_tokens)

            usage_pct = (total_tokens / max_tokens * 100) if max_tokens > 0 else 0
            token_info = f" [dim][Tokens: {total_str}/{max_str} ({usage_pct:.0f}%)][/dim]"

        # Command panel (at top)
        command_text = Text()
        command_text.append("> ", style="cyan bold")
        command_text.append(self.current_command, style="cyan bold")

        command_panel = Panel(
            command_text,
            title=f"[bold blue]Command{elapsed_time}{token_info}[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
        elements.append(command_panel)

        # Tool outputs
        for i, tool_data in enumerate(self.tool_outputs):
            tool_name = tool_data['tool']
            output = tool_data['output']
            args = tool_data['args']
            collapsed = tool_data['collapsed']
            lines = tool_data['lines']

            # Format arguments for display
            args_str = ""
            if args:
                args_display = []
                for key, value in args.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    args_display.append(f"{key}={repr(value_str)}")
                args_str = f" ({', '.join(args_display)})"

            if collapsed:
                # Collapsed state
                collapse_text = Text()
                collapse_text.append("▶ ", style="yellow")
                collapse_text.append(f"[{tool_name}]", style="cyan bold")
                if args_str:
                    collapse_text.append(args_str, style="cyan dim")
                collapse_text.append(f" ({lines} lines) ", style="dim")
                collapse_text.append("[Use /expand to view]", style="dim italic")
                elements.append(collapse_text)
            else:
                # Expanded state
                display_output = output
                if len(output) > 2000:
                    display_output = output[:2000] + f"\n\n... ({len(output) - 2000} more chars)"

                title = f"[bold green]▼ {tool_name}[/bold green]"
                if args_str:
                    title += f"[dim]{args_str}[/dim]"

                output_panel = Panel(
                    display_output,
                    title=title,
                    border_style="green",
                    padding=(0, 1)
                )
                elements.append(output_panel)

        # Print all elements
        for element in elements:
            self.console.print(element)

        # Print hints
        if any(t['collapsed'] for t in self.tool_outputs):
            self.console.print("\n[dim]提示: 使用 /expand 展开折叠的输出, /collapse 折叠输出, /toggle 切换最后一个[/dim]")

    def _run_precheck(self):
        """Run environment pre-check"""
        while True:
            self.console.print("\n[cyan]运行环境检查...[/cyan]")

            # Run pre-checks (skip project structure check)
            results = []
            # First check and kill local Ollama if using remote
            results.append(PreCheck.check_and_kill_local_ollama())
            results.append(PreCheck.check_ssh_tunnel())
            results.append(PreCheck.check_ollama_connection())
            results.append(PreCheck.check_ollama_model(model_name="qwen3:latest"))

            # Display results
            all_passed = all(r.success for r in results)

            for result in results:
                status = "✓" if result.success else "✗"
                color = "green" if result.success else "red"
                self.console.print(f"[{color}]{status}[/{color}] {result.message}")

            if not all_passed:
                self.console.print("\n[yellow]⚠ 环境检查失败[/yellow]")
                self.console.print("\n[yellow]建议操作:[/yellow]")

                for result in results:
                    if not result.success:
                        if "SSH Tunnel" in result.name:
                            self.console.print("  • 启动 SSH 隧道: [cyan]ssh -fN ollama-tunnel[/cyan]")
                        elif "Ollama Connection" in result.name:
                            self.console.print("  • 验证远程服务器上的 Ollama 服务是否运行")
                        elif "Ollama Model" in result.name:
                            model = result.details.get('model', 'qwen3:latest')
                            self.console.print(f"  • 拉取模型: [cyan]ollama pull {model}[/cyan]")

                self.console.print("\n[yellow]提示: 使用 --skip-precheck 参数跳过环境检查[/yellow]\n")

                # Ask user if they want to continue, retry, or quit
                try:
                    response = input("选择操作 - [r]重试 / [y]继续 / [N]退出: ").strip().lower()
                    if response == 'r':
                        # Retry - continue the while loop
                        continue
                    elif response in ['y', 'yes']:
                        # Continue despite failures
                        break
                    else:
                        # Quit (default)
                        self.console.print("[red]已取消启动[/red]")
                        sys.exit(1)
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[red]已取消启动[/red]")
                    sys.exit(1)
            else:
                self.console.print("\n[green]✓ 环境检查通过[/green]")
                break

    def _confirm_tool_execution(self, tool_name: str, category: str, arguments: dict) -> ConfirmAction:
        """Prompt user to confirm tool execution

        Args:
            tool_name: Name of the tool to execute
            category: Tool category (filesystem, executor, analyzer)
            arguments: Tool arguments

        Returns:
            ConfirmAction: User's choice (ALLOW_ONCE, ALLOW_ALWAYS, DENY)
        """
        # Format arguments for display
        args_display = []
        for key, value in arguments.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 60:
                value_str = value_str[:57] + "..."
            args_display.append(f"  • {key}: {value_str}")
        args_text = "\n".join(args_display) if args_display else "  (无参数)"

        # Special handling for bash_run - highlight the command
        if tool_name == 'bash_run':
            command = arguments.get('command', '')
            self.console.print(Panel(
                f"[yellow]⚠ 工具执行确认[/yellow]\n\n"
                f"[bold]工具:[/bold] {tool_name}\n"
                f"[bold]类别:[/bold] {category}\n"
                f"[bold]命令:[/bold] [cyan]{command}[/cyan]\n\n"
                f"[dim]参数:[/dim]\n{args_text}",
                title="需要确认",
                border_style="yellow"
            ))
        else:
            self.console.print(Panel(
                f"[yellow]⚠ 工具执行确认[/yellow]\n\n"
                f"[bold]工具:[/bold] {tool_name}\n"
                f"[bold]类别:[/bold] {category}\n\n"
                f"[dim]参数:[/dim]\n{args_text}",
                title="需要确认",
                border_style="yellow"
            ))

        # Prompt for action
        self.console.print("\n[bold]选择操作:[/bold]")
        self.console.print("  [green]1[/green] - 本次允许 (ALLOW_ONCE)")
        self.console.print("  [blue]2[/blue] - 始终允许 (ALLOW_ALWAYS)")
        self.console.print("  [red]3[/red] - 拒绝并停止 (DENY)")

        while True:
            try:
                choice = input("\n请输入选择 (1/2/3): ").strip()

                if choice == '1':
                    self.console.print("[green]✓ 本次允许执行[/green]\n")
                    return ConfirmAction.ALLOW_ONCE
                elif choice == '2':
                    if tool_name == 'bash_run':
                        command = arguments.get('command', '')
                        base_cmd = command.split()[0] if command else ''
                        self.console.print(f"[blue]✓ 始终允许命令: {base_cmd}[/blue]\n")
                    else:
                        self.console.print(f"[blue]✓ 始终允许工具: {tool_name}[/blue]\n")
                    return ConfirmAction.ALLOW_ALWAYS
                elif choice == '3':
                    self.console.print("[red]✗ 已拒绝，停止执行[/red]\n")
                    return ConfirmAction.DENY
                else:
                    self.console.print("[yellow]无效选择，请输入 1、2 或 3[/yellow]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[red]✗ 已取消，停止执行[/red]\n")
                return ConfirmAction.DENY

    def show_welcome(self):
        """Show welcome message"""
        stream_status = "✓ 启用" if self.client.stream_enabled else "✗ 禁用"
        stream_hint = "(实时输出)" if self.client.stream_enabled else "(等待完整响应)"

        welcome = """
# Claude-Qwen AI 编程助手

**项目根目录**: {root}
**流式输出**: {stream_status} {stream_hint}

**可用命令**:
- `/help` - 显示帮助
- `/clear` - 清除对话历史（保留文件访问）
- `/compact` - 手动压缩上下文
- `/usage` - 显示 Token 使用情况
- `/reset-confirmations` - 重置工具执行确认
- `/model` - 管理 Ollama 模型（list/create/pull/health）
- `/cmd <command>` - 执行本地终端命令
- `/cmdremote <command>` - 执行远程终端命令（SSH）
- `/expand` / `/collapse` / `/toggle` - 展开/折叠工具输出
- `/exit` - 退出

**快速开始**: 直接输入您的请求，例如：
- "找到 network_handler.cpp 并添加超时重试机制"
- "编译项目并修复错误"
- "为当前文件生成单元测试"

💡 修改 `config/ollama.yaml` 中的 `stream` 配置可切换输出模式
💡 工具输出超过 20 行会自动折叠，使用 /expand 查看详情
"""
        self.console.print(Panel(
            Markdown(welcome.format(
                root=self.project_root,
                stream_status=stream_status,
                stream_hint=stream_hint
            )),
            title="欢迎",
            border_style="blue"
        ))
    
    def run(self):
        """Run interactive loop"""
        self.show_welcome()
        
        while True:
            try:
                # Get user input
                user_input = self.session.prompt('\n> ').strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Clear tool outputs and set current command
                import time
                self.current_command = user_input
                self.command_start_time = time.time()
                self.tool_outputs = []

                # Execute task
                self.console.print("\n[cyan]执行中...[/cyan]")

                try:
                    # Check if streaming is enabled in config
                    stream_enabled = self.client.stream_enabled

                    if stream_enabled:
                        # Streaming mode: real-time output
                        streamed_content = []

                        def on_chunk(chunk: str):
                            """Callback for streaming chunks"""
                            streamed_content.append(chunk)
                            # Print chunk in real-time
                            self.console.print(chunk, end='', style="white")

                        # Run with streaming enabled
                        response = self.agent.run(user_input, stream=True, on_chunk=on_chunk)

                        # Print newline after streaming
                        self.console.print("\n")

                        # If response is empty (fully streamed), use streamed content
                        if not response.strip() and streamed_content:
                            response = ''.join(streamed_content)
                    else:
                        # Non-streaming mode: wait for complete response
                        response = self.agent.run(user_input, stream=False)

                        # Display response in panel
                        self.console.print(Panel(
                            Markdown(response),
                            title="响应",
                            border_style="green"
                        ))

                    # Display tool outputs summary if any
                    if self.tool_outputs:
                        self.display_tool_outputs_summary()

                except Exception as e:
                    self.console.print(f"[red]错误: {e}[/red]")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]已取消[/yellow]")
                continue
            except EOFError:
                break
        
        self.console.print("\n[blue]再见![/blue]")
    
    def handle_command(self, command: str) -> bool:
        """
        Handle slash commands
        
        Returns:
            False to exit, True to continue
        """
        cmd = command.lower().split()[0]
        
        if cmd == '/exit' or cmd == '/quit':
            return False
        
        elif cmd == '/help':
            self.show_help()
        
        elif cmd == '/clear':
            self.agent.conversation_history.clear()
            self.agent.tool_calls.clear()
            self.console.print("[green]已清除对话历史[/green]")
        
        elif cmd == '/compact':
            self.console.print("[cyan]压缩中...[/cyan]")
            self.agent._compress_context()
            self.console.print("[green]压缩完成[/green]")
            self.console.print(self.agent.get_usage_report())
        
        elif cmd == '/usage':
            report = self.agent.get_usage_report()
            self.console.print(Panel(report, title="Token 使用情况"))
        
        elif cmd == '/root':
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                new_root = parts[1]
                if os.path.exists(new_root):
                    self.project_root = os.path.abspath(new_root)
                    self.agent.set_project_root(self.project_root)
                    self.console.print(f"[green]项目根目录已设置为: {self.project_root}[/green]")
                else:
                    self.console.print(f"[red]目录不存在: {new_root}[/red]")
            else:
                self.console.print(f"当前项目根目录: {self.project_root}")

        elif cmd == '/reset-confirmations':
            # Reset all saved confirmations
            self.agent.confirmation.reset_confirmations()
            self.console.print("[green]✓ 已重置所有工具执行确认[/green]")
            self.console.print("[dim]下次执行工具时将重新询问确认[/dim]")

        elif cmd == '/model':
            # Handle model management commands
            self.handle_model_command(command)

        elif cmd == '/cmd':
            # Execute local command
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                cmd_to_run = parts[1]
                self.remote_commands.execute_local_command(cmd_to_run)
            else:
                self.console.print("[yellow]用法: /cmd <command>[/yellow]")
                self.console.print("示例: /cmd ls -la")

        elif cmd == '/cmdremote':
            # Execute remote command
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                cmd_to_run = parts[1]
                self.remote_commands.execute_remote_command(cmd_to_run)
            else:
                self.console.print("[yellow]用法: /cmdremote <command>[/yellow]")
                self.console.print("示例: /cmdremote ps aux | grep ollama")

        elif cmd == '/expand':
            # Expand last collapsed output
            for i in range(len(self.tool_outputs) - 1, -1, -1):
                if self.tool_outputs[i]['collapsed']:
                    self.toggle_output(i)
                    self.console.print(f"[green]✓ 展开了输出 #{i + 1}[/green]")
                    return True
            self.console.print("[yellow]没有折叠的输出[/yellow]")

        elif cmd == '/collapse':
            # Collapse last expanded output
            for i in range(len(self.tool_outputs) - 1, -1, -1):
                if not self.tool_outputs[i]['collapsed']:
                    self.toggle_output(i)
                    self.console.print(f"[green]✓ 折叠了输出 #{i + 1}[/green]")
                    return True
            self.console.print("[yellow]没有展开的输出[/yellow]")

        elif cmd == '/toggle':
            # Toggle last output
            self.toggle_last_output()
            self.console.print("[green]✓ 切换了最后一个输出状态[/green]")

        elif cmd == '/testvs':
            # Test VSCode integration
            self.test_vscode_integration()

        elif cmd == '/vscode':
            # Open current project in VSCode
            self.open_in_vscode()

        else:
            self.console.print(f"[yellow]未知命令: {cmd}[/yellow]")
            self.console.print("输入 /help 查看可用命令")

        return True

    def test_vscode_integration(self):
        """Test VSCode extension integration

        Tests various VSCode operations:
        - Get active file
        - Get selection
        - Show diff
        - Apply changes
        - Open file
        - Get workspace folder
        """
        from backend.tools import vscode
        from backend.rpc.client import is_vscode_mode
        from rich.table import Table

        self.console.print("\n[cyan]═══════════════════════════════════════[/cyan]")
        self.console.print("[cyan bold]  VSCode Extension 集成测试[/cyan bold]")
        self.console.print("[cyan]═══════════════════════════════════════[/cyan]\n")

        # Check communication mode
        mode = "VSCode RPC" if is_vscode_mode() else "Mock"
        self.console.print(f"[dim]通信模式: {mode}[/dim]\n")

        # Create results table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("测试项", style="white", width=30)
        table.add_column("状态", style="green", width=10)
        table.add_column("结果", style="dim", width=50)

        # Test 1: Get active file
        try:
            file_info = vscode.get_active_file()
            table.add_row(
                "1. 获取当前文件",
                "[green]✓[/green]",
                f"路径: {file_info['path']}\n行数: {file_info['lineCount']}"
            )
        except Exception as e:
            table.add_row("1. 获取当前文件", "[red]✗[/red]", str(e))

        # Test 2: Get selection
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

        # Test 3: Show diff
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

        # Test 4: Apply changes
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

        # Test 5: Open file
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

        # Test 6: Get workspace folder
        try:
            workspace = vscode.get_workspace_folder()
            table.add_row(
                "6. 获取工作区路径",
                "[green]✓[/green]",
                f"路径: {workspace}"
            )
        except Exception as e:
            table.add_row("6. 获取工作区路径", "[red]✗[/red]", str(e))

        # Display results
        self.console.print(table)

        # Display sample data
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

        # Display next steps
        self.console.print("\n[yellow]下一步:[/yellow]")
        self.console.print("  1. 实现 VSCode extension 通信协议（JSON-RPC）")
        self.console.print("  2. 添加 IPC 或 Socket 通信模式")
        self.console.print("  3. 在 VSCode extension 中实现对应的命令处理")
        self.console.print("  4. 测试实际的 extension 对接\n")

    def open_in_vscode(self):
        """Open current project in VSCode with Claude-Qwen extension"""
        import subprocess
        import shutil

        self.console.print("\n[cyan]打开 VSCode...[/cyan]")

        # Check if code command is available
        if not shutil.which('code'):
            self.console.print("[red]错误: 未找到 'code' 命令[/red]")
            self.console.print("[yellow]请确保已安装 VSCode 并添加到 PATH[/yellow]")
            self.console.print("[dim]安装方法: VSCode → Command Palette → 'Shell Command: Install code command in PATH'[/dim]")
            return

        # Check if extension is installed
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

        # Open VSCode
        try:
            self.console.print(f"[dim]执行: code {self.project_root}[/dim]")
            subprocess.run(
                ['code', self.project_root],
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

    def handle_model_command(self, command: str):
        """Handle /model subcommands for Ollama model management

        Available subcommands:
        - /model list - List all models
        - /model create - Create claude-qwen model
        - /model show <name> - Show model details
        - /model delete <name> - Delete a model
        - /model pull <name> - Pull a model from registry
        - /model health - Check Ollama server health
        """
        parts = command.split()

        if len(parts) < 2:
            self.console.print("[yellow]用法: /model <subcommand> [args][/yellow]")
            self.console.print("\n可用子命令:")
            self.console.print("  • list - 列出所有模型")
            self.console.print("  • create - 创建 claude-qwen 模型")
            self.console.print("  • show <name> - 显示模型详情")
            self.console.print("  • delete <name> - 删除模型")
            self.console.print("  • pull <name> - 拉取模型")
            self.console.print("  • health - 检查服务器健康状态")
            return

        subcmd = parts[1].lower()

        if subcmd == 'list':
            self.remote_commands.list_models()

        elif subcmd == 'create':
            self.remote_commands.create_model()

        elif subcmd == 'show':
            if len(parts) < 3:
                self.console.print("[red]错误: 需要指定模型名称[/red]")
                self.console.print("用法: /model show <model_name>")
                return
            self.remote_commands.show_model(parts[2])

        elif subcmd == 'delete':
            if len(parts) < 3:
                self.console.print("[red]错误: 需要指定模型名称[/red]")
                self.console.print("用法: /model delete <model_name>")
                return
            confirm = '-y' in parts or '--yes' in parts
            self.remote_commands.delete_model(parts[2], confirm=confirm)

        elif subcmd == 'pull':
            if len(parts) < 3:
                self.console.print("[red]错误: 需要指定模型名称[/red]")
                self.console.print("用法: /model pull <model_name>")
                return
            self.remote_commands.pull_model(parts[2])

        elif subcmd == 'health':
            self.remote_commands.check_health()

        else:
            self.console.print(f"[yellow]未知子命令: {subcmd}[/yellow]")
            self.console.print("输入 /model 查看可用子命令")

    def show_help(self):
        """Show help message"""
        help_text = """
## 可用命令

### Agent 控制
- `/help` - 显示此帮助信息
- `/clear` - 清除对话历史（保留文件访问权限）
- `/compact` - 手动触发上下文压缩
- `/usage` - 显示 Token 使用情况
- `/root [path]` - 查看或设置项目根目录
- `/reset-confirmations` - 重置所有工具执行确认
- `/exit` 或 `/quit` - 退出程序

### 工具输出管理
- `/expand` - 展开最后一个折叠的工具输出
- `/collapse` - 折叠最后一个展开的工具输出
- `/toggle` - 切换最后一个工具输出的状态

### VSCode 集成
- `/vscode` - 在 VSCode 中打开当前项目
- `/testvs` - 测试 VSCode extension 集成（Mock 模式）

### 模型管理
- `/model list` - 列出所有 Ollama 模型
- `/model create` - 创建 claude-qwen 模型
- `/model show <name>` - 显示模型详情
- `/model delete <name>` - 删除模型
- `/model pull <name>` - 拉取模型
- `/model health` - 检查 Ollama 服务器状态

### 命令透传
- `/cmd <command>` - 在本地执行终端命令
- `/cmdremote <command>` - 在远程服务器执行终端命令（通过 SSH）

## 示例用法

**文件操作**:
```
找到 network_handler.cpp 并添加超时重试机制
```

**编译修复**:
```
编译项目并修复所有错误
```

**测试生成**:
```
为当前文件生成单元测试
分析 HTTP 模块并生成集成测试
```

**代码分析**:
```
分析项目结构
查找所有网络相关的函数
```

**命令透传**:
```
/cmd ls -la                    # 查看本地目录
/cmd ps aux | grep ollama      # 查看本地进程
/cmdremote ollama list         # 在远程服务器列出模型
/cmdremote nvidia-smi          # 查看远程 GPU 状态
```

**工具输出管理**:
工具输出超过 20 行会自动折叠，使用 `/expand` 展开查看详细信息。
"""
        self.console.print(Panel(Markdown(help_text), title="帮助"))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Claude-Qwen AI 编程助手')
    parser.add_argument('--root', '-r', help='项目根目录', default=None)
    parser.add_argument('--skip-precheck', action='store_true',
                        help='跳过环境预检查（用于测试或离线环境）')
    parser.add_argument('--version', '-v', action='version', version='0.1.0')

    args = parser.parse_args()

    # Initialize and run CLI
    cli = CLI(project_root=args.root, skip_precheck=args.skip_precheck)

    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
