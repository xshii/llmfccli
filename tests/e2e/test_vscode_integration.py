#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E 测试：VSCode Extension 集成

测试 CLI 与 VSCode Extension 的 Socket 通信

前置条件：
1. VSCode 已安装 claude-qwen extension
2. VSCode 已启动并打开项目
3. Extension 的 socket 服务器正在运行
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_socket_connection():
    """测试 Socket 连接"""
    print("1. 测试 Socket 连接...")

    from backend.rpc.client import get_client, is_vscode_mode

    client = get_client()

    # 等待心跳连接
    max_wait = 10
    for i in range(max_wait):
        if is_vscode_mode():
            break
        time.sleep(1)
        print(f"   等待连接... ({i+1}/{max_wait})")

    if is_vscode_mode():
        print("   ✓ Socket 连接成功")
        return True
    else:
        print("   ✗ Socket 连接失败")
        print("   请确保 VSCode 已启动并安装了 claude-qwen extension")
        return False


def test_get_active_file():
    """测试获取当前打开的文件"""
    print("\n2. 测试获取当前文件...")

    from backend.rpc.client import is_vscode_mode
    if not is_vscode_mode():
        print("   ✗ 跳过：未连接到 VSCode")
        return False

    try:
        from backend.tools import vscode
        file_info = vscode.get_active_file()

        path = file_info.get('path')
        language = file_info.get('language')
        line_count = file_info.get('lineCount')

        print(f"   路径: {path}")
        print(f"   语言: {language}")
        print(f"   行数: {line_count}")

        if path:
            print("   ✓ 获取当前文件成功")
            return True
        else:
            print("   ✗ 获取当前文件失败：无活动文件")
            return False

    except Exception as e:
        print(f"   ✗ 获取当前文件失败: {e}")
        return False


def test_get_selection():
    """测试获取选中内容/光标位置"""
    print("\n3. 测试获取选中/光标位置...")

    from backend.rpc.client import is_vscode_mode
    if not is_vscode_mode():
        print("   ✗ 跳过：未连接到 VSCode")
        return False

    try:
        from backend.tools import vscode
        selection = vscode.get_selection()

        start_line = selection['start']['line'] + 1
        end_line = selection['end']['line'] + 1
        text = selection.get('text', '')

        if start_line == end_line:
            print(f"   光标位置: 第 {start_line} 行")
        else:
            print(f"   选中区域: 第 {start_line}-{end_line} 行")

        if text:
            preview = text[:50] + "..." if len(text) > 50 else text
            print(f"   选中文本: {preview}")

        print("   ✓ 获取选中/光标位置成功")
        return True

    except Exception as e:
        print(f"   ✗ 获取选中/光标位置失败: {e}")
        return False


def test_status_line():
    """测试 Status Line 显示"""
    print("\n4. 测试 Status Line...")

    from backend.rpc.client import is_vscode_mode
    if not is_vscode_mode():
        print("   ✗ 跳过：未连接到 VSCode")
        return False

    try:
        from backend.cli.status_line import StatusLine
        from rich.console import Console
        from io import StringIO

        # 创建一个模拟的 console 来捕获输出
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        # 模拟 agent 和 client
        class MockAgent:
            class TokenCounter:
                usage = {'total': 1500}
                max_tokens = 128000
            token_counter = TokenCounter()

        class MockClient:
            last_conversation_file = None
            last_request_file = None

        status_line = StatusLine(console, MockAgent(), MockClient())
        status_line.show()

        result = output.getvalue()
        print(f"   输出: {result.strip()}")

        if "Tokens:" in result:
            print("   ✓ Status Line 显示正常")
            return True
        else:
            print("   ✗ Status Line 显示异常")
            return False

    except Exception as e:
        print(f"   ✗ Status Line 测试失败: {e}")
        return False


def test_heartbeat_ping():
    """测试心跳 Ping"""
    print("\n5. 测试心跳 Ping...")

    from backend.rpc.client import is_vscode_mode, send_vscode_request

    if not is_vscode_mode():
        print("   ✗ 跳过：未连接到 VSCode")
        return False

    try:
        # 发送 ping 请求
        result = send_vscode_request("ping", timeout=2.0)

        if result and result.get('pong'):
            print(f"   响应: {result}")
            print("   ✓ 心跳 Ping 成功")
            return True
        else:
            print(f"   ✗ 心跳响应异常: {result}")
            return False

    except Exception as e:
        print(f"   ✗ 心跳 Ping 失败: {e}")
        return False


def test_socket_reconnect():
    """测试 Socket 断线重连"""
    print("\n6. 测试断线重连...")

    from backend.rpc.client import get_client, is_vscode_mode

    if not is_vscode_mode():
        print("   ✗ 跳过：未连接到 VSCode")
        return False

    client = get_client()
    print("   当前状态: 已连接")

    # 模拟断开连接
    print("   模拟断开连接...")
    client._disconnect()

    if not is_vscode_mode():
        print("   断开成功，等待重连...")

        # 等待心跳重连
        max_wait = 10
        for i in range(max_wait):
            time.sleep(1)
            if is_vscode_mode():
                print(f"   ✓ 重连成功 ({i+1}秒)")
                return True

        print("   ✗ 重连超时")
        return False
    else:
        print("   ✗ 断开失败")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("VSCode Extension 集成测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("Socket 连接", test_socket_connection()))
    results.append(("获取当前文件", test_get_active_file()))
    results.append(("获取选中/光标", test_get_selection()))
    results.append(("Status Line", test_status_line()))
    results.append(("心跳 Ping", test_heartbeat_ping()))
    results.append(("断线重连", test_socket_reconnect()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n总计: {passed} 通过, {failed} 失败")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
