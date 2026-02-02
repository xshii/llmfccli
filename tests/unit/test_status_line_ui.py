#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StatusLine 单元测试

测试状态行显示器的各个方法。
"""

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch, PropertyMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console

from backend.cli.ui.status_line import StatusLine


def create_mock_agent():
    """创建 mock AgentLoop"""
    agent = MagicMock()
    agent.token_counter = MagicMock()
    agent.token_counter.usage = {'total': 5000}
    agent.token_counter.max_tokens = 32000
    return agent


def create_mock_client():
    """创建 mock OllamaClient"""
    client = MagicMock()
    client.last_conversation_file = None
    client.last_request_file = None
    return client


def create_test_status_line():
    """创建测试用的 StatusLine 实例"""
    console = Console(file=StringIO(), force_terminal=True)
    agent = create_mock_agent()
    client = create_mock_client()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

    return StatusLine(
        console=console,
        agent=agent,
        client=client,
        project_root=project_root
    )


def test_format_number_small():
    """测试小于1000的数字格式化"""
    status_line = create_test_status_line()

    result = status_line._format_number(500)
    assert result == "500", f"Expected '500', got '{result}'"

    result = status_line._format_number(0)
    assert result == "0", f"Expected '0', got '{result}'"

    result = status_line._format_number(999)
    assert result == "999", f"Expected '999', got '{result}'"

    print("✓ test_format_number_small PASSED")


def test_format_number_thousands():
    """测试千位数字格式化"""
    status_line = create_test_status_line()

    result = status_line._format_number(1000)
    assert result == "1.0K", f"Expected '1.0K', got '{result}'"

    result = status_line._format_number(5000)
    assert result == "5.0K", f"Expected '5.0K', got '{result}'"

    result = status_line._format_number(32000)
    assert result == "32.0K", f"Expected '32.0K', got '{result}'"

    result = status_line._format_number(1500)
    assert result == "1.5K", f"Expected '1.5K', got '{result}'"

    print("✓ test_format_number_thousands PASSED")


def test_format_tokens():
    """测试 Token 格式化"""
    status_line = create_test_status_line()
    status_line.agent.token_counter.usage = {'total': 5000}
    status_line.agent.token_counter.max_tokens = 32000

    result = status_line._format_tokens()

    assert result is not None
    assert "5.0K" in result
    assert "32.0K" in result
    assert "16%" in result  # 5000/32000 = 15.625%

    print("✓ test_format_tokens PASSED")


def test_format_tokens_no_counter():
    """测试无 token_counter 时返回 None"""
    status_line = create_test_status_line()
    del status_line.agent.token_counter

    result = status_line._format_tokens()

    assert result is None, f"Expected None, got '{result}'"

    print("✓ test_format_tokens_no_counter PASSED")


def test_format_tokens_zero_max():
    """测试 max_tokens 为 0 时不除以零"""
    status_line = create_test_status_line()
    status_line.agent.token_counter.max_tokens = 0

    result = status_line._format_tokens()

    assert result is not None
    assert "0%" in result

    print("✓ test_format_tokens_zero_max PASSED")


def test_format_file_link_no_line():
    """测试无行号的文件链接格式化"""
    status_line = create_test_status_line()

    with patch('backend.utils.feature.get_feature_value') as mock_feature:
        mock_feature.side_effect = lambda key, default: {
            "cli_output.hyperlink_protocol.protocol": "file",
            "cli_output.hyperlink_protocol.show_line_number": True
        }.get(key, default)

        result = status_line._format_file_link("/test/path/file.py", None)

        assert "file.py" in result
        assert ":" not in result or "file://" in result  # 没有行号

    print("✓ test_format_file_link_no_line PASSED")


def test_format_file_link_with_line():
    """测试有行号的文件链接格式化"""
    status_line = create_test_status_line()

    with patch('backend.utils.feature.get_feature_value') as mock_feature:
        mock_feature.side_effect = lambda key, default: {
            "cli_output.hyperlink_protocol.protocol": "file",
            "cli_output.hyperlink_protocol.show_line_number": True
        }.get(key, default)

        result = status_line._format_file_link("/test/path/file.py", "42")

        assert "file.py" in result
        assert "42" in result

    print("✓ test_format_file_link_with_line PASSED")


def test_format_file_link_vscode_protocol():
    """测试 VSCode 协议的文件链接"""
    status_line = create_test_status_line()

    with patch('backend.utils.feature.get_feature_value') as mock_feature:
        mock_feature.side_effect = lambda key, default: {
            "cli_output.hyperlink_protocol.protocol": "vscode",
            "cli_output.hyperlink_protocol.show_line_number": True
        }.get(key, default)

        result = status_line._format_file_link("/test/path/file.py", "10")

        assert "vscode://file" in result
        assert "file.py" in result

    print("✓ test_format_file_link_vscode_protocol PASSED")


def test_format_file_link_none_protocol():
    """测试无协议时只返回文件名"""
    status_line = create_test_status_line()

    with patch('backend.utils.feature.get_feature_value') as mock_feature:
        mock_feature.side_effect = lambda key, default: {
            "cli_output.hyperlink_protocol.protocol": "none",
            "cli_output.hyperlink_protocol.show_line_number": True
        }.get(key, default)

        result = status_line._format_file_link("/test/path/file.py", "10")

        assert result == "file.py:10", f"Expected 'file.py:10', got '{result}'"
        assert "[link=" not in result

    print("✓ test_format_file_link_none_protocol PASSED")


def test_format_file_link_line_range():
    """测试行范围格式"""
    status_line = create_test_status_line()

    with patch('backend.utils.feature.get_feature_value') as mock_feature:
        mock_feature.side_effect = lambda key, default: {
            "cli_output.hyperlink_protocol.protocol": "none",
            "cli_output.hyperlink_protocol.show_line_number": True
        }.get(key, default)

        result = status_line._format_file_link("/test/path/file.py", "10-20")

        assert "file.py" in result
        assert "10" in result  # 应该使用起始行

    print("✓ test_format_file_link_line_range PASSED")


def test_format_ide_file_not_connected():
    """测试未连接 VSCode 时的显示"""
    status_line = create_test_status_line()

    with patch('backend.rpc.client.is_vscode_mode', return_value=False):
        result = status_line._format_ide_file()

        assert "未连接" in result or "vscode" in result.lower()

    print("✓ test_format_ide_file_not_connected PASSED")


def test_format_ide_file_no_active_file():
    """测试无活动文件时的显示"""
    status_line = create_test_status_line()

    with patch('backend.rpc.client.is_vscode_mode', return_value=True):
        with patch.object(status_line, '_get_ide_file_info', return_value=None):
            result = status_line._format_ide_file()

            assert "无活动文件" in result

    print("✓ test_format_ide_file_no_active_file PASSED")


def test_format_conversation_file_none():
    """测试无对话文件时的显示"""
    status_line = create_test_status_line()
    status_line.client.last_conversation_file = None
    status_line.client.last_request_file = None

    result = status_line._format_conversation_file()

    assert "暂无历史对话" in result

    print("✓ test_format_conversation_file_none PASSED")


def test_format_conversation_file_exists():
    """测试有对话文件时的显示"""
    status_line = create_test_status_line()

    # 创建临时文件路径
    temp_file = "/tmp/test_conversation.json"

    with patch('os.path.exists', return_value=True):
        status_line.client.last_conversation_file = temp_file

        with patch('backend.utils.feature.get_feature_value') as mock_feature:
            mock_feature.side_effect = lambda key, default: {
                "cli_output.hyperlink_protocol.protocol": "file"
            }.get(key, default)

            result = status_line._format_conversation_file()

            assert "查看历史会话" in result
            assert "[link=" in result

    print("✓ test_format_conversation_file_exists PASSED")


def test_get_conversation_file_from_conversation():
    """测试从 last_conversation_file 获取路径"""
    status_line = create_test_status_line()

    with patch('os.path.exists', return_value=True):
        status_line.client.last_conversation_file = "/tmp/conv.json"
        status_line.client.last_request_file = "/tmp/req.json"

        result = status_line._get_conversation_file()

        assert result == "/tmp/conv.json"

    print("✓ test_get_conversation_file_from_conversation PASSED")


def test_get_conversation_file_fallback_to_request():
    """测试回退到 last_request_file"""
    status_line = create_test_status_line()

    def exists_side_effect(path):
        return path == "/tmp/req.json"

    with patch('os.path.exists', side_effect=exists_side_effect):
        status_line.client.last_conversation_file = "/tmp/conv.json"
        status_line.client.last_request_file = "/tmp/req.json"

        result = status_line._get_conversation_file()

        assert result == "/tmp/req.json"

    print("✓ test_get_conversation_file_fallback_to_request PASSED")


def test_format_todo_progress_empty():
    """测试无 todo 时返回 None"""
    status_line = create_test_status_line()

    with patch('backend.todo.get_todo_manager') as mock_manager:
        mock_manager.return_value.total_count = 0

        result = status_line._format_todo_progress()

        assert result is None

    print("✓ test_format_todo_progress_empty PASSED")


def test_format_todo_progress_with_tasks():
    """测试有 todo 时的进度显示"""
    status_line = create_test_status_line()

    mock_todo = MagicMock()
    mock_todo.total_count = 5
    mock_todo.completed_count = 2
    mock_todo.progress_percent = 40
    mock_todo.current_task = MagicMock()
    mock_todo.current_task.active_form = "Working on task"
    mock_todo.current_task.content = "Task content"

    with patch('backend.todo.get_todo_manager', return_value=mock_todo):
        result = status_line._format_todo_progress()

        assert result is not None
        assert "40%" in result
        assert "2/5" in result
        assert "Working on task" in result

    print("✓ test_format_todo_progress_with_tasks PASSED")


def test_format_todo_progress_long_task_name():
    """测试长任务名称截断"""
    status_line = create_test_status_line()

    mock_todo = MagicMock()
    mock_todo.total_count = 1
    mock_todo.completed_count = 0
    mock_todo.progress_percent = 0
    mock_todo.current_task = MagicMock()
    mock_todo.current_task.active_form = "A" * 50  # 超过 40 字符
    mock_todo.current_task.content = "Task"

    with patch('backend.todo.get_todo_manager', return_value=mock_todo):
        result = status_line._format_todo_progress()

        assert result is not None
        assert "..." in result  # 应该被截断

    print("✓ test_format_todo_progress_long_task_name PASSED")


def test_show_combines_all_parts():
    """测试 show 方法组合所有部分"""
    status_line = create_test_status_line()

    # Mock 所有格式化方法
    with patch.object(status_line, '_format_todo_progress', return_value=None):
        with patch.object(status_line, '_format_role', return_value="Role"):
            with patch.object(status_line, '_format_tokens', return_value="Tokens: 5K/32K"):
                with patch.object(status_line, '_format_ide_file', return_value="file.py"):
                    with patch.object(status_line, '_format_conversation_file', return_value="History"):
                        status_line.show()

                        output = status_line.console.file.getvalue()
                        assert "Role" in output
                        assert "Tokens" in output

    print("✓ test_show_combines_all_parts PASSED")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Testing StatusLine")
    print("=" * 60 + "\n")

    tests = [
        test_format_number_small,
        test_format_number_thousands,
        test_format_tokens,
        test_format_tokens_no_counter,
        test_format_tokens_zero_max,
        test_format_file_link_no_line,
        test_format_file_link_with_line,
        test_format_file_link_vscode_protocol,
        test_format_file_link_none_protocol,
        test_format_file_link_line_range,
        test_format_ide_file_not_connected,
        test_format_ide_file_no_active_file,
        test_format_conversation_file_none,
        test_format_conversation_file_exists,
        test_get_conversation_file_from_conversation,
        test_get_conversation_file_fallback_to_request,
        test_format_todo_progress_empty,
        test_format_todo_progress_with_tasks,
        test_format_todo_progress_long_task_name,
        test_show_combines_all_parts,
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
