#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 claude-qwen 命令行入口点

验证：
1. main 函数可以从 backend.cli.main 模块导入
2. main 函数可以从 backend.cli 包级别导入
3. main 函数是可调用的
4. claude-qwen 命令可以正确执行
"""

import os
import sys
import subprocess
import importlib

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def test_main_function_import_from_module():
    """测试从 backend.cli.main 模块导入 main 函数"""
    from backend.cli.main import main

    assert main is not None, "main 函数不应为 None"
    assert callable(main), "main 应该是可调用的函数"

    print("✓ Test 1: main 函数可以从 backend.cli.main 导入")


def test_main_module_import_from_package():
    """测试从 backend.cli 包级别导入 main 模块"""
    from backend.cli import main
    import types

    # 由于存在 backend/cli/main.py 子模块，
    # Python 导入系统会优先导入模块而不是调用 __getattr__
    assert main is not None, "main 不应为 None"
    assert isinstance(main, types.ModuleType), \
        "从 backend.cli 导入的 main 应该是模块（因为子模块存在）"

    # 但模块中应该有 main() 函数
    assert hasattr(main, 'main'), "main 模块应该有 main 函数"
    assert callable(main.main), "main.main 应该是可调用的函数"

    print("✓ Test 2: main 模块可以从 backend.cli 包级别导入")


def test_main_function_signature():
    """测试 main 函数签名"""
    from backend.cli.main import main
    import inspect

    # 检查是否是函数
    assert inspect.isfunction(main), "main 应该是一个函数"

    # 检查函数签名（main 应该不接受参数）
    sig = inspect.signature(main)
    assert len(sig.parameters) == 0, "main() 不应接受参数"

    print("✓ Test 3: main 函数签名正确")


def test_cli_command_version():
    """测试 claude-qwen --version 命令"""
    result = subprocess.run(
        ['claude-qwen', '--version'],
        capture_output=True,
        text=True,
        timeout=5
    )

    assert result.returncode == 0, \
        f"命令应该成功执行，但返回码为 {result.returncode}"

    # 验证版本输出
    assert '0.1.0' in result.stdout, \
        f"应该输出版本号 0.1.0，但输出为: {result.stdout}"

    print(f"✓ Test 4: claude-qwen --version 执行成功，输出: {result.stdout.strip()}")


def test_cli_command_help():
    """测试 claude-qwen --help 命令"""
    result = subprocess.run(
        ['claude-qwen', '--help'],
        capture_output=True,
        text=True,
        timeout=5
    )

    assert result.returncode == 0, \
        f"命令应该成功执行，但返回码为 {result.returncode}"

    # 验证帮助信息包含关键内容
    assert 'Claude-Qwen' in result.stdout, "帮助信息应包含 Claude-Qwen"
    assert '--root' in result.stdout, "帮助信息应包含 --root 选项"
    assert '--skip-precheck' in result.stdout, "帮助信息应包含 --skip-precheck 选项"

    print("✓ Test 5: claude-qwen --help 执行成功")


def test_entry_point_consistency():
    """测试入口点配置一致性"""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # Fallback for Python 3.10

    # 读取 pyproject.toml
    pyproject_path = os.path.join(
        os.path.dirname(__file__),
        '../../pyproject.toml'
    )

    with open(pyproject_path, 'rb') as f:
        config = tomllib.load(f)

    # 验证入口点配置
    entry_point = config['project']['scripts']['claude-qwen']

    # 应该是 backend.cli.main:main
    assert entry_point == 'backend.cli.main:main', \
        f"入口点应该是 'backend.cli.main:main'，但实际是 '{entry_point}'"

    print(f"✓ Test 6: pyproject.toml 入口点配置正确: {entry_point}")


def test_entry_point_resolution():
    """测试入口点正确解析（回归测试）"""
    # 这是一个回归测试，确保入口点配置正确

    # 模拟 setuptools 入口点解析
    # backend.cli.main:main 应该解析为 backend.cli.main 模块的 main 函数
    from backend.cli.main import main

    assert main is not None, "应该能导入 main 函数"
    assert callable(main), "main 应该是可调用的函数"

    # 验证这是函数而不是模块
    import types
    assert not isinstance(main, types.ModuleType), \
        "从 backend.cli.main 导入的 main 应该是函数，不是模块"

    print("✓ Test 7: 回归测试通过 - 入口点正确解析为函数")


def main():
    """运行所有测试"""
    tests = [
        test_main_function_import_from_module,
        test_main_module_import_from_package,
        test_main_function_signature,
        test_cli_command_version,
        test_cli_command_help,
        test_entry_point_consistency,
        test_entry_point_resolution,
    ]

    print("=" * 60)
    print("测试 Claude-Qwen 命令行入口点")
    print("=" * 60)
    print()

    failed_tests = []

    for test_func in tests:
        try:
            test_func()
        except AssertionError as e:
            print(f"✗ {test_func.__name__} 失败: {e}")
            failed_tests.append((test_func.__name__, str(e)))
        except Exception as e:
            print(f"✗ {test_func.__name__} 错误: {e}")
            failed_tests.append((test_func.__name__, str(e)))

    print()
    print("=" * 60)

    if failed_tests:
        print(f"❌ {len(failed_tests)} 个测试失败:")
        for name, error in failed_tests:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print(f"✅ 所有 {len(tests)} 个测试通过!")
        print()
        print("入口点验证:")
        print("  ✓ Python 模块导入")
        print("  ✓ Python 包导入")
        print("  ✓ 函数签名")
        print("  ✓ CLI 命令执行")
        print("  ✓ 配置文件一致性")
        print("  ✓ 回归测试")

    print("=" * 60)


if __name__ == '__main__':
    main()
