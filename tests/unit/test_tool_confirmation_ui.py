#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ToolConfirmationUI 单元测试

测试 UI 层的工具确认逻辑，确保与 ToolConfirmation 类正确集成。
"""

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console

from backend.agent.tools import ConfirmAction, ConfirmResult
from backend.agent.tools.confirmation import ToolConfirmation
from backend.agent.tools.registry import ToolRegistry
from backend.cli.path_utils import PathUtils
from backend.cli.ui.tool_confirmation_ui import ToolConfirmationUI


class TestToolConfirmationUI:
    """ToolConfirmationUI 测试类"""

    def setup_method(self):
        """每个测试前的设置"""
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        self.console = Console(file=StringIO(), force_terminal=True)
        self.path_utils = PathUtils(self.project_root)
        self.registry = ToolRegistry(project_root=self.project_root)
        self.confirmation = ToolConfirmation(tool_registry=self.registry)
        self.ui = ToolConfirmationUI(
            console=self.console,
            project_root=self.project_root,
            path_utils=self.path_utils,
            confirmation_manager=self.confirmation
        )


def test_extract_line_number_from_line_range():
    """测试从 line_range 提取行号"""
    ui = create_test_ui()

    # tuple 格式
    result = ui._extract_line_number({'line_range': (10, 50)})
    assert result == 10, f"Expected 10, got {result}"

    # list 格式
    result = ui._extract_line_number({'line_range': [20, 100]})
    assert result == 20, f"Expected 20, got {result}"

    print("✓ test_extract_line_number_from_line_range PASSED")


def test_extract_line_number_from_line():
    """测试从 line 参数提取行号"""
    ui = create_test_ui()

    result = ui._extract_line_number({'line': 42})
    assert result == 42, f"Expected 42, got {result}"

    print("✓ test_extract_line_number_from_line PASSED")


def test_extract_line_number_from_start_line():
    """测试从 start_line 参数提取行号"""
    ui = create_test_ui()

    result = ui._extract_line_number({'start_line': 100})
    assert result == 100, f"Expected 100, got {result}"

    print("✓ test_extract_line_number_from_start_line PASSED")


def test_extract_line_number_none():
    """测试无行号参数时返回 None"""
    ui = create_test_ui()

    result = ui._extract_line_number({'path': '/some/file.py'})
    assert result is None, f"Expected None, got {result}"

    result = ui._extract_line_number({})
    assert result is None, f"Expected None, got {result}"

    print("✓ test_extract_line_number_none PASSED")


def test_truncate_short_text():
    """测试短文本不截断"""
    ui = create_test_ui()

    result = ui._truncate("hello", 10)
    assert result == "hello", f"Expected 'hello', got '{result}'"

    print("✓ test_truncate_short_text PASSED")


def test_truncate_long_text():
    """测试长文本截断"""
    ui = create_test_ui()

    result = ui._truncate("hello world this is a long text", 10)
    assert result == "hello w...", f"Expected 'hello w...', got '{result}'"
    assert len(result) == 10, f"Expected length 10, got {len(result)}"

    print("✓ test_truncate_long_text PASSED")


def test_truncate_exact_length():
    """测试刚好等于最大长度的文本"""
    ui = create_test_ui()

    result = ui._truncate("1234567890", 10)
    assert result == "1234567890", f"Expected '1234567890', got '{result}'"

    print("✓ test_truncate_exact_length PASSED")


def test_format_arguments_empty():
    """测试空参数格式化"""
    ui = create_test_ui()

    result = ui._format_arguments('view_file', {})
    assert result == "  (无参数)", f"Expected '  (无参数)', got '{result}'"

    print("✓ test_format_arguments_empty PASSED")


def test_format_arguments_simple():
    """测试简单参数格式化"""
    ui = create_test_ui()

    result = ui._format_arguments('bash_run', {'command': 'ls -la'})
    assert 'command' in result
    assert 'ls -la' in result

    print("✓ test_format_arguments_simple PASSED")


def test_format_arguments_list():
    """测试列表参数格式化"""
    ui = create_test_ui()

    # 短列表
    result = ui._format_arguments('test_tool', {'items': [1, 2, 3]})
    assert 'items' in result
    assert '[1, 2, 3]' in result

    # 长列表
    result = ui._format_arguments('test_tool', {'items': [1, 2, 3, 4, 5, 6]})
    assert 'items' in result
    assert '6 items' in result

    print("✓ test_format_arguments_list PASSED")


def test_format_arguments_dict():
    """测试字典参数格式化"""
    ui = create_test_ui()

    result = ui._format_arguments('test_tool', {'config': {'key1': 'value1', 'key2': 'value2'}})
    assert 'config' in result
    assert 'key1' in result
    assert 'value1' in result

    print("✓ test_format_arguments_dict PASSED")


def test_get_signature_integration():
    """测试 UI 与 ToolConfirmation._get_signature 的集成"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    registry = ToolRegistry(project_root=project_root)
    confirmation = ToolConfirmation(tool_registry=registry)

    # 测试 _get_signature 方法存在且可调用
    assert hasattr(confirmation, '_get_signature'), "ToolConfirmation should have _get_signature method"

    # 测试调用不抛异常
    signature = confirmation._get_signature('view_file', {'path': '/test/file.py'})
    assert signature is not None
    assert isinstance(signature, str)

    # 测试 bash_run 的签名包含命令
    signature = confirmation._get_signature('bash_run', {'command': 'ls -la'})
    assert 'bash_run' in signature

    print("✓ test_get_signature_integration PASSED")


def test_confirm_non_interactive_mode():
    """测试非交互模式下自动拒绝"""
    ui = create_test_ui()

    # Mock stdin.isatty() 返回 False
    with patch('sys.stdin') as mock_stdin:
        mock_stdin.isatty.return_value = False

        result = ui.confirm('view_file', 'filesystem', {'path': '/test/file.py'})

        assert result.action == ConfirmAction.DENY
        assert result.reason == "非交互模式"

    print("✓ test_confirm_non_interactive_mode PASSED")


def test_confirm_calls_get_signature():
    """测试 confirm 方法正确调用 _get_signature"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    console = Console(file=StringIO(), force_terminal=True)
    path_utils = PathUtils(project_root)
    registry = ToolRegistry(project_root=project_root)
    confirmation = ToolConfirmation(tool_registry=registry)

    # Mock _get_signature 方法
    original_get_signature = confirmation._get_signature
    call_count = [0]

    def mock_get_signature(tool_name, arguments):
        call_count[0] += 1
        return original_get_signature(tool_name, arguments)

    confirmation._get_signature = mock_get_signature

    ui = ToolConfirmationUI(
        console=console,
        project_root=project_root,
        path_utils=path_utils,
        confirmation_manager=confirmation
    )

    # 在非交互模式下调用 confirm
    with patch('sys.stdin') as mock_stdin:
        mock_stdin.isatty.return_value = False
        ui.confirm('view_file', 'filesystem', {'path': '/test/file.py'})

    # 验证 _get_signature 被调用
    assert call_count[0] == 1, f"Expected _get_signature to be called once, but was called {call_count[0]} times"

    print("✓ test_confirm_calls_get_signature PASSED")


def test_show_options():
    """测试选项显示"""
    ui = create_test_ui()

    # 调用 _show_options
    ui._show_options("view_file")

    # 检查输出包含选项
    output = ui.console.file.getvalue()
    assert "1" in output  # 本次允许
    assert "2" in output  # 始终允许
    assert "3" in output  # 拒绝

    print("✓ test_show_options PASSED")


def test_show_confirmation_panel_bash():
    """测试 bash_run 确认面板显示"""
    ui = create_test_ui()

    ui._show_confirmation_panel('bash_run', 'executor', {'command': 'ls -la'}, '  command: ls -la')

    output = ui.console.file.getvalue()
    assert 'bash_run' in output
    assert 'ls -la' in output

    print("✓ test_show_confirmation_panel_bash PASSED")


def test_show_confirmation_panel_other():
    """测试其他工具确认面板显示"""
    ui = create_test_ui()

    ui._show_confirmation_panel('view_file', 'filesystem', {'path': '/test/file.py'}, '  path: /test/file.py')

    output = ui.console.file.getvalue()
    assert 'view_file' in output
    assert 'filesystem' in output

    print("✓ test_show_confirmation_panel_other PASSED")


def create_test_ui():
    """创建测试用的 ToolConfirmationUI 实例"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    console = Console(file=StringIO(), force_terminal=True)
    path_utils = PathUtils(project_root)
    registry = ToolRegistry(project_root=project_root)
    confirmation = ToolConfirmation(tool_registry=registry)

    return ToolConfirmationUI(
        console=console,
        project_root=project_root,
        path_utils=path_utils,
        confirmation_manager=confirmation
    )


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Testing ToolConfirmationUI")
    print("=" * 60 + "\n")

    tests = [
        test_extract_line_number_from_line_range,
        test_extract_line_number_from_line,
        test_extract_line_number_from_start_line,
        test_extract_line_number_none,
        test_truncate_short_text,
        test_truncate_long_text,
        test_truncate_exact_length,
        test_format_arguments_empty,
        test_format_arguments_simple,
        test_format_arguments_list,
        test_format_arguments_dict,
        test_get_signature_integration,
        test_confirm_non_interactive_mode,
        test_confirm_calls_get_signature,
        test_show_options,
        test_show_confirmation_panel_bash,
        test_show_confirmation_panel_other,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        print(f"✅ ALL {passed} TESTS PASSED")
    else:
        print(f"❌ {failed} FAILED, {passed} PASSED")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
