#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrecheckRunner 单元测试

测试预检查运行器的各个方法。
"""

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rich.console import Console

from backend.cli.ui.precheck_runner import PrecheckRunner
from backend.utils.precheck import PreCheckResult


def create_test_runner():
    """创建测试用的 PrecheckRunner 实例"""
    console = Console(file=StringIO(), force_terminal=True)
    runner = PrecheckRunner(console=console)
    return runner


def test_get_path_prefix_empty():
    """测试无额外路径时返回空字符串"""
    runner = create_test_runner()
    runner._extra_paths = []

    result = runner._get_path_prefix()
    assert result == "", f"Expected empty string, got '{result}'"

    print("✓ test_get_path_prefix_empty PASSED")


def test_get_path_prefix_single():
    """测试单个额外路径"""
    runner = create_test_runner()
    runner._extra_paths = ['/usr/local/bin']

    result = runner._get_path_prefix()
    assert 'export PATH=' in result
    assert '/usr/local/bin' in result

    print("✓ test_get_path_prefix_single PASSED")


def test_get_path_prefix_multiple():
    """测试多个额外路径"""
    runner = create_test_runner()
    runner._extra_paths = ['/opt/bin', '/usr/local/bin']

    result = runner._get_path_prefix()
    assert '/opt/bin:/usr/local/bin' in result or '/opt/bin' in result

    print("✓ test_get_path_prefix_multiple PASSED")


def test_display_results_all_passed():
    """测试所有检查通过时的显示"""
    runner = create_test_runner()

    results = [
        PreCheckResult(name="Test 1", success=True, message="Test 1 passed"),
        PreCheckResult(name="Test 2", success=True, message="Test 2 passed"),
    ]

    all_passed = runner._display_results(results)

    assert all_passed is True, "Expected all_passed to be True"

    output = runner.console.file.getvalue()
    assert "✓" in output

    print("✓ test_display_results_all_passed PASSED")


def test_display_results_some_failed():
    """测试部分检查失败时的显示"""
    runner = create_test_runner()

    results = [
        PreCheckResult(name="Test 1", success=True, message="Test 1 passed"),
        PreCheckResult(name="Test 2", success=False, message="Test 2 failed"),
    ]

    all_passed = runner._display_results(results)

    assert all_passed is False, "Expected all_passed to be False"

    output = runner.console.file.getvalue()
    assert "✗" in output

    print("✓ test_display_results_some_failed PASSED")


def test_display_results_all_failed():
    """测试所有检查失败时的显示"""
    runner = create_test_runner()

    results = [
        PreCheckResult(name="Test 1", success=False, message="Test 1 failed"),
        PreCheckResult(name="Test 2", success=False, message="Test 2 failed"),
    ]

    all_passed = runner._display_results(results)

    assert all_passed is False, "Expected all_passed to be False"

    print("✓ test_display_results_all_failed PASSED")


def test_show_suggestions_ssh_tunnel():
    """测试 SSH 隧道失败时的建议显示"""
    runner = create_test_runner()
    runner._ssh_host = "test-host"

    results = [
        PreCheckResult(name="SSH Tunnel Check", success=False, message="SSH 隧道未连接"),
    ]

    runner._show_suggestions(results)

    output = runner.console.file.getvalue()
    assert "ssh" in output.lower()
    assert "test-host" in output

    print("✓ test_show_suggestions_ssh_tunnel PASSED")


def test_show_suggestions_remote_ollama():
    """测试远程 Ollama 未运行时的建议显示"""
    runner = create_test_runner()
    runner._ssh_host = "ollama-server"

    results = [
        PreCheckResult(name="SSH Tunnel Check", success=False, message="远程 Ollama 服务未运行"),
    ]

    runner._show_suggestions(results)

    output = runner.console.file.getvalue()
    assert "ollama serve" in output

    print("✓ test_show_suggestions_remote_ollama PASSED")


def test_show_suggestions_model_missing():
    """测试模型缺失时的建议显示"""
    runner = create_test_runner()

    results = [
        PreCheckResult(
            name="Ollama Model Check",
            success=False,
            message="模型未找到",
            details={'model': 'glm-4.7-flash'}
        ),
    ]

    runner._show_suggestions(results)

    output = runner.console.file.getvalue()
    assert "ollama pull" in output
    # 注意：Rich 颜色代码会拆分字符串，所以检查部分匹配
    assert "glm" in output and "flash" in output

    print("✓ test_show_suggestions_model_missing PASSED")


def test_read_single_key_non_interactive():
    """测试非交互模式下的按键读取"""
    runner = create_test_runner()

    with patch('sys.stdin') as mock_stdin:
        mock_stdin.isatty.return_value = False
        mock_stdin.readline.return_value = "\n"

        # 模拟 input() 返回空字符串
        with patch('builtins.input', return_value=''):
            result = runner._read_single_key()

        assert result == 'r', f"Expected 'r' (default), got '{result}'"

    print("✓ test_read_single_key_non_interactive PASSED")


def test_read_single_key_with_input():
    """测试有输入时的按键读取"""
    runner = create_test_runner()

    with patch('sys.stdin') as mock_stdin:
        mock_stdin.isatty.return_value = False

        with patch('builtins.input', return_value='s'):
            result = runner._read_single_key()

        assert result == 's', f"Expected 's', got '{result}'"

    print("✓ test_read_single_key_with_input PASSED")


def test_get_user_action_ssh():
    """测试用户选择启动 SSH"""
    runner = create_test_runner()

    with patch.object(runner, '_read_single_key', return_value='s'):
        result = runner._get_user_action()

    assert result == 'ssh', f"Expected 'ssh', got '{result}'"

    print("✓ test_get_user_action_ssh PASSED")


def test_get_user_action_retry():
    """测试用户选择重试"""
    runner = create_test_runner()

    with patch.object(runner, '_read_single_key', return_value='r'):
        result = runner._get_user_action()

    assert result == 'retry', f"Expected 'retry', got '{result}'"

    print("✓ test_get_user_action_retry PASSED")


def test_get_user_action_exit():
    """测试用户选择退出"""
    runner = create_test_runner()

    with patch.object(runner, '_read_single_key', return_value='n'):
        result = runner._get_user_action()

    assert result == 'exit', f"Expected 'exit', got '{result}'"

    print("✓ test_get_user_action_exit PASSED")


def test_get_user_action_keyboard_interrupt():
    """测试键盘中断"""
    runner = create_test_runner()

    with patch.object(runner, '_read_single_key', side_effect=KeyboardInterrupt):
        with patch.object(runner.console, 'print'):
            result = runner._get_user_action()

    assert result == 'exit', f"Expected 'exit', got '{result}'"

    print("✓ test_get_user_action_keyboard_interrupt PASSED")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Testing PrecheckRunner")
    print("=" * 60 + "\n")

    tests = [
        test_get_path_prefix_empty,
        test_get_path_prefix_single,
        test_get_path_prefix_multiple,
        test_display_results_all_passed,
        test_display_results_some_failed,
        test_display_results_all_failed,
        test_show_suggestions_ssh_tunnel,
        test_show_suggestions_remote_ollama,
        test_show_suggestions_model_missing,
        test_read_single_key_non_interactive,
        test_read_single_key_with_input,
        test_get_user_action_ssh,
        test_get_user_action_retry,
        test_get_user_action_exit,
        test_get_user_action_keyboard_interrupt,
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
