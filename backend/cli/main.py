# -*- coding: utf-8 -*-
"""
主 CLI 类 - 重构后的简化版本
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from ..agent.loop import AgentLoop
from ..llm.client import OllamaClient
from ..utils.precheck import PreCheck
from ..agent.tools import ConfirmAction
from ..remotectl.commands import RemoteCommands
from ..cli_completer import ClaudeQwenCompleter, PathCompleter, FileNameCompleter, CombinedCompleter
from ..shell_session import PersistentShellSession

from .path_utils import PathUtils
from .output_manager import ToolOutputManager
from .command_registry import CommandRegistry


class CLI:
    """交互式 CLI - 重构版"""

    def __init__(self, project_root: Optional[str] = None, skip_precheck: bool = False):
        """初始化 CLI

        Args:
            project_root: 项目根目录
            skip_precheck: 跳过环境预检查（用于测试）
        """
        self.console = Console()
        self.project_root = project_root or str(Path.cwd())

        # 检查是否在 VSCode 集成模式
        self.vscode_mode = os.getenv('VSCODE_INTEGRATION', '').lower() == 'true'

        # 初始化 RPC 客户端（如果在 VSCode 模式）
        if self.vscode_mode:
            self._init_rpc_client()

        # 运行预检查（除非明确跳过）
        if not skip_precheck:
            self._run_precheck()

        # 初始化全局工具注册器（供工具确认等功能使用）
        from backend.agent.tools import initialize_tools
        initialize_tools(self.project_root)

        # 初始化 agent
        self.client = OllamaClient()
        self.agent = AgentLoop(
            client=self.client,
            project_root=self.project_root,
            confirmation_callback=self._confirm_tool_execution,
            tool_output_callback=None  # 稍后设置
        )

        # 初始化路径工具
        self.path_utils = PathUtils(self.project_root)

        # 初始化输出管理器
        self.output_manager = ToolOutputManager(self.console, self.path_utils, self.agent)

        # 设置 agent 的工具输出回调
        self.agent.tool_output_callback = self.output_manager.add_tool_output

        # 设置 prompt session，包含 tab 补全
        history_file = Path.home() / '.claude_qwen_history'

        # 创建补全器
        command_completer = ClaudeQwenCompleter()
        path_completer = PathCompleter(self.project_root)
        # 使用自适应缓存（None = 根据项目大小自动调整）
        self.filename_completer = FileNameCompleter(self.project_root, cache_duration=None)
        combined_completer = CombinedCompleter([
            command_completer,
            path_completer,
            self.filename_completer
        ])

        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=combined_completer,
            complete_while_typing=False,  # 仅在 Tab 时补全
        )

        # 初始化远程命令（用于 /model 命令）
        self.remote_commands = RemoteCommands(self.console)

        # 初始化持久化 shell session（用于 /cmd）
        self.shell_session = PersistentShellSession(initial_cwd=self.project_root)

        # 初始化命令处理器
        self._init_commands()

    def _init_rpc_client(self):
        """初始化 JSON-RPC 客户端用于 VSCode 通信"""
        from backend.rpc.client import get_client

        try:
            rpc_client = get_client()
            self.console.print("[dim]✓ RPC 客户端已启动（VSCode 集成模式）[/dim]")
        except Exception as e:
            self.console.print(f"[yellow]⚠ RPC 客户端启动失败: {e}[/yellow]")

    def _init_commands(self):
        """初始化命令注册器（自动发现所有命令）"""
        self.command_registry = CommandRegistry(
            self.console,
            agent=self.agent,
            remote_commands=self.remote_commands,
        )

    def _run_precheck(self):
        """运行环境预检查"""
        while True:
            self.console.print("\n[cyan]运行环境检查...[/cyan]")

            # 运行预检查（跳过项目结构检查）
            results = []
            # 首先检查并终止本地 Ollama（如果使用远程）
            results.append(PreCheck.check_and_kill_local_ollama())
            results.append(PreCheck.check_ssh_tunnel())
            results.append(PreCheck.check_ollama_connection())
            results.append(PreCheck.check_ollama_model(model_name="qwen3:latest"))

            # 显示结果
            all_passed = all(r.success for r in results)

            for result in results:
                status = "✓" if result.success else "✗"
                color = "green" if result.success else "red"
                self.console.print(f"[{color}]{status}[/{color}] {result.message}")

            if not all_passed:
                self.console.print("\n[yellow]⚠ 环境检查失败[/yellow]")
                self.console.print("\n[yellow]建议操作:[/yellow]")

                # 加载 SSH 主机配置
                ssh_host = "ollama-tunnel"
                try:
                    config_path = Path(__file__).parent.parent.parent / "config" / "ollama.yaml"
                    with open(config_path, 'r', encoding='utf-8') as f:
                        import yaml
                        config = yaml.safe_load(f)
                        ssh_host = config.get('ssh', {}).get('host', 'ollama-tunnel')
                except Exception:
                    pass

                for result in results:
                    if not result.success:
                        if "SSH Tunnel" in result.name:
                            if "远程 Ollama 服务未运行" in result.message:
                                self.console.print(f"  • 在远程服务器启动 Ollama: [cyan]ssh {ssh_host} 'ollama serve &'[/cyan]")
                            else:
                                self.console.print(f"  • 启动 SSH 隧道: [cyan]ssh -fN {ssh_host}[/cyan]")
                        elif "Ollama Connection" in result.name:
                            self.console.print(f"  • 在远程服务器启动 Ollama: [cyan]ssh {ssh_host} 'nohup ollama serve > /dev/null 2>&1 &'[/cyan]")
                        elif "Ollama Model" in result.name:
                            model = result.details.get('model', 'qwen3:latest')
                            self.console.print(f"  • 拉取模型: [cyan]ollama pull {model}[/cyan]")

                self.console.print("\n[yellow]提示: 使用 --skip-precheck 参数跳过环境检查[/yellow]\n")

                # 询问用户是否要启动 SSH 并重试、重试或退出
                try:
                    self.console.print("选择操作 - \\[s]启动SSH并重试 / \\[R]手动重试 / \\[n]退出: ", end='')

                    # 单键读取（不需要按回车）
                    import platform
                    response = ''
                    if not sys.stdin.isatty():
                        # 非交互模式，使用普通输入
                        response = input().strip().lower() or 'r'
                    elif platform.system() == 'Windows':
                        import msvcrt
                        response = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                        self.console.print(response)  # 回显用户输入
                    else:
                        try:
                            import termios
                            import tty
                            fd = sys.stdin.fileno()
                            old_settings = termios.tcgetattr(fd)
                            try:
                                tty.setraw(fd)
                                response = sys.stdin.read(1).lower()
                            finally:
                                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                            self.console.print(response)  # 回显用户输入
                        except (termios.error, OSError):
                            # 终端不支持 termios，使用普通输入
                            response = input().strip().lower() or 'r'
                    if response == 's':
                        # 启动 SSH 隧道并重试
                        import subprocess
                        import platform

                        try:
                            # 终止占用端口 11434 的进程
                            if platform.system() == 'Windows':
                                # Windows: 使用 netstat 和 taskkill
                                result = subprocess.run(
                                    'netstat -ano | findstr :11434',
                                    shell=True, capture_output=True, text=True
                                )
                                if result.returncode == 0 and result.stdout.strip():
                                    pids = set()
                                    for line in result.stdout.strip().split('\n'):
                                        parts = line.split()
                                        if parts:
                                            pids.add(parts[-1])
                                    for pid in pids:
                                        if pid.strip() and pid != '0':
                                            subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                                    self.console.print(f"[dim]已终止占用端口 11434 的进程 (PID: {', '.join(pids)})[/dim]")
                            else:
                                # macOS/Linux: 使用 lsof
                                result = subprocess.run(
                                    'lsof -i tcp:11434',
                                    shell=True, capture_output=True, text=True
                                )
                                if result.stdout.strip():
                                    # 获取 PID（跳过标题行）
                                    lines = result.stdout.strip().split('\n')[1:]
                                    pids = set()
                                    for line in lines:
                                        parts = line.split()
                                        if len(parts) >= 2:
                                            pids.add(parts[1])
                                    if pids:
                                        for pid in pids:
                                            subprocess.run(['kill', '-9', pid], capture_output=True)
                                        self.console.print(f"[dim]已终止占用端口 11434 的进程 (PID: {', '.join(pids)})[/dim]")
                            import time
                            time.sleep(1)  # 等待端口释放
                        except Exception as e:
                            self.console.print(f"[dim]清理端口失败: {e}[/dim]")

                        # 启动新隧道
                        self.console.print(f"[cyan]启动 SSH 隧道: ssh -fN {ssh_host}[/cyan]")
                        try:
                            subprocess.run(['ssh', '-fN', ssh_host], check=True)
                            self.console.print("[green]✓ SSH 隧道已启动[/green]")
                        except subprocess.CalledProcessError as e:
                            self.console.print(f"[red]✗ SSH 启动失败: {e}[/red]")
                        except FileNotFoundError:
                            self.console.print("[red]✗ 未找到 ssh 命令[/red]")
                        continue
                    elif response == 'n':
                        # 退出
                        self.console.print("[red]已取消启动[/red]")
                        sys.exit(1)
                    else:
                        # 重试（默认，包括空输入）
                        continue
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[red]已取消启动[/red]")
                    sys.exit(1)
            else:
                self.console.print("\n[green]✓ 环境检查通过[/green]")
                break

    def _confirm_tool_execution(self, tool_name: str, category: str, arguments: dict) -> ConfirmAction:
        """提示用户确认工具执行

        Args:
            tool_name: 要执行的工具名称
            category: 工具类别（filesystem, executor, analyzer）
            arguments: 工具参数

        Returns:
            ConfirmAction: 用户的选择（ALLOW_ONCE, ALLOW_ALWAYS, DENY）
        """
        # 获取工具 schema 以检查参数格式
        from backend.agent.tools import registry
        tool_metadata = registry.get_tool_metadata(tool_name)
        param_formats = {}

        if tool_metadata:
            properties = tool_metadata.get('schema', {}).get('function', {}).get('parameters', {}).get('properties', {})
            for param_name, param_info in properties.items():
                if param_info.get('format') == 'filepath':
                    param_formats[param_name] = 'filepath'

        # 格式化参数显示，带路径压缩
        args_display = []

        # 提取行号信息（用于显示）
        line_number = None
        if 'line_range' in arguments and arguments['line_range']:
            # line_range 格式: (start, end) 或 [start, end]
            line_range = arguments['line_range']
            if isinstance(line_range, (tuple, list)) and len(line_range) >= 1:
                line_number = line_range[0]
        elif 'line' in arguments:
            line_number = arguments.get('line')
        elif 'start_line' in arguments:
            line_number = arguments.get('start_line')

        for key, value in arguments.items():
            value_str = str(value)

            # 根据 schema 格式处理路径参数
            if param_formats.get(key) == 'filepath':
                # 获取绝对路径（相对路径基于项目根目录）
                import os
                if not os.path.isabs(value_str):
                    abs_path = os.path.join(self.project_root, value_str)
                else:
                    abs_path = value_str

                # 压缩路径用于显示
                compressed = self.path_utils.compress_path(value_str, max_length=50)

                # 构建 file:// 超链接
                file_uri = f"file://{abs_path}"
                if line_number:
                    # 有些编辑器支持 file://path#line 格式
                    file_uri += f"#{line_number}"

                # 使用 Rich markup 格式的超链接
                value_str = f"[link={file_uri}]{compressed}[/link]"

                # 如果有行号信息，附加显示
                if line_number:
                    value_str += f" [dim]:{line_number}[/dim]"
            # 截断其他长值
            elif len(value_str) > 60:
                value_str = value_str[:57] + "..."

            args_display.append(f"  • {key}: {value_str}")
        args_text = "\n".join(args_display) if args_display else "  (无参数)"

        # 特殊处理 bash_run - 高亮命令
        if tool_name == 'bash_run':
            command = arguments.get('command', '')
            self.console.print(Panel(
                f"[yellow]⚠ 工具执行确认[/yellow] - 工具: [bold]{tool_name}[/bold] | 类别: [dim]{category}[/dim]\n"
                f"命令: [cyan]{command}[/cyan] | 参数:\n{args_text}",
                title="需要确认",
                border_style="yellow"
            ))
        else:
            self.console.print(Panel(
                f"[yellow]⚠ 工具执行确认[/yellow] - 工具: [bold]{tool_name}[/bold] | 类别: [dim]{category}[/dim] | 参数:\n{args_text}",
                title="需要确认",
                border_style="yellow"
            ))

        # 提示操作
        self.console.print("[bold]选择操作:[/bold]")
        self.console.print("  [green]1[/green] - 本次允许 (ALLOW_ONCE)")
        self.console.print("  [blue]2[/blue] - 始终允许 (ALLOW_ALWAYS)")
        self.console.print("  [red]3[/red] - 拒绝并停止 (DENY)")

        while True:
            try:
                choice = input("> ").strip()

                if choice == '1':
                    self.console.print("[green]✓ 本次允许执行[/green]")
                    return ConfirmAction.ALLOW_ONCE
                elif choice == '2':
                    # 获取工具签名用于显示
                    signature = self.agent.confirmation._get_tool_signature(tool_name, arguments)

                    if tool_name == 'bash_run':
                        command = arguments.get('command', '')
                        base_cmd = command.split()[0] if command else ''
                        self.console.print(f"[blue]✓ 始终允许命令: {base_cmd}[/blue]")
                    elif tool_name == 'git':
                        action = arguments.get('action', '')
                        self.console.print(f"[blue]✓ 始终允许 Git 操作: {action}[/blue]")

                        # 检查是否有危险参数仍需确认
                        args = arguments.get('args', {})
                        if self.agent.confirmation.is_dangerous_git_operation(action, args):
                            self.console.print(
                                f"[yellow]  ⚠️  注意：危险参数仍需确认 (如 --force, --hard)[/yellow]"
                            )
                    else:
                        self.console.print(f"[blue]✓ 始终允许工具: {tool_name}[/blue]")

                    # 显示将被允许的签名 key
                    self.console.print(f"[dim]  允许标识: {signature}[/dim]")
                    return ConfirmAction.ALLOW_ALWAYS
                elif choice == '3':
                    self.console.print("[red]✗ 已拒绝，停止执行[/red]")
                    return ConfirmAction.DENY
                else:
                    self.console.print("[yellow]无效选择，请输入 1、2 或 3[/yellow]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("[red]✗ 已取消，停止执行[/red]")
                return ConfirmAction.DENY

    def show_welcome(self):
        """显示欢迎消息"""
        stream_status = "✓ 启用" if self.client.stream_enabled else "✗ 禁用"
        stream_hint = "(实时输出)" if self.client.stream_enabled else "(等待完整响应)"

        welcome = Text()
        welcome.append("Claude-Qwen AI 编程助手\n", style="bold cyan")
        welcome.append("项目根目录", style="bold")
        welcome.append(f": {self.project_root} | ")
        welcome.append("流式输出", style="bold")
        welcome.append(f": {stream_status} {stream_hint}\n")
        welcome.append("可用命令", style="bold")
        welcome.append(":\n")
        welcome.append("  /help", style="green")
        welcome.append(" - 显示帮助 | ")
        welcome.append("/clear", style="green")
        welcome.append(" - 清除对话历史 | ")
        welcome.append("/compact [ratio]", style="green")
        welcome.append(" - 智能压缩上下文\n")
        welcome.append("  /model", style="green")
        welcome.append(" - 管理 Ollama 模型 | ")
        welcome.append("/cmd <command>", style="green")
        welcome.append(" - 执行本地终端命令\n")
        welcome.append("  /root [path]", style="green")
        welcome.append(" - 切换项目根目录 | ")
        welcome.append("/exit", style="green")
        welcome.append(" - 退出 (或按 Ctrl+D)\n")
        welcome.append("快速开始", style="bold")
        welcome.append(": 直接输入您的请求，例如：\n")
        welcome.append("  • \"找到 network_handler.cpp 并添加超时重试机制\"\n", style="dim")
        welcome.append("  • \"编译项目并修复错误\"\n", style="dim")
        welcome.append("💡 按 ")
        welcome.append("Tab", style="bold")
        welcome.append(" 自动补全 | ")
        welcome.append("Ctrl+C", style="bold")
        welcome.append(" 中断执行 | ")
        welcome.append("Ctrl+D", style="bold")
        welcome.append(" 退出程序")

        self.console.print(Panel(welcome, title="欢迎", border_style="blue"))

    def _show_token_status(self):
        """在提示符前显示当前 token 使用情况"""
        if hasattr(self.agent, 'token_counter'):
            total_tokens = self.agent.token_counter.usage.get('total', 0)
            max_tokens = self.agent.token_counter.max_tokens

            # 格式化 tokens 为 K（千）
            if total_tokens >= 1000:
                total_str = f"{total_tokens/1000:.1f}K"
            else:
                total_str = str(total_tokens)

            if max_tokens >= 1000:
                max_str = f"{max_tokens/1000:.0f}K"
            else:
                max_str = str(max_tokens)

            usage_pct = (total_tokens / max_tokens * 100) if max_tokens > 0 else 0

            # 显示 token 信息和文件链接
            token_info = f"[dim]Tokens: {total_str}/{max_str} ({usage_pct:.0f}%)"

            # 添加对话/请求文件链接（如果可用）
            file_path = None
            if hasattr(self.client, 'last_conversation_file') and self.client.last_conversation_file:
                file_path = self.client.last_conversation_file
            elif hasattr(self.client, 'last_request_file') and self.client.last_request_file:
                file_path = self.client.last_request_file

            if file_path and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                file_url = f"file://{os.path.abspath(file_path)}"
                token_info += f" | [link={file_url}]{filename}[/link]"

            token_info += "[/dim]"
            self.console.print(token_info)

    def run(self):
        """运行交互循环"""
        self.show_welcome()
        first_prompt = True

        while True:
            try:
                # 在下一个提示前显示 token 使用情况（首次除外）
                if not first_prompt:
                    self.console.print()  # 在 token 状态前添加空行
                    self._show_token_status()
                first_prompt = False

                # 获取用户输入（提示符中无额外换行）
                user_input = self.session.prompt('> ').strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith('/'):
                    if not self.handle_command(user_input):
                        break
                    continue

                # 清除工具输出并设置当前命令
                self.output_manager.set_current_command(user_input)

                # 执行任务
                self.console.print("[cyan]执行中...[/cyan]")

                try:
                    # 检查配置中是否启用流式输出
                    stream_enabled = self.client.stream_enabled

                    if stream_enabled:
                        # 流式模式：实时输出
                        streamed_content = []

                        def on_chunk(chunk: str):
                            """流式chunk 回调"""
                            # 清理 \r 避免 macOS/Linux 显示 ^M
                            clean_chunk = chunk.replace('\r', '')
                            streamed_content.append(clean_chunk)
                            # 实时打印 chunk
                            self.console.print(clean_chunk, end='', style="white")

                        # 运行并启用流式输出
                        response = self.agent.run(user_input, stream=True, on_chunk=on_chunk)

                        # 如果响应为空（完全流式输出），使用流式内容
                        if not response.strip() and streamed_content:
                            response = ''.join(streamed_content)
                    else:
                        # 非流式模式：等待完整响应
                        response = self.agent.run(user_input, stream=False)

                        # 如果用户拒绝工具执行，不显示面板
                        if response and response != "Tool execution stopped by user.":
                            # 在面板中显示响应
                            self.console.print(Panel(
                                Markdown(response),
                                title="响应",
                                border_style="green"
                            ))

                    # 工具输出已在执行期间内联显示
                    # 无需摘要显示

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
        处理斜杠命令

        Returns:
            False 退出，True 继续
        """
        parts = command.lower().split()
        cmd = parts[0][1:]  # 移除 '/'
        args = parts[1:]

        if cmd in ['exit', 'quit']:
            return False

        elif cmd == 'clear':
            self.agent.conversation_history.clear()
            self.agent.tool_calls.clear()
            self.console.print("[green]已清除对话历史[/green]")

        elif self.command_registry.has(cmd):
            command = self.command_registry.get(cmd)
            if command:
                return command.execute(args)
            else:
                self.console.print(f"[red]错误: 无法加载命令 {cmd}[/red]")
                return True

        elif cmd == 'cache':
            # 显示文件补全缓存信息
            cache_info = self.filename_completer.get_cache_info()

            # 确定项目规模类别
            file_count = cache_info['file_count']
            if file_count < 100:
                size_category = "小型项目"
            elif file_count < 1000:
                size_category = "中型项目"
            elif file_count < 5000:
                size_category = "大型项目"
            else:
                size_category = "超大型项目"

            # 格式化缓存年龄
            cache_age = cache_info['cache_age_seconds']
            if cache_age < 60:
                age_str = f"{cache_age:.1f} 秒前"
            elif cache_age < 3600:
                age_str = f"{cache_age/60:.1f} 分钟前"
            else:
                age_str = f"{cache_age/3600:.1f} 小时前"

            # 格式化缓存时长
            duration = cache_info['cache_duration']
            if duration < 60:
                duration_str = f"{duration} 秒"
            elif duration < 3600:
                duration_str = f"{duration/60:.1f} 分钟"
            else:
                duration_str = f"{duration/3600:.1f} 小时"

            cache_report = f"""
**文件缓存信息**

- **项目规模**: {size_category} ({file_count} 个文件)
- **缓存时长**: {duration_str} {'(自适应)' if cache_info['adaptive_mode'] else '(固定)'}
- **上次扫描**: {age_str}
- **扫描耗时**: {cache_info['last_scan_duration_ms']:.1f} ms
- **缓存状态**: {'✓ 有效' if cache_age < duration else '✗ 已过期（将在下次补全时刷新）'}

💡 缓存时间根据项目大小和扫描性能自动调整
"""
            self.console.print(Panel(cache_report, title="文件补全缓存"))

        elif cmd == 'root':
            if len(args) > 0:
                new_root = args[0]
                if os.path.exists(new_root):
                    self.project_root = os.path.abspath(new_root)
                    self.agent.set_project_root(self.project_root)
                    self.console.print(f"[green]项目根目录已设置为: {self.project_root}[/green]")
                else:
                    self.console.print(f"[red]目录不存在: {new_root}[/red]")
            else:
                self.console.print(f"当前项目根目录: {self.project_root}")

        elif cmd == 'cmd':
            # 执行本地命令（持久化 shell）
            if len(args) > 0:
                cmd_to_run = ' '.join(args)
                self.console.print(f"[cyan]执行命令:[/cyan] {cmd_to_run}")
                success, stdout, stderr = self.shell_session.execute(cmd_to_run)

                if stdout:
                    self.console.print(stdout)
                if stderr:
                    self.console.print(f"[red]{stderr}[/red]")

                if success:
                    self.console.print(f"[green]✓ 命令执行成功[/green]")
                else:
                    self.console.print(f"[red]✗ 命令执行失败[/red]")
            else:
                self.console.print("[yellow]用法: /cmd <command>[/yellow]")
                self.console.print("示例: /cmd ls -la")
                self.console.print("[dim]提示: 持久化会话，cd 等命令会保留状态[/dim]")

        elif cmd == 'cmdremote':
            # 执行远程命令
            if len(args) > 0:
                cmd_to_run = ' '.join(args)
                self.remote_commands.execute_remote_command(cmd_to_run)
            else:
                self.console.print("[yellow]用法: /cmdremote <command>[/yellow]")
                self.console.print("示例: /cmdremote ps aux | grep ollama")

        elif cmd == 'cmdclear':
            # 重置持久化 shell session
            self.console.print("[yellow]重置 shell 会话...[/yellow]")
            self.shell_session.reset()
            self.console.print(f"[green]✓ Shell 会话已重置到初始目录: {self.project_root}[/green]")

        else:
            self.console.print(f"[yellow]未知命令: /{cmd}[/yellow]")
            self.console.print("输入 /help 查看可用命令")

        return True


def main():
    """Main entry point"""
    import argparse
    import sys

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
