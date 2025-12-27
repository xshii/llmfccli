# -*- coding: utf-8 -*-
"""
Role 命令 - 角色切换管理

支持：
- 列出所有可用角色
- 切换到指定角色
- 显示当前角色信息
"""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base import Command
from backend.roles import get_role_manager


class RoleCommand(Command):
    """角色管理命令"""

    def __init__(self, console: Console, agent=None, **kwargs):
        """
        初始化角色命令

        Args:
            console: Rich Console 实例
            agent: AgentLoop 实例（用于切换后更新）
        """
        super().__init__(console)
        self.agent = agent

    @property
    def name(self) -> str:
        return "role"

    @property
    def aliases(self) -> List[str]:
        return ["r"]

    @property
    def description(self) -> str:
        return "切换 AI 助手角色"

    @property
    def category(self) -> str:
        return "agent"

    @property
    def usage(self) -> str:
        return "/role [list|switch <role_id>|info]"

    def execute(self, args: List[str]) -> bool:
        """
        处理 /role 命令

        子命令:
        - /role 或 /role list - 列出所有可用角色
        - /role switch <role_id> - 切换到指定角色
        - /role info - 显示当前角色详细信息
        - /role <role_id> - 快速切换（简写）
        """
        role_manager = get_role_manager()

        if len(args) == 0:
            # 无参数：显示角色列表和当前角色
            self._show_roles_list(role_manager)
            return True

        subcmd = args[0].lower()

        if subcmd == 'list':
            self._show_roles_list(role_manager)

        elif subcmd == 'switch':
            if len(args) < 2:
                self.console.print("[red]错误: 需要指定角色 ID[/red]")
                self.console.print("用法: /role switch <role_id>")
                self._show_roles_list(role_manager)
                return True
            self._switch_role(role_manager, args[1])

        elif subcmd == 'info':
            self._show_role_info(role_manager)

        elif subcmd == 'reload':
            # 重新加载角色配置
            role_manager.reload_config()
            self.console.print("[green]✓ 角色配置已重新加载[/green]")

        else:
            # 尝试作为角色 ID 进行快速切换
            if role_manager.get_role(subcmd):
                self._switch_role(role_manager, subcmd)
            else:
                self.console.print(f"[yellow]未知子命令或角色: {subcmd}[/yellow]")
                self.console.print("输入 /role 查看可用角色")

        return True

    def _show_roles_list(self, role_manager):
        """显示角色列表"""
        roles = role_manager.list_roles()
        current_role_id = role_manager.current_role_id

        table = Table(title="可用角色", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("图标")
        table.add_column("名称")
        table.add_column("描述")
        table.add_column("状态")

        for role in roles:
            is_current = role.id == current_role_id
            status = "[green]● 当前[/green]" if is_current else ""
            name_style = "bold" if is_current else ""

            table.add_row(
                role.id,
                role.icon,
                f"[{name_style}]{role.name}[/{name_style}]" if name_style else role.name,
                role.description[:40] + "..." if len(role.description) > 40 else role.description,
                status
            )

        self.console.print(table)
        self.console.print("\n[dim]使用 /role <id> 切换角色，如: /role knowledge_curator[/dim]")

    def _switch_role(self, role_manager, role_id: str):
        """切换角色"""
        old_role = role_manager.current_role

        if role_manager.switch_role(role_id):
            new_role = role_manager.current_role

            # 显示切换信息
            self.console.print(Panel(
                f"[green]✓ 角色已切换[/green]\n\n"
                f"从: {old_role.icon} {old_role.name}\n"
                f"到: {new_role.icon} {new_role.name}\n\n"
                f"[dim]模型: {new_role.model}[/dim]\n"
                f"[dim]工具类别: {', '.join(new_role.tool_categories)}[/dim]",
                title="角色切换",
                border_style="green"
            ))

            # 清除对话历史（角色切换后上下文不再适用）
            if self.agent:
                self.agent.conversation_history.clear()
                self.console.print("[dim]对话历史已清除，开始新的会话[/dim]")
        else:
            self.console.print(f"[red]错误: 未知角色 '{role_id}'[/red]")
            self._show_roles_list(role_manager)

    def _show_role_info(self, role_manager):
        """显示当前角色详细信息"""
        role = role_manager.current_role

        info_text = f"""
{role.icon} **{role.name}** ({role.name_en})

**描述**: {role.description}

**模型**: `{role.model}`

**工具类别**: {', '.join(role.tool_categories) or '无限制'}

**额外包含工具**: {', '.join(role.included_tools) or '无'}

**排除工具**: {', '.join(role.excluded_tools) or '无'}

**系统提示**:
```
{role.system_prompt[:500]}{'...' if len(role.system_prompt) > 500 else ''}
```
"""
        from rich.markdown import Markdown
        self.console.print(Panel(
            Markdown(info_text),
            title=f"角色详情: {role.id}",
            border_style="blue"
        ))
