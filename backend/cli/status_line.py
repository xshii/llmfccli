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

    def __init__(self, console: Console, agent: "AgentLoop", client: "OllamaClient"):
        self.console = console
        self.agent = agent
        self.client = client

    def show(self):
        """显示状态行"""
        parts = [
            self._format_tokens(),
            self._format_ide_file(),
            self._format_conversation_file(),
        ]
        # 过滤掉 None
        parts = [p for p in parts if p]
        status = f"[dim]{' | '.join(parts)}[/dim]"
        self.console.print(status)

        # 显示 system reminder 信息（如果有）
        reminder = self._format_system_reminder()
        if reminder:
            self.console.print(f"[dim]{reminder}[/dim]")

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
        """格式化文件链接"""
        filename = os.path.basename(file_path)

        if line_info:
            # 带行号的链接
            line_anchor = line_info.split('-')[0]
            url = f"file://{file_path}#{line_anchor}"
            return f"[link={url}]{filename}:{line_info}[/link]"
        else:
            url = f"file://{file_path}"
            return f"[link={url}]{filename}[/link]"

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

        url = f"file://{os.path.abspath(file_path)}"
        return f"[link={url}]查看对话历史[/link]"

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

    # ========== System Reminder 部分 ==========

    def _format_system_reminder(self) -> Optional[str]:
        """格式化 system reminder 信息"""
        try:
            from backend.cli.system_reminder import get_system_reminder
            reminder = get_system_reminder()
            if reminder:
                # 将多行内容合并为单行显示
                lines = [line.strip() for line in reminder.split('\n') if line.strip()]
                return ' | '.join(lines)
        except Exception:
            pass
        return None
