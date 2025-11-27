# -*- coding: utf-8 -*-
"""
Compact 命令 - 上下文压缩
"""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base import Command


class CompactCommand(Command):
    """压缩上下文命令"""

    def __init__(self, console: Console, agent):
        """
        初始化压缩命令

        Args:
            console: Rich Console 实例
            agent: Agent 实例
        """
        super().__init__(console)
        self.agent = agent

    @property
    def name(self) -> str:
        return "compact"

    @property
    def description(self) -> str:
        return "智能压缩上下文"

    def execute(self, args: List[str]) -> bool:
        """
        处理 /compact 命令

        支持:
        - /compact         : 压缩到默认目标 (60%)
        - /compact 0.5     : 压缩到 50% of max tokens
        - /compact --info  : 显示压缩信息而不压缩
        """
        target_ratio = None
        show_info_only = False

        # 解析参数
        if len(args) > 0:
            arg = args[0]
            if arg == '--info' or arg == '-i':
                show_info_only = True
            else:
                try:
                    target_ratio = float(arg)
                    if target_ratio <= 0 or target_ratio >= 1:
                        self.console.print("[red]错误: 目标比例必须在 0 和 1 之间[/red]")
                        return True
                except ValueError:
                    self.console.print(f"[red]错误: 无效的比例值 '{arg}'[/red]")
                    return True

        # 获取当前状态
        token_counter = self.agent.token_counter
        current_total = token_counter.usage['total']
        max_tokens = token_counter.max_tokens
        current_pct = token_counter.get_usage_percentage()

        # 构建当前使用情况表格
        usage_table = Table(title="当前 Token 使用情况")
        usage_table.add_column("模块", style="cyan")
        usage_table.add_column("当前使用", justify="right")
        usage_table.add_column("预算", justify="right")
        usage_table.add_column("占比", justify="right")
        usage_table.add_column("状态")

        for category, tokens in token_counter.usage.items():
            if category == 'total':
                continue

            budget = token_counter.get_budget_for_category(category)
            pct = (tokens / budget * 100) if budget > 0 else 0
            status = "✓" if tokens <= budget else "⚠ 超预算"

            usage_table.add_row(
                category,
                f"{tokens:,}",
                f"{budget:,}",
                f"{pct:.1f}%",
                status
            )

        usage_table.add_row(
            "总计",
            f"{current_total:,}",
            f"{max_tokens:,}",
            f"{current_pct*100:.1f}%",
            "⚠ 需压缩" if current_pct > 0.85 else "✓"
        )

        self.console.print(usage_table)

        if show_info_only:
            # 显示压缩策略信息
            self.console.print("\n[cyan]压缩策略说明:[/cyan]")
            self.console.print(f"- 触发阈值: {token_counter.compression_config['trigger_threshold']*100:.0f}%")
            self.console.print(f"- 目标比例: {token_counter.compression_config['target_after_compress']*100:.0f}%")
            self.console.print(f"- 最小间隔: {token_counter.compression_config['min_interval']}秒")

            self.console.print("\n[cyan]各模块预算分配:[/cyan]")
            for category, ratio in token_counter.budgets.items():
                budget_tokens = int(max_tokens * ratio)
                self.console.print(f"  {category:20s}: {ratio*100:>5.1f}% ({budget_tokens:>8,} tokens)")
            return True

        # 计算压缩目标
        if target_ratio is None:
            target_ratio = token_counter.compression_config['target_after_compress']

        target_tokens = int(max_tokens * target_ratio)

        # 显示压缩计划
        self.console.print(f"\n[cyan]压缩目标:[/cyan] {current_total:,} → {target_tokens:,} tokens ({target_ratio*100:.0f}%)")
        self.console.print(f"[cyan]预计节省:[/cyan] {current_total - target_tokens:,} tokens")

        # 执行压缩
        self.console.print("\n[yellow]正在压缩上下文...[/yellow]")

        # 存储原始计数
        msg_count_before = len(self.agent.conversation_history)

        try:
            # 压缩
            self.agent._compress_context()

            # 获取新计数
            msg_count_after = len(self.agent.conversation_history)
            new_total = token_counter.usage['total']
            new_pct = token_counter.get_usage_percentage()

            # 显示结果
            self.console.print("\n[green]✓ 压缩完成[/green]\n")

            result_table = Table(title="压缩结果")
            result_table.add_column("项目", style="cyan")
            result_table.add_column("压缩前", justify="right")
            result_table.add_column("压缩后", justify="right")
            result_table.add_column("变化", justify="right")

            result_table.add_row(
                "消息数量",
                f"{msg_count_before}",
                f"{msg_count_after}",
                f"-{msg_count_before - msg_count_after}"
            )

            result_table.add_row(
                "总 Token 数",
                f"{current_total:,}",
                f"{new_total:,}",
                f"-{current_total - new_total:,} ({(1-new_total/current_total)*100:.1f}%)"
            )

            result_table.add_row(
                "使用率",
                f"{current_pct*100:.1f}%",
                f"{new_pct*100:.1f}%",
                f"-{(current_pct-new_pct)*100:.1f}%"
            )

            self.console.print(result_table)

            # 显示保留的信息
            self.console.print("\n[cyan]保留信息:[/cyan]")
            self.console.print(f"  - 活动文件: {len(self.agent.active_files)} 个")
            self.console.print(f"  - 项目结构: {self.agent.project_root}")
            self.console.print(f"  - 最近消息: {msg_count_after} 条")
            self.console.print(f"  - 工具定义: 已重新注入")

        except Exception as e:
            self.console.print(f"\n[red]✗ 压缩失败: {e}[/red]")

        return True
