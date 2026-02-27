# -*- coding: utf-8 -*-
"""
CLI Diff Display - 在终端中用颜色显示编辑差异

在非 VSCode 环境下，作为 diff view 的替代方案。
参考 git diff 的呈现方式，带行号和背景色。
"""

import difflib
import os
import re
from typing import List, Optional, Tuple

from rich.console import Console
from rich.text import Text

# 最大显示行数（超过时截断，首尾各显示一半）
MAX_DIFF_LINES = 30

# @@ -old_start,old_count +new_start,new_count @@
_HUNK_RE = re.compile(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@')

# 缩进（与工具输出对齐）
_INDENT = "     "

# 行类型
_HEADER = "header"
_HUNK = "hunk"
_DEL = "del"
_ADD = "add"
_CTX = "ctx"


def _annotate_lines(
    diff_lines: List[str],
) -> List[Tuple[str, Optional[int], Optional[int], str]]:
    """为每行标注类型和行号。

    Returns:
        list of (type, old_num|None, new_num|None, content)
    """
    result = []
    old_num = 0
    new_num = 0

    for line in diff_lines:
        content = line.rstrip('\n')
        if line.startswith('---') or line.startswith('+++'):
            result.append((_HEADER, None, None, content))
        elif (m := _HUNK_RE.match(line)):
            old_num = int(m.group(1))
            new_num = int(m.group(2))
            result.append((_HUNK, None, None, content))
        elif line.startswith('-'):
            result.append((_DEL, old_num, None, content))
            old_num += 1
        elif line.startswith('+'):
            result.append((_ADD, None, new_num, content))
            new_num += 1
        else:
            result.append((_CTX, old_num, new_num, content))
            old_num += 1
            new_num += 1

    return result


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

    # 先标注行号，再截断（保持行号连续）
    annotated = _annotate_lines(diff_lines)

    omitted = 0
    if len(annotated) > MAX_DIFF_LINES:
        half = MAX_DIFF_LINES // 2
        head = annotated[:half]
        tail = annotated[-half:]
        omitted = len(annotated) - MAX_DIFF_LINES
        annotated = head + [None] + tail

    # 渲染
    output = Text()
    for entry in annotated:
        if entry is None:
            output.append(
                f"{_INDENT}           ... ({omitted} lines omitted) ...\n",
                style="dim italic",
            )
            continue

        kind, o_num, n_num, content = entry

        if kind == _HEADER:
            output.append(f"{_INDENT}{content}\n", style="bold")
        elif kind == _HUNK:
            output.append(f"{_INDENT}{content}\n", style="cyan")
        elif kind == _DEL:
            lo = f"{o_num:>4}" if o_num is not None else "    "
            output.append(f"{_INDENT}", style="dim")
            output.append(f"{lo}      │ ", style="dim red")
            output.append(f"{content}\n", style="red on #3c1f1f")
        elif kind == _ADD:
            ln = f"{n_num:>4}" if n_num is not None else "    "
            output.append(f"{_INDENT}", style="dim")
            output.append(f"     {ln} │ ", style="dim green")
            output.append(f"{content}\n", style="green on #1f3c1f")
        else:  # _CTX
            lo = f"{o_num:>4}" if o_num is not None else "    "
            ln = f"{n_num:>4}" if n_num is not None else "    "
            output.append(f"{_INDENT}", style="dim")
            output.append(f"{lo} {ln} │ ", style="dim")
            output.append(f"{content}\n", style="dim")

    console.print(output, end="")
