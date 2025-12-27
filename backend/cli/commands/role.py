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
        return "/role [list|switch <role_id>|info|create [role_id|all]]"

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

        elif subcmd == 'create':
            # 创建角色模型
            target = args[1] if len(args) > 1 else None
            self._create_role_model(role_manager, target)

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
        table.add_column("模型")
        table.add_column("状态")

        for role in roles:
            is_current = role.id == current_role_id
            status = "[green]● 当前[/green]" if is_current else ""
            name_style = "bold" if is_current else ""

            # 检查模型是否存在
            model_exists = role_manager.check_role_model_exists(role.id)
            model_status = "[green]✓[/green]" if model_exists else "[yellow]✗[/yellow]"

            table.add_row(
                role.id,
                role.icon,
                f"[{name_style}]{role.name}[/{name_style}]" if name_style else role.name,
                role.description[:30] + "..." if len(role.description) > 30 else role.description,
                model_status,
                status
            )

        self.console.print(table)
        self.console.print("\n[dim]使用 /role <id> 切换角色，/role create all 创建所有模型[/dim]")

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

        # 检查模型状态
        model_exists = role_manager.check_role_model_exists(role.id)
        model_status = "✓ 已创建" if model_exists else "✗ 未创建（使用 /role create 创建）"

        info_text = f"""
{role.icon} **{role.name}** ({role.name_en})

**描述**: {role.description}

**模型**: `{role.model}` - {model_status}

**基础模型**: `{role.base_model}`

**Modelfile**: `{role.modelfile or '无'}`

**工具类别**: {', '.join(role.tool_categories) or '无限制'}

**额外包含工具**: {', '.join(role.included_tools) or '无'}

**排除工具**: {', '.join(role.excluded_tools) or '无'}
"""
        from rich.markdown import Markdown
        self.console.print(Panel(
            Markdown(info_text),
            title=f"角色详情: {role.id}",
            border_style="blue"
        ))

    def _create_role_model(self, role_manager, target: str = None):
        """创建角色模型"""
        from rich.progress import Progress, SpinnerColumn, TextColumn

        if target == 'all':
            # 创建所有角色模型
            self.console.print("[cyan]正在创建所有角色模型...[/cyan]\n")
            results = role_manager.create_all_role_models()

            for role_id, (success, message) in results.items():
                role = role_manager.get_role(role_id)
                icon = role.icon if role else "🤖"
                if success:
                    self.console.print(f"  {icon} [green]✓[/green] {role_id}: {message}")
                else:
                    self.console.print(f"  {icon} [red]✗[/red] {role_id}: {message}")

            success_count = sum(1 for s, _ in results.values() if s)
            self.console.print(f"\n[dim]完成: {success_count}/{len(results)} 个模型[/dim]")

        elif target:
            # 创建指定角色模型
            role = role_manager.get_role(target)
            if not role:
                self.console.print(f"[red]错误: 未知角色 '{target}'[/red]")
                return

            self.console.print(f"[cyan]正在创建模型 {role.model}...[/cyan]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                progress.add_task(f"创建 {role.model}...", total=None)
                success, message = role_manager.create_role_model(target)

            if success:
                self.console.print(f"[green]✓ {message}[/green]")
            else:
                self.console.print(f"[red]✗ {message}[/red]")

        else:
            # 默认创建当前角色模型
            role = role_manager.current_role
            self.console.print(f"[cyan]正在创建当前角色模型 {role.model}...[/cyan]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                progress.add_task(f"创建 {role.model}...", total=None)
                success, message = role_manager.create_role_model()

            if success:
                self.console.print(f"[green]✓ {message}[/green]")
            else:
                self.console.print(f"[red]✗ {message}[/red]")
