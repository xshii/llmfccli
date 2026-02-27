# -*- coding: utf-8 -*-
"""
ToolConfirmationUI - 工具执行确认界面

从 CLI 类提取的工具确认 UI 逻辑，负责：
1. 格式化显示工具参数
2. 提示用户确认
3. 处理用户选择
"""

import sys
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

from backend.agent.tools import ConfirmAction, ConfirmResult
from backend.constants import Limit


class ToolConfirmationUI:
    """工具执行确认界面"""

    def __init__(
        self,
        console: Console,
        project_root: str,
        path_utils: Any,
        confirmation_manager: Any
    ):
        """
        初始化工具确认界面

        Args:
            console: Rich Console 实例
            project_root: 项目根目录
            path_utils: PathUtils 实例
            confirmation_manager: ToolConfirmation 实例
        """
        self.console = console
        self.project_root = project_root
        self.path_utils = path_utils
        self.confirmation = confirmation_manager

    def confirm(
        self,
        tool_name: str,
        category: str,
        arguments: Dict[str, Any]
    ) -> ConfirmResult:
        """
        提示用户确认工具执行

        Args:
            tool_name: 要执行的工具名称
            category: 工具类别（filesystem, executor, analyzer）
            arguments: 工具参数

        Returns:
            ConfirmResult: 用户的选择和可选的拒绝原因
        """
        # 格式化参数显示
        args_text = self._format_arguments(tool_name, arguments)

        # 显示确认面板
        self._show_confirmation_panel(tool_name, category, arguments, args_text)

        # edit_file / create_file: 在确认前显示 diff 预览
        if tool_name in ('edit_file', 'create_file'):
            self._show_diff_preview(tool_name, arguments)

        # 获取工具签名用于显示
        signature = self.confirmation._get_signature(tool_name, arguments)

        # 提示操作选项
        self._show_options(signature)

        # 检查 stdin 是否可用
        if not sys.stdin.isatty():
            self.console.print("[yellow]非交互模式，自动拒绝工具执行[/yellow]")
            return ConfirmResult(action=ConfirmAction.DENY, reason="非交互模式")

        # 获取用户选择
        return self._get_user_choice(tool_name, arguments, signature)

    def _show_diff_preview(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """在确认前显示 CLI diff 预览"""
        from backend.cli.cli_diff import show_edit_diff

        file_path = arguments.get('path', '')

        if tool_name == 'edit_file':
            old_str = arguments.get('old_str', '')
            new_str = arguments.get('new_str', '')
            if old_str or new_str:
                show_edit_diff(self.console, old_str, new_str, file_path=file_path)
        elif tool_name == 'create_file':
            content = arguments.get('content', '')
            if content:
                show_edit_diff(self.console, '', content, file_path=file_path)

    def _format_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """格式化参数显示"""
        from backend.agent.tools import registry
        from backend.cli.hyperlink import create_file_hyperlink

        # 获取工具 schema 以检查参数格式
        tool_metadata = registry.get_tool_metadata(tool_name)
        param_formats = {}

        if tool_metadata:
            properties = (tool_metadata.get('schema', {})
                         .get('function', {})
                         .get('parameters', {})
                         .get('properties', {}))
            for param_name, param_info in properties.items():
                if param_info.get('format') == 'filepath':
                    param_formats[param_name] = 'filepath'

        # 提取行号信息
        line_number = self._extract_line_number(arguments)

        # 格式化各参数
        args_display = []
        max_len = Limit.STRING_PREVIEW_LENGTH

        for key, value in arguments.items():
            if param_formats.get(key) == 'filepath':
                # 文件路径参数，创建超链接
                value_str = create_file_hyperlink(
                    path=str(value),
                    project_root=self.project_root,
                    path_utils=self.path_utils,
                    line=line_number
                )
                args_display.append(f"  {key}: {value_str}")
            elif isinstance(value, dict) and value:
                # 嵌套 dict 展开显示
                args_display.append(f"  {key}:")
                for sub_key, sub_value in value.items():
                    sub_value_str = self._truncate(str(sub_value), max_len)
                    args_display.append(f"      - {sub_key}: {sub_value_str}")
            elif isinstance(value, list) and value:
                # list 展开显示
                if len(value) <= 3:
                    args_display.append(f"  {key}: {value}")
                else:
                    args_display.append(f"  {key}: [{len(value)} items]")
                    for item in value[:3]:
                        item_str = self._truncate(str(item), max_len)
                        args_display.append(f"      - {item_str}")
                    if len(value) > 3:
                        args_display.append(f"      - ... ({len(value) - 3} more)")
            else:
                # 其他类型
                value_str = self._truncate(str(value), 60)
                args_display.append(f"  {key}: {value_str}")

        return "\n".join(args_display) if args_display else "  (无参数)"

    def _extract_line_number(self, arguments: Dict[str, Any]) -> Optional[int]:
        """从参数中提取行号"""
        if 'line_range' in arguments and arguments['line_range']:
            line_range = arguments['line_range']
            if isinstance(line_range, (tuple, list)) and len(line_range) >= 1:
                return line_range[0]
        elif 'line' in arguments:
            return arguments.get('line')
        elif 'start_line' in arguments:
            return arguments.get('start_line')
        return None

    def _truncate(self, text: str, max_len: int) -> str:
        """截断过长文本"""
        if len(text) > max_len:
            return text[:max_len - 3] + "..."
        return text

    def _show_confirmation_panel(
        self,
        tool_name: str,
        category: str,
        arguments: Dict[str, Any],
        args_text: str
    ) -> None:
        """显示确认面板"""
        if tool_name == 'bash_run':
            # 特殊处理 bash_run - 高亮命令
            command = arguments.get('command', '')
            self.console.print(Panel(
                f"[yellow]工具执行确认[/yellow] - 工具: [bold]{tool_name}[/bold] | "
                f"类别: [dim]{category}[/dim]\n"
                f"命令: [cyan]{command}[/cyan] | 参数:\n{args_text}",
                title="需要确认",
                border_style="yellow"
            ))
        else:
            self.console.print(Panel(
                f"[yellow]工具执行确认[/yellow] - 工具: [bold]{tool_name}[/bold] | "
                f"类别: [dim]{category}[/dim] | 参数:\n{args_text}",
                title="需要确认",
                border_style="yellow"
            ))

    def _show_options(self, signature: str) -> None:
        """显示操作选项"""
        self.console.print("[bold]选择操作:[/bold]")
        self.console.print("  [green]1[/green] - 本次允许")
        self.console.print(f"  [blue]2[/blue] - 始终允许 [cyan]{signature}[/cyan]")
        self.console.print("  [red]3[/red] - 拒绝并停止")

    def _get_user_choice(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        signature: str
    ) -> ConfirmResult:
        """获取用户选择"""
        while True:
            try:
                choice = input("> ").strip()

                if choice == '1':
                    self.console.print("[green]本次允许执行[/green]")
                    return ConfirmResult(action=ConfirmAction.ALLOW_ONCE)

                elif choice == '2':
                    self.console.print(f"[blue]始终允许: {signature}[/blue]")
                    self._warn_dangerous_git(tool_name, arguments)
                    return ConfirmResult(action=ConfirmAction.ALLOW_ALWAYS)

                elif choice == '3':
                    return self._handle_deny()

                else:
                    self.console.print("[yellow]无效选择，请输入 1、2 或 3[/yellow]")

            except (KeyboardInterrupt, EOFError):
                self.console.print("[red]已取消[/red]")
                return ConfirmResult(action=ConfirmAction.DENY, reason="用户取消")

    def _warn_dangerous_git(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """警告危险的 git 操作"""
        if tool_name == 'git':
            args = arguments.get('args', {})
            action = arguments.get('action', '')
            if self.confirmation.is_dangerous_git_operation(action, args):
                self.console.print(
                    "[yellow]  注意：危险参数仍需确认 (如 --force, --hard)[/yellow]"
                )

    def _handle_deny(self) -> ConfirmResult:
        """处理拒绝选择"""
        self.console.print("[yellow]请输入拒绝原因 (直接回车跳过):[/yellow]")
        try:
            reason = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            reason = ""

        if reason:
            self.console.print(f"[red]已拒绝: {reason}[/red]")
        else:
            self.console.print("[red]已拒绝[/red]")

        return ConfirmResult(action=ConfirmAction.DENY, reason=reason if reason else None)
