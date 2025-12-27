# -*- coding: utf-8 -*-
"""
/session 命令 - 管理会话
"""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from datetime import datetime

from .base import BaseCommand


class SessionCommand(BaseCommand):
    """会话管理命令"""

    def __init__(self, console: Console, **dependencies):
        super().__init__(console, **dependencies)
        self.agent = dependencies.get('agent')

    @property
    def name(self) -> str:
        return "session"

    @property
    def aliases(self) -> List[str]:
        return ["resume", "sessions"]

    @property
    def description(self) -> str:
        return "管理和恢复会话"

    @property
    def category(self) -> str:
        return "session"

    @property
    def usage(self) -> str:
        return "/session [list|resume [#]|save|delete <#>]"

    def execute(self, args: List[str]) -> bool:
        """
        处理 /session 命令

        子命令:
        - /session 或 /session list - 列出最近的会话
        - /session resume [#] - 恢复会话（无序号则显示选择菜单）
        - /session save - 手动保存当前会话
        - /session delete <#> - 删除指定会话
        """
        from backend.session import get_session_manager

        project_root = self.dependencies.get('project_root', '.')
        session_manager = get_session_manager(project_root)

        if not args:
            # 默认显示会话列表
            self._show_sessions_list(session_manager)
            return True

        subcmd = args[0].lower()

        if subcmd == 'list':
            self._show_sessions_list(session_manager)

        elif subcmd == 'resume':
            session_id = args[1] if len(args) > 1 else None
            self._resume_session(session_manager, session_id)

        elif subcmd == 'save':
            self._save_current_session(session_manager)

        elif subcmd == 'delete':
            if len(args) > 1:
                self._delete_session(session_manager, args[1])
            else:
                self.console.print("[yellow]用法: /session delete <#>[/yellow]")

        else:
            # 尝试作为会话 ID 进行恢复
            self._resume_session(session_manager, subcmd)

        return True

    def _show_sessions_list(self, session_manager):
        """显示会话列表"""
        sessions = session_manager.list_sessions(limit=15)

        if not sessions:
            self.console.print("[dim]暂无保存的会话[/dim]")
            self.console.print("[dim]会话会在退出时自动保存，或使用 /session save 手动保存[/dim]")
            return

        table = Table(title="最近会话", show_header=True, header_style="bold cyan")
        table.add_column("#", style="bold cyan", width=3)
        table.add_column("时间", width=12)
        table.add_column("消息", width=5)
        table.add_column("摘要", max_width=50)

        for i, session in enumerate(sessions, 1):
            # 解析时间
            try:
                updated = datetime.fromisoformat(session.updated_at)
                time_str = updated.strftime('%m-%d %H:%M')
            except:
                time_str = session.updated_at[:16]

            # 生成更好的摘要：最后一条用户消息 + 最后一条助手消息
            summary = self._get_session_summary(session)

            table.add_row(
                str(i),
                time_str,
                str(session.message_count),
                summary
            )

        self.console.print(table)
        self.console.print("\n[dim]使用 /session resume <#> 恢复会话，如 /session resume 1[/dim]")

    def _get_session_summary(self, session) -> str:
        """获取会话摘要：最后一条用户提问 + 简短回答"""
        import re

        history = session.conversation_history
        if not history:
            return "空会话"

        # 找最后一条用户消息
        last_user_msg = None
        last_assistant_msg = None

        for msg in reversed(history):
            role = msg.get('role', '')
            content = msg.get('content', '')

            # 清理 system-reminder
            content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.DOTALL)
            content = content.strip()

            if not content:
                continue

            if role == 'user' and last_user_msg is None:
                last_user_msg = content
            elif role == 'assistant' and last_assistant_msg is None:
                last_assistant_msg = content

            if last_user_msg and last_assistant_msg:
                break

        # 构建摘要
        if last_user_msg:
            # 截断用户消息
            if len(last_user_msg) > 35:
                user_part = last_user_msg[:32] + '...'
            else:
                user_part = last_user_msg

            # 如果有助手回复，添加简短摘要
            if last_assistant_msg:
                # 取助手回复的前 15 个字符
                if len(last_assistant_msg) > 15:
                    assistant_part = last_assistant_msg[:12] + '...'
                else:
                    assistant_part = last_assistant_msg
                return f"{user_part} → {assistant_part}"
            else:
                return user_part

        return session.summary or "空会话"

    def _resume_session(self, session_manager, session_id: Optional[str]):
        """恢复会话"""
        sessions = session_manager.list_sessions(limit=15)

        if not sessions:
            self.console.print("[yellow]暂无可恢复的会话[/yellow]")
            return

        # 如果没有指定 ID，显示选择菜单
        if session_id is None:
            self._show_sessions_list(session_manager)
            self.console.print()

            try:
                choice = Prompt.ask(
                    "选择要恢复的会话",
                    default="1",
                    console=self.console
                )

                # 支持数字索引或会话 ID
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(sessions):
                        session_id = sessions[idx].id
                    else:
                        self.console.print(f"[red]无效的选择: {choice}[/red]")
                        return
                else:
                    session_id = choice

            except KeyboardInterrupt:
                self.console.print("\n[dim]已取消[/dim]")
                return

        # 加载会话
        session = session_manager.load_session(session_id)

        if session is None:
            # 尝试通过索引查找
            if session_id.isdigit():
                idx = int(session_id) - 1
                if 0 <= idx < len(sessions):
                    session = session_manager.load_session(sessions[idx].id)

        if session is None:
            self.console.print(f"[red]会话不存在: {session_id}[/red]")
            return

        # 恢复到 agent
        if self.agent:
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

            self.console.print(f"[green]✓ 已恢复会话: {session.id}[/green]")
            self.console.print(f"  [dim]消息数: {session.message_count} | 角色: {session.role_id}[/dim]")

            # 显示最后几条消息的摘要
            self._show_recent_messages(session.conversation_history)
        else:
            self.console.print("[red]错误: Agent 未初始化[/red]")

    def _show_recent_messages(self, history: List, count: int = 3):
        """显示最近的几条消息"""
        import re

        user_messages = []
        for msg in history:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.DOTALL)
                content = content.strip()
                if content:
                    user_messages.append(content)

        if user_messages:
            self.console.print("\n[dim]最近的提问:[/dim]")
            for msg in user_messages[-count:]:
                if len(msg) > 60:
                    msg = msg[:57] + '...'
                self.console.print(f"  [cyan]> {msg}[/cyan]")

    def _save_current_session(self, session_manager):
        """保存当前会话"""
        if not self.agent:
            self.console.print("[red]错误: Agent 未初始化[/red]")
            return

        if not self.agent.conversation_history:
            self.console.print("[yellow]当前会话为空，无需保存[/yellow]")
            return

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
            self.console.print(f"[green]✓ 会话已保存: {session_id}[/green]")
        else:
            self.console.print("[red]保存会话失败[/red]")

    def _delete_session(self, session_manager, session_id: str):
        """删除会话"""
        sessions = session_manager.list_sessions(limit=20)

        # 支持数字索引
        if session_id.isdigit():
            idx = int(session_id) - 1
            if 0 <= idx < len(sessions):
                session_id = sessions[idx].id
            else:
                self.console.print(f"[red]无效的索引: {session_id}[/red]")
                return

        if session_manager.delete_session(session_id):
            self.console.print(f"[green]✓ 已删除会话: {session_id}[/green]")
        else:
            self.console.print(f"[red]删除失败: {session_id}[/red]")
