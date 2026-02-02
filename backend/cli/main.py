# -*- coding: utf-8 -*-
"""
主 CLI 类 - 重构后的简化版本
"""

import os
import sys
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from ..agent.loop import AgentLoop
from ..agent.tools import ConfirmAction, ConfirmResult
from ..llm.client import OllamaClient
from ..remotectl.commands import RemoteCommands
from ..tools.executor_tools.bash_session import set_shared_session
from ..utils.feature import is_feature_enabled
from ..utils.i18n import I18n
from .ui import PrecheckRunner, StatusLine, ToolConfirmationUI
from ..utils.shell_session import PersistentShellSession
from .completers import ClaudeQwenCompleter, CombinedCompleter, FileNameCompleter, PathCompleter
from .command_registry import CommandRegistry
from .output_manager import ToolOutputManager
from .path_utils import PathUtils


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
            confirmation_callback=self._on_confirm,
            tool_output_callback=None  # 稍后设置
        )

        # 初始化路径工具
        self.path_utils = PathUtils(self.project_root)

        # 初始化工具确认 UI
        self.tool_confirmation_ui = ToolConfirmationUI(
            console=self.console,
            project_root=self.project_root,
            path_utils=self.path_utils,
            confirmation_manager=self.agent.confirmation
        )

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
        runner = PrecheckRunner(self.console)
        if not runner.run():
            sys.exit(1)

    def _on_confirm(self, tool_name: str, category: str, arguments: dict) -> ConfirmResult:
        """提示用户确认工具执行（代理到 ToolConfirmationUI）"""
        return self.tool_confirmation_ui.confirm(tool_name, category, arguments)

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
        except Exception:
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

                        self.console.print("[green]✓ 已恢复会话[/green]")
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
            # 清除 todo 列表
            from backend.todo import get_todo_manager
            get_todo_manager().clear()
            # 开始新的日志会话
            self.client.start_new_session()
            self.console.print("[green]已清除对话历史和任务列表[/green]")

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
    parser.add_argument('--version', '-v', action='version', version='1.0.0')
    parser.add_argument('--test', '-t', action='store_true',
                        help='运行 benchmark 测试')
    parser.add_argument('--model', '-m', help='指定模型（用于 --test）', default=None)

    args = parser.parse_args()

    # 运行 benchmark 测试
    if args.test:
        import os
        from tests.benchmark.run_benchmark import AgentBenchmark
        # 使用 fixtures 目录作为测试项目
        test_project = os.path.join(os.path.dirname(__file__), '../../tests/fixtures/sample-cpp')
        benchmark = AgentBenchmark(project_root=test_project, model=args.model or "glm-4.7-flash:latest")
        benchmark.run_all()
        return

    # Initialize and run CLI
    cli = CLI(project_root=args.root, skip_precheck=args.skip_precheck)

    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
