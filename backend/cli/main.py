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
from ..agent.tools import ConfirmAction, ConfirmResult
from ..remotectl.commands import RemoteCommands
from .cli_completer import ClaudeQwenCompleter, PathCompleter, FileNameCompleter, CombinedCompleter
from ..utils.shell_session import PersistentShellSession
from ..tools.executor_tools.bash_session import set_shared_session
from ..utils.i18n import I18n
from ..utils.feature import is_feature_enabled

from .path_utils import PathUtils
from .output_manager import ToolOutputManager
from .command_registry import CommandRegistry
from .status_line import StatusLine


class CLI:
    """交互式 CLI - 重构版"""

    def __init__(self, project_root: Optional[str] = None, skip_precheck: bool = False):
        """初始化 CLI

        Args:
            project_root: 项目根目录
            skip_precheck: 跳过环境预检查（用于测试）
        """
        # 初始化语言设置（必须在所有工具加载之前）
        I18n.initialize()

        self.console = Console()
        self.project_root = project_root or str(Path.cwd())

        # 切换工作目录到项目根目录
        os.chdir(self.project_root)

        # 启动 RPC 客户端（后台心跳检测 VSCode extension）
        from backend.rpc.client import get_client
        get_client()  # 启动心跳线程

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

        # 初始化状态行
        self.status_line = StatusLine(self.console, self.agent, self.client, self.project_root)

        # 设置 agent 的工具输出回调
        self.agent.tool_output_callback = self.output_manager.add_tool_output

        # 设置流式输出回调（实时打印命令输出）
        self._setup_streaming_callbacks()

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

        # 初始化持久化 shell session（用于 /cmd 和 bash_run tool）
        self.shell_session = PersistentShellSession(initial_cwd=self.project_root)
        # 共享给 tools，让 Agent 调用 bash_run 时使用同一个 shell
        set_shared_session(self.shell_session, self.project_root)

        # 初始化命令处理器
        self._init_commands()

    def _init_commands(self):
        """初始化命令注册器（自动发现所有命令）"""
        self.command_registry = CommandRegistry(
            self.console,
            agent=self.agent,
            remote_commands=self.remote_commands,
            shell_session=self.shell_session,
            project_root=self.project_root,
        )

    def _setup_streaming_callbacks(self):
        """设置命令执行的流式输出回调"""
        if not is_feature_enabled("tool_execution.streaming_output"):
            return

        def on_stdout(line: str):
            """实时打印 stdout"""
            self.console.print(f"   [green]{line}[/green]")

        def on_stderr(line: str):
            """实时打印 stderr"""
            self.console.print(f"   [red]{line}[/red]")

        # 设置 agent tool executor 的流式回调
        if hasattr(self.agent, 'tool_executor') and hasattr(self.agent.tool_executor, 'set_streaming_callbacks'):
            self.agent.tool_executor.set_streaming_callbacks(on_stdout, on_stderr)

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

    def _confirm_tool_execution(self, tool_name: str, category: str, arguments: dict) -> ConfirmResult:
        """提示用户确认工具执行

        Args:
            tool_name: 要执行的工具名称
            category: 工具类别（filesystem, executor, analyzer）
            arguments: 工具参数

        Returns:
            ConfirmResult: 用户的选择和可选的拒绝原因
        """
        from .hyperlink import create_file_hyperlink

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
            # 根据 schema 格式处理路径参数（使用统一的 hyperlink 模块）
            if param_formats.get(key) == 'filepath':
                value_str = create_file_hyperlink(
                    path=str(value),
                    project_root=self.project_root,
                    path_utils=self.path_utils,
                    line=line_number
                )
                args_display.append(f"  • {key}: {value_str}")
            # 嵌套 dict 展开显示
            elif isinstance(value, dict) and value:
                args_display.append(f"  • {key}:")
                for sub_key, sub_value in value.items():
                    sub_value_str = str(sub_value)
                    if len(sub_value_str) > 50:
                        sub_value_str = sub_value_str[:47] + "..."
                    args_display.append(f"      - {sub_key}: {sub_value_str}")
            # list 展开显示
            elif isinstance(value, list) and value:
                if len(value) <= 3:
                    args_display.append(f"  • {key}: {value}")
                else:
                    args_display.append(f"  • {key}: [{len(value)} items]")
                    for item in value[:3]:
                        item_str = str(item)
                        if len(item_str) > 50:
                            item_str = item_str[:47] + "..."
                        args_display.append(f"      - {item_str}")
                    if len(value) > 3:
                        args_display.append(f"      - ... ({len(value) - 3} more)")
            else:
                value_str = str(value)
                # 截断其他长值
                if len(value_str) > 60:
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

        # 获取工具签名用于显示
        signature = self.agent.confirmation._get_tool_signature(tool_name, arguments)

        # 提示操作
        self.console.print("[bold]选择操作:[/bold]")
        self.console.print("  [green]1[/green] - 本次允许")
        self.console.print(f"  [blue]2[/blue] - 始终允许 [cyan]{signature}[/cyan]")
        self.console.print("  [red]3[/red] - 拒绝并停止")

        # 检查 stdin 是否可用（VSCode rerun 时可能不可用）
        if not sys.stdin.isatty():
            self.console.print("[yellow]⚠ 非交互模式，自动拒绝工具执行[/yellow]")
            return ConfirmResult(action=ConfirmAction.DENY, reason="非交互模式")

        while True:
            try:
                choice = input("> ").strip()

                if choice == '1':
                    self.console.print("[green]✓ 本次允许执行[/green]")
                    return ConfirmResult(action=ConfirmAction.ALLOW_ONCE)
                elif choice == '2':
                    self.console.print(f"[blue]✓ 始终允许: {signature}[/blue]")

                    # 对 git 工具额外提示危险参数
                    if tool_name == 'git':
                        args = arguments.get('args', {})
                        action = arguments.get('action', '')
                        if self.agent.confirmation.is_dangerous_git_operation(action, args):
                            self.console.print(
                                f"[yellow]  ⚠️  注意：危险参数仍需确认 (如 --force, --hard)[/yellow]"
                            )

                    return ConfirmResult(action=ConfirmAction.ALLOW_ALWAYS)
                elif choice == '3':
                    self.console.print("[yellow]请输入拒绝原因 (直接回车跳过):[/yellow]")
                    try:
                        reason = input("> ").strip()
                    except (KeyboardInterrupt, EOFError):
                        reason = ""
                    if reason:
                        self.console.print(f"[red]✗ 已拒绝: {reason}[/red]")
                    else:
                        self.console.print("[red]✗ 已拒绝[/red]")
                    return ConfirmResult(action=ConfirmAction.DENY, reason=reason if reason else None)
                else:
                    self.console.print("[yellow]无效选择，请输入 1、2 或 3[/yellow]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("[red]✗ 已取消[/red]")
                return ConfirmResult(action=ConfirmAction.DENY, reason="用户取消")

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

    def _get_ide_context(self) -> str:
        """获取 IDE 上下文（project root + cwd + 当前打开的文件信息 + system reminder）

        Returns:
            str: 包含 <system-reminder> 标签的上下文字符串
        """
        import os
        from backend.cli.system_reminder import get_system_reminder

        context_parts = []

        # 始终添加 project root 和当前工作目录
        context_parts.append(f'Project root: {self.project_root}')

        current_cwd = os.getcwd()
        context_parts.append(f'Current working directory: {current_cwd}')

        # 添加 system reminder 配置信息
        system_reminder = get_system_reminder()
        if system_reminder:
            context_parts.append(system_reminder)

        # 检查功能开关
        if is_feature_enabled("ide_integration.inject_active_file_context"):
            # 检查是否连接到 VSCode extension（动态检测）
            from backend.rpc.client import is_vscode_mode
            if is_vscode_mode():
                try:
                    from backend.tools import vscode

                    file_info = vscode.get_active_file()
                    file_path = file_info['path']

                    file_msg = f'User has "{file_path}" open in IDE. Use this context when the request appears related.'
                    context_parts.append(file_msg)
                except Exception:
                    pass  # IDE 文件信息获取失败，仅使用 project root + cwd

        # 组合上下文
        if context_parts:
            context_msg = '\n'.join(context_parts)
            return f"<system-reminder>\n{context_msg}\n</system-reminder>"

        return ""

    def run(self):
        """运行交互循环"""
        self.show_welcome()

        # 检查是否有可恢复的会话
        self._check_resume_session()

        first_prompt = True

        while True:
            try:
                # 显示状态行
                if not first_prompt:
                    self.console.print()  # 非首次时添加空行
                self.status_line.show()
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

                # 注入 IDE 上下文（当前打开的文件）
                ide_context = self._get_ide_context()
                if ide_context:
                    user_input_with_context = f"{ide_context}\n{user_input}"
                else:
                    user_input_with_context = user_input

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
                        response = self.agent.run(user_input_with_context, stream=True, on_chunk=on_chunk)

                        # 如果响应为空（完全流式输出），使用流式内容
                        if not response.strip() and streamed_content:
                            response = ''.join(streamed_content)
                    else:
                        # 非流式模式：等待完整响应
                        response = self.agent.run(user_input_with_context, stream=False)

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

        # 退出时自动保存会话
        self._auto_save_session()
        self.console.print("\n[blue]再见![/blue]")

    def _auto_save_session(self):
        """退出时自动保存会话"""
        if not self.agent.conversation_history:
            return

        try:
            from backend.session import get_session_manager
            session_manager = get_session_manager(self.project_root)

            # 获取当前角色
            role_id = "programmer"
            try:
                from backend.roles import get_role_manager
                role_manager = get_role_manager()
                role_id = role_manager.current_role_id
            except Exception:
                pass

            session_id = session_manager.save_session(
                conversation_history=self.agent.conversation_history,
                tool_calls=self.agent.tool_calls,
                active_files=self.agent.active_files,
                role_id=role_id
            )

            if session_id:
                self.console.print(f"[dim]会话已保存: {session_id}[/dim]")

            # 清理旧会话
            session_manager.clear_old_sessions(keep_count=20)
        except Exception as e:
            # 静默失败
            pass

    def _check_resume_session(self) -> bool:
        """
        检查是否有可恢复的会话

        Returns:
            True 如果成功恢复会话
        """
        try:
            from backend.session import get_session_manager
            session_manager = get_session_manager(self.project_root)

            latest = session_manager.get_latest_session()
            if not latest:
                return False

            # 检查是否是最近 24 小时内的会话
            from datetime import datetime, timedelta
            try:
                updated = datetime.fromisoformat(latest.updated_at)
                if datetime.now() - updated > timedelta(hours=24):
                    return False
            except:
                return False

            # 提示用户是否恢复
            import re
            summary = latest.summary or "无摘要"
            if len(summary) > 50:
                summary = summary[:47] + "..."

            self.console.print(f"\n[cyan]发现最近会话[/cyan]: {summary}")
            self.console.print(f"[dim]  会话 ID: {latest.id} | 消息数: {latest.message_count}[/dim]")

            # 检查 stdin 是否可用（VSCode rerun 时可能不可用）
            if not sys.stdin.isatty():
                self.console.print("[dim]非交互模式，跳过会话恢复提示[/dim]")
                return False

            try:
                from rich.prompt import Confirm
                if Confirm.ask("是否恢复该会话?", default=False, console=self.console):
                    # 恢复会话
                    session = session_manager.load_session(latest.id)
                    if session:
                        self.agent.conversation_history = session.conversation_history.copy()
                        self.agent.tool_calls = session.tool_calls.copy()
                        self.agent.active_files = session.active_files.copy()

                        # 恢复角色
                        try:
                            from backend.roles import get_role_manager
                            role_manager = get_role_manager()
                            if session.role_id and role_manager.get_role(session.role_id):
                                role_manager.switch_role(session.role_id)
                        except Exception:
                            pass

                        self.console.print(f"[green]✓ 已恢复会话[/green]")
                        return True
            except KeyboardInterrupt:
                pass

            return False
        except Exception:
            return False

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
            # 开始新的日志会话
            self.client.start_new_session()
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

        elif cmd == 'cmdremote':
            # 执行远程命令
            if len(args) > 0:
                cmd_to_run = ' '.join(args)
                self.remote_commands.execute_remote_command(cmd_to_run)
            else:
                self.console.print("[yellow]用法: /cmdremote <command>[/yellow]")
                self.console.print("示例: /cmdremote ps aux | grep ollama")

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
