# -*- coding: utf-8 -*-
"""
CLI Diff Display - 在终端中用颜色显示编辑差异

在非 VSCode 环境下，作为 diff view 的替代方案。
"""

import difflib
import os
from typing import Optional

from rich.console import Console
from rich.text import Text


def show_edit_diff(
    console: Console,
    old_str: str,
    new_str: str,
    file_path: Optional[str] = None,
    context_lines: int = 3,
):
    """在 CLI 中显示 edit_file 的差异

    Args:
        console: Rich Console 实例
        old_str: 被替换的原始字符串
        new_str: 替换后的字符串
        file_path: 文件路径（用于标题）
        context_lines: 上下文行数
    """
    old_lines = old_str.splitlines(keepends=True)
    new_lines = new_str.splitlines(keepends=True)

    # 确保最后一行有换行符（统一 diff 格式）
    if old_lines and not old_lines[-1].endswith('\n'):
        old_lines[-1] += '\n'
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'

    filename = os.path.basename(file_path) if file_path else "file"
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        n=context_lines,
    )

    diff_lines = list(diff)
    if not diff_lines:
        return

    output = Text()
    for line in diff_lines:
        line_stripped = line.rstrip('\n')
        if line.startswith('---') or line.startswith('+++'):
            output.append(line_stripped + '\n', style="bold")
        elif line.startswith('@@'):
            output.append(line_stripped + '\n', style="cyan")
        elif line.startswith('-'):
            output.append(line_stripped + '\n', style="red")
        elif line.startswith('+'):
            output.append(line_stripped + '\n', style="green")
        else:
            output.append(line_stripped + '\n', style="dim")

    console.print(output, end="")
