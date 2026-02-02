# -*- coding: utf-8 -*-
"""
工具输出管理模块

管理工具调用的输出显示和格式化
"""

import time
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.markup import render
from rich.panel import Panel
from rich.text import Text

from .hyperlink import create_file_hyperlink, create_tool_hyperlink
from .path_utils import PathUtils


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

    def add_tool_output(self, tool_name: str, output: Union[Dict, str, Any], args: Optional[Dict] = None):
        """添加工具输出用于显示

        Args:
            tool_name: 工具名称
            output: 输出内容（dict 或 str）
            args: 工具参数（可选）
        """
        # 特殊处理 assistant thinking 消息
        if tool_name == '__assistant_thinking__':
            # 显示思考消息
            thinking_line = Text()
            thinking_line.append(str(output), style="dim italic")
            self.console.print(thinking_line)
            return  # 不添加到 tool_outputs

        # 特殊处理模型未使用工具的提示
        if tool_name == '__no_tool_calls__':
            warning_line = Text()
            warning_line.append(str(output), style="yellow")
            self.console.print(warning_line)
            return  # 不添加到 tool_outputs

        # 显示工具调用（持久化行，保留在屏幕上）
        tool_line = Text()
        tool_line.append("🔧 ", style="yellow")

        # 格式化工具调用
        formatted_call = self._format_tool_call(tool_name, args)
        # 解析 rich markup 并添加到 Text 对象
        tool_line.append_text(render(formatted_call))

        self.console.print(tool_line)

        # 显示执行结果（最多5行）
        self._display_result_lines(output)

        self.tool_outputs.append({
            'tool': tool_name,
            'output': output,
            'args': args or {}
        })

    def _display_result_lines(self, output: Union[Dict, str, Any], max_lines: int = 5):
        """显示工具执行结果（最多 max_lines 行）

        Args:
            output: 工具输出（dict 或 str）
            max_lines: 最大显示行数
        """
        MAX_LINE_LEN = 120

        # 提取显示文本和错误状态
        has_error = False
        display_text = ""

        if isinstance(output, dict):
            # 统一格式：通过 success/ok 判断
            has_error = not output.get('success', output.get('ok', True))

            # 统一使用 output 字段
            display_text = output.get('output', '')

            # 向后兼容：尝试其他可能的字段名
            if not display_text:
                if has_error:
                    display_text = output.get('error', output.get('stderr', ''))
                else:
                    display_text = output.get('stdout', output.get('content', ''))

            # 特殊处理 results 列表
            if not display_text and 'results' in output:
                results = output.get('results', [])
                if isinstance(results, list):
                    display_text = f"{len(results)} results"
        else:
            display_text = str(output)
            if 'error' in display_text.lower() or 'failed' in display_text.lower():
                has_error = True

        if not display_text:
            return

        # 截取前几行
        lines = str(display_text).strip().split('\n')
        color = "red" if has_error else "green"

        for i, line in enumerate(lines[:max_lines]):
            line = line.rstrip()
            if len(line) > MAX_LINE_LEN:
                line = line[:MAX_LINE_LEN - 3] + "..."

            result_line = Text()
            result_line.append("   ", style="dim")
            result_line.append(line, style=color)
            self.console.print(result_line)

        # 如果还有更多行
        if len(lines) > max_lines:
            more_line = Text()
            more_line.append("   ", style="dim")
            more_line.append(f"... (+{len(lines) - max_lines} lines)", style="dim")
            self.console.print(more_line)

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
