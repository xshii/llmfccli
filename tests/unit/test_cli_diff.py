# -*- coding: utf-8 -*-
"""
Unit tests for CLI diff preview (backend/cli/cli_diff.py)

Tests:
1. _annotate_lines: 行类型标注 + 行号计算
2. show_edit_diff: 基本替换、纯新增、纯删除
3. 截断逻辑: 超过 MAX_DIFF_LINES 时截断
4. 空 diff: old_str == new_str 时无输出
5. 多 hunk: 不连续修改产生多个 hunk
6. 无尾换行: 最后一行无 \n 时正确处理
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from io import StringIO
from rich.console import Console

from backend.cli.cli_diff import (
    _annotate_lines,
    show_edit_diff,
    MAX_DIFF_LINES,
    _HEADER,
    _HUNK,
    _DEL,
    _ADD,
    _CTX,
)


def make_console():
    """创建一个捕获输出的 Console（无颜色）"""
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, no_color=True, width=120)
    return console, buf


# ─── _annotate_lines ────────────────────────────────────────────

def test_annotate_header():
    """--- 和 +++ 行应标注为 header"""
    lines = [
        "--- a/foo.cpp\n",
        "+++ b/foo.cpp\n",
    ]
    result = _annotate_lines(lines)
    assert len(result) == 2
    assert result[0][0] == _HEADER
    assert result[1][0] == _HEADER
    assert result[0][1] is None  # header 无行号

    print("✓ test_annotate_header PASSED")


def test_annotate_hunk():
    """@@ 行应标注为 hunk，并正确解析起始行号"""
    lines = ["@@ -10,3 +20,4 @@\n"]
    result = _annotate_lines(lines)
    assert result[0][0] == _HUNK
    assert result[0][1] is None  # hunk 本身无行号

    print("✓ test_annotate_hunk PASSED")


def test_annotate_del_add_ctx():
    """删除、新增、上下文行应正确标注类型和行号"""
    lines = [
        "@@ -1,3 +1,3 @@\n",
        " context line\n",      # ctx: old=1, new=1
        "-deleted line\n",      # del: old=2
        "+added line\n",        # add: new=2
        " another context\n",   # ctx: old=3, new=3
    ]
    result = _annotate_lines(lines)

    # hunk
    assert result[0][0] == _HUNK

    # context line
    assert result[1] == (_CTX, 1, 1, " context line")

    # deleted
    assert result[2][0] == _DEL
    assert result[2][1] == 2   # old_num
    assert result[2][2] is None  # new_num

    # added
    assert result[3][0] == _ADD
    assert result[3][1] is None  # old_num
    assert result[3][2] == 2    # new_num

    # second context
    assert result[4] == (_CTX, 3, 3, " another context")

    print("✓ test_annotate_del_add_ctx PASSED")


def test_annotate_consecutive_line_numbers():
    """连续删除/新增行号应递增"""
    lines = [
        "@@ -5,4 +5,2 @@\n",
        "-line A\n",    # old=5
        "-line B\n",    # old=6
        "-line C\n",    # old=7
        "+line X\n",    # new=5
    ]
    result = _annotate_lines(lines)
    # skip hunk
    assert result[1][1] == 5   # first del old_num
    assert result[2][1] == 6
    assert result[3][1] == 7
    assert result[4][2] == 5   # first add new_num

    print("✓ test_annotate_consecutive_line_numbers PASSED")


# ─── show_edit_diff ─────────────────────────────────────────────

def test_basic_replace():
    """基本替换：输出应包含删除行和新增行"""
    console, buf = make_console()
    show_edit_diff(console, "old line", "new line", file_path="test.cpp")
    output = buf.getvalue()

    assert "-old line" in output
    assert "+new line" in output
    assert "a/test.cpp" in output
    assert "b/test.cpp" in output

    print("✓ test_basic_replace PASSED")


def test_pure_addition():
    """纯新增（old_str 为空）：只有 + 行"""
    console, buf = make_console()
    show_edit_diff(console, "", "new content\nline 2\n", file_path="new.cpp")
    output = buf.getvalue()

    assert "+new content" in output
    assert "+line 2" in output
    # 不应有 - 行（除了 header ---）
    lines = output.split('\n')
    del_lines = [l for l in lines if l.strip().startswith('-') and not l.strip().startswith('---')]
    assert len(del_lines) == 0

    print("✓ test_pure_addition PASSED")


def test_pure_deletion():
    """纯删除（new_str 为空）：只有 - 行"""
    console, buf = make_console()
    show_edit_diff(console, "line to delete\n", "", file_path="del.cpp")
    output = buf.getvalue()

    assert "-line to delete" in output

    print("✓ test_pure_deletion PASSED")


def test_no_diff():
    """old_str == new_str 时不应有输出"""
    console, buf = make_console()
    show_edit_diff(console, "same content", "same content")
    output = buf.getvalue()

    assert output.strip() == ""

    print("✓ test_no_diff PASSED")


def test_multiline_replace():
    """多行替换：行号连续正确"""
    old = "line1\nline2\nline3\n"
    new = "LINE1\nLINE2\nLINE3\n"
    console, buf = make_console()
    show_edit_diff(console, old, new, file_path="multi.cpp")
    output = buf.getvalue()

    assert "-line1" in output
    assert "+LINE1" in output
    assert "-line3" in output
    assert "+LINE3" in output

    print("✓ test_multiline_replace PASSED")


def test_truncation():
    """超过 MAX_DIFF_LINES 时应截断并显示 omitted 提示"""
    # 生成大量差异行
    old = "\n".join(f"old line {i}" for i in range(100)) + "\n"
    new = "\n".join(f"new line {i}" for i in range(100)) + "\n"

    console, buf = make_console()
    show_edit_diff(console, old, new, file_path="big.cpp")
    output = buf.getvalue()

    assert "omitted" in output

    print("✓ test_truncation PASSED")


def test_no_trailing_newline():
    """最后一行无换行符时不应报错"""
    console, buf = make_console()
    show_edit_diff(console, "no newline at end", "replaced no newline")
    output = buf.getvalue()

    assert "-no newline at end" in output
    assert "+replaced no newline" in output

    print("✓ test_no_trailing_newline PASSED")


def test_file_path_in_header():
    """file_path 应出现在 diff header 中"""
    console, buf = make_console()
    show_edit_diff(console, "a", "b", file_path="/path/to/handler.cpp")
    output = buf.getvalue()

    assert "a/handler.cpp" in output
    assert "b/handler.cpp" in output

    print("✓ test_file_path_in_header PASSED")


def test_no_file_path_defaults():
    """不传 file_path 时默认用 'file'"""
    console, buf = make_console()
    show_edit_diff(console, "x", "y")
    output = buf.getvalue()

    assert "a/file" in output
    assert "b/file" in output

    print("✓ test_no_file_path_defaults PASSED")


def test_context_lines():
    """context_lines 参数控制上下文行数"""
    old = "ctx1\nctx2\nctx3\nOLD\nctx4\nctx5\nctx6\n"
    new = "ctx1\nctx2\nctx3\nNEW\nctx4\nctx5\nctx6\n"

    # context_lines=1: 只显示修改点前后各 1 行
    console, buf = make_console()
    show_edit_diff(console, old, new, context_lines=1)
    output = buf.getvalue()

    assert "-OLD" in output
    assert "+NEW" in output
    # ctx3 和 ctx4 应在上下文中，ctx1/ctx2/ctx5/ctx6 不应出现
    lines = output.split('\n')
    content_lines = [l.strip() for l in lines]
    assert any("ctx3" in l for l in content_lines)
    assert any("ctx4" in l for l in content_lines)
    assert not any("ctx1" in l for l in content_lines)
    assert not any("ctx6" in l for l in content_lines)

    print("✓ test_context_lines PASSED")


if __name__ == '__main__':
    print("=" * 60)
    print("测试 CLI Diff Preview (backend/cli/cli_diff.py)")
    print("=" * 60)
    print()

    # _annotate_lines tests
    test_annotate_header()
    test_annotate_hunk()
    test_annotate_del_add_ctx()
    test_annotate_consecutive_line_numbers()

    # show_edit_diff tests
    test_basic_replace()
    test_pure_addition()
    test_pure_deletion()
    test_no_diff()
    test_multiline_replace()
    test_truncation()
    test_no_trailing_newline()
    test_file_path_in_header()
    test_no_file_path_defaults()
    test_context_lines()

    print()
    print("=" * 60)
    print("✅ 所有 CLI Diff 测试通过！")
    print("=" * 60)
