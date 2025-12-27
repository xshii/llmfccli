# -*- coding: utf-8 -*-
"""
Status Line - 状态行显示模块

显示 Token 使用情况、当前 IDE 文件、对话文件等信息
"""

import os
from typing import Optional, Tuple, TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from ..agent.loop import AgentLoop
    from ..llm.client import OllamaClient


class StatusLine:
    """状态行显示器"""

    def __init__(self, console: Console, agent: "AgentLoop", client: "OllamaClient", project_root: str = ""):
        self.console = console
        self.agent = agent
        self.client = client
        self.project_root = project_root or os.getcwd()

    def show(self):
        """显示状态行"""
        # 先显示 todo 进度（如果有）
        todo_line = self._format_todo_progress()
        if todo_line:
            self.console.print(todo_line)

        parts = [
            self._format_role(),
            self._format_tokens(),
            self._format_ide_file(),
            self._format_conversation_file(),
        ]
        # 过滤掉 None
        parts = [p for p in parts if p]
        status = f"[dim]{' | '.join(parts)}[/dim]"
        self.console.print(status)

    # ========== Todo 部分 ==========

    def _format_todo_progress(self) -> Optional[str]:
        """格式化 todo 进度显示"""
        try:
            from backend.todo import get_todo_manager
            manager = get_todo_manager()

            if manager.total_count == 0:
                return None

            # 进度条
            progress = manager.progress_percent
            bar_width = 20
            filled = int(bar_width * progress / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            # 当前任务
            current = manager.current_task
            current_text = ""
            if current:
                active = current.active_form or current.content
                if len(active) > 40:
                    active = active[:37] + "..."
                current_text = f" ▸ [cyan]{active}[/cyan]"

            return f"[dim][{bar}] {progress}% ({manager.completed_count}/{manager.total_count})[/dim]{current_text}"
        except Exception:
            return None

    # ========== 角色部分 ==========

    def _format_role(self) -> Optional[str]:
        """格式化当前角色"""
        try:
            from backend.roles import get_role_manager
            role_manager = get_role_manager()
            role = role_manager.current_role
            return f"{role.icon} {role.name}"
        except Exception:
            return None

    # ========== Token 部分 ==========

    def _format_tokens(self) -> Optional[str]:
        """格式化 token 使用情况"""
        if not hasattr(self.agent, 'token_counter'):
            return None

        total = self.agent.token_counter.usage.get('total', 0)
        max_tokens = self.agent.token_counter.max_tokens
        pct = (total / max_tokens * 100) if max_tokens > 0 else 0

        total_str = self._format_number(total)
        max_str = self._format_number(max_tokens)

        return f"Tokens: {total_str}/{max_str} ({pct:.0f}%)"

    def _format_number(self, n: int) -> str:
        """格式化数字（K 表示千）"""
        return f"{n/1000:.1f}K" if n >= 1000 else str(n)

    # ========== IDE 文件部分 ==========

    def _format_ide_file(self) -> str:
        """格式化 IDE 文件信息"""
        from backend.rpc.client import is_vscode_mode

        if not is_vscode_mode():
            return "[yellow]未连接 vscode-ext[/yellow]"

        info = self._get_ide_file_info()
        if not info:
            return "[yellow]无活动文件[/yellow]"

        file_path, line_info = info
        return self._format_file_link(file_path, line_info)

    def _format_file_link(self, file_path: str, line_info: Optional[str]) -> str:
        """格式化文件链接（只显示文件名）"""
        from backend.utils.feature import get_feature_value

        # 解析行号
        line_number = None
        if line_info:
            line_number = int(line_info.split('-')[0])

        # 获取文件名
        filename = os.path.basename(file_path)
        abs_path = os.path.abspath(file_path) if not os.path.isabs(file_path) else file_path

        # 获取协议配置
        protocol = get_feature_value("cli_output.hyperlink_protocol.protocol", "file")
        show_line = get_feature_value("cli_output.hyperlink_protocol.show_line_number", True)

        # 构建显示文本
        display = filename
        if show_line and line_number:
            display += f":{line_number}"

        if protocol == "none":
            return display

        elif protocol == "vscode":
            uri = f"vscode://file{abs_path}"
            if line_number:
                uri += f":{line_number}"
            return f"[link={uri}]{display}[/link]"

        else:
            # file:// 协议
            uri = f"file://{abs_path}"
            return f"[link={uri}]{display}[/link]"

    def _get_ide_file_info(self) -> Optional[Tuple[str, Optional[str]]]:
        """获取 IDE 文件信息 (路径, 行号)"""
        try:
            from backend.tools import vscode

            file_info = vscode.get_active_file()
            file_path = file_info.get('path')
            if not file_path:
                return None

            line_info = self._get_line_info()
            return (file_path, line_info)
        except Exception:
            return None

    def _get_line_info(self) -> Optional[str]:
        """获取当前行号或选中区域"""
        try:
            from backend.tools import vscode

            selection = vscode.get_selection()
            start = selection['start']['line'] + 1  # 转为 1-based
            end = selection['end']['line'] + 1

            if start == end:
                return str(start)
            return f"{start}-{end}"
        except Exception:
            return None

    # ========== 对话文件部分 ==========

    def _format_conversation_file(self) -> str:
        """格式化对话文件链接"""
        file_path = self._get_conversation_file()
        if not file_path:
            return "[dim]暂无历史对话[/dim]"

        # 直接使用文件路径创建超链接，显示文字为"查看历史会话"
        from backend.utils.feature import get_feature_value
        protocol = get_feature_value("cli_output.hyperlink_protocol.protocol", "file")
        abs_path = os.path.abspath(file_path)

        if protocol == "none":
            return "查看历史会话"
        elif protocol == "vscode":
            uri = f"vscode://file{abs_path}"
        else:
            uri = f"file://{abs_path}"

        return f"[link={uri}]查看历史会话[/link]"

    def _get_conversation_file(self) -> Optional[str]:
        """获取对话文件路径"""
        # 优先使用 conversation 文件
        if hasattr(self.client, 'last_conversation_file') and self.client.last_conversation_file:
            path = self.client.last_conversation_file
            if os.path.exists(path):
                return path

        # 回退到 request 文件
        if hasattr(self.client, 'last_request_file') and self.client.last_request_file:
            path = self.client.last_request_file
            if os.path.exists(path):
                return path

        return None
