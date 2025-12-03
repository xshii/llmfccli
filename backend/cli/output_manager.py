# -*- coding: utf-8 -*-
"""
工具输出管理模块

管理工具调用的输出显示和格式化
"""

import time
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.markup import render

from .path_utils import PathUtils
from .hyperlink import create_file_hyperlink, create_tool_hyperlink


class ToolOutputManager:
    """工具输出管理器"""

    def __init__(self, console: Console, path_utils: PathUtils, agent):
        """
        初始化输出管理器

        Args:
            console: Rich Console 实例
            path_utils: 路径工具实例
            agent: Agent 实例（用于获取 token 信息）
        """
        self.console = console
        self.path_utils = path_utils
        self.agent = agent

        # 当前命令跟踪
        self.current_command = ""
        self.command_start_time: Optional[float] = None
        self.tool_outputs: List[Dict[str, Any]] = []

    def add_tool_output(self, tool_name: str, output: str, args: Optional[Dict] = None):
        """添加工具输出用于显示

        Args:
            tool_name: 工具名称
            output: 输出内容
            args: 工具参数（可选）
        """
        # 特殊处理 assistant thinking 消息
        if tool_name == '__assistant_thinking__':
            # 显示思考消息
            thinking_line = Text()
            thinking_line.append(output, style="dim italic")
            self.console.print(thinking_line)
            return  # 不添加到 tool_outputs

        # 显示工具调用（持久化行，保留在屏幕上）
        tool_line = Text()
        tool_line.append("🔧 ", style="yellow")

        # 格式化工具调用
        formatted_call = self._format_tool_call(tool_name, args)
        # 解析 rich markup 并添加到 Text 对象
        tool_line.append_text(render(formatted_call))

        self.console.print(tool_line)

        self.tool_outputs.append({
            'tool': tool_name,
            'output': output,
            'args': args or {}
        })

    def _format_tool_call(self, tool_name: str, args: Optional[Dict] = None) -> str:
        """格式化工具调用为单行，带路径压缩

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            格式化的字符串（带 Rich markup）
        """
        # 工具名称带超链接（使用统一的 hyperlink 模块）
        parts = [create_tool_hyperlink(tool_name)]

        if args:
            # 已知的文件路径参数名
            PATH_PARAM_NAMES = {'path', 'file', 'file_path', 'filepath', 'source', 'target', 'destination', 'src', 'dst'}

            args_parts = []
            line_number = None  # 用于显示行号

            # 提取行号信息（如果存在）
            if 'line_range' in args and args['line_range']:
                # line_range 通常是 [start, end] 或 (start, end)
                line_range = args['line_range']
                if isinstance(line_range, (list, tuple)) and len(line_range) >= 1:
                    line_number = line_range[0]  # 使用起始行
            elif 'line' in args:
                line_number = args['line']

            for key, value in args.items():
                value_str = str(value)

                # 启发式判断：参数名包含路径关键词 且 值包含路径分隔符
                is_path_param = (
                    key.lower() in PATH_PARAM_NAMES and
                    ('/' in value_str or '\\' in value_str)
                )

                # 如果是路径参数，压缩并添加超链接（使用统一的 hyperlink 模块）
                if is_path_param:
                    value_str = create_file_hyperlink(
                        path=value_str,
                        project_root=self.path_utils.project_root,
                        path_utils=self.path_utils,
                        line=line_number
                    )
                # 截断其他长值
                elif len(value_str) > 50:
                    value_str = value_str[:47] + "..."

                args_parts.append(f"{key}={value_str}")

            parts.append(f"[dim]({', '.join(args_parts)})[/dim]")

        return " ".join(parts)

    def display_tool_outputs_summary(self):
        """显示所有工具输出的摘要"""
        if not self.tool_outputs:
            return

        elements = []

        # 计算执行时间
        elapsed_time = ""
        if self.command_start_time:
            elapsed = time.time() - self.command_start_time
            if elapsed < 60:
                elapsed_time = f" [dim]({elapsed:.1f}s)[/dim]"
            else:
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                elapsed_time = f" [dim]({minutes}m {seconds}s)[/dim]"

        # 获取 token 使用情况
        token_info = ""
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
            token_info = f" [dim][Tokens: {total_str}/{max_str} ({usage_pct:.0f}%)][/dim]"

        # 命令面板（顶部）
        command_text = Text()
        command_text.append("> ", style="cyan bold")
        command_text.append(self.current_command, style="cyan bold")

        command_panel = Panel(
            command_text,
            title=f"[bold blue]Command{elapsed_time}{token_info}[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
        elements.append(command_panel)

        # 工具输出
        for i, tool_data in enumerate(self.tool_outputs):
            tool_name = tool_data['tool']
            output = tool_data['output']
            args = tool_data['args']

            # 格式化参数显示
            args_str = ""
            if args:
                args_display = []
                for key, value in args.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    args_display.append(f"{key}={repr(value_str)}")
                args_str = f" ({', '.join(args_display)})"

            # 显示输出
            display_output = output
            if len(output) > 2000:
                display_output = output[:2000] + f"\n\n... ({len(output) - 2000} more chars)"

            title = f"[bold green]▼ {tool_name}[/bold green]"
            if args_str:
                title += f"[dim]{args_str}[/dim]"

            output_panel = Panel(
                display_output,
                title=title,
                border_style="green",
                padding=(0, 1)
            )
            elements.append(output_panel)

        # 打印所有元素
        for element in elements:
            self.console.print(element)

    def set_current_command(self, command: str):
        """设置当前命令

        Args:
            command: 用户输入的命令
        """
        self.current_command = command
        self.command_start_time = time.time()
        self.tool_outputs = []

    def clear(self):
        """清除工具输出"""
        self.tool_outputs = []
        self.current_command = ""
        self.command_start_time = None
