#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test tab completion functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.cli.cli_completer import ClaudeQwenCompleter, PathCompleter, CombinedCompleter
from prompt_toolkit.document import Document


def test_command_completion():
    """Test slash command completion"""
    completer = ClaudeQwenCompleter()

    print("\n[测试 1] 补全斜杠命令")
    print("=" * 50)

    # Test completing /h
    document = Document('/h')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '/h'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    assert any(c.text == '/help' for c in completions), "应该包含 /help"
    print("✓ /help 补全成功")

    return True


def test_model_subcommand_completion():
    """Test /model subcommand completion"""
    completer = ClaudeQwenCompleter()

    print("\n[测试 2] 补全 /model 子命令")
    print("=" * 50)

    # Test completing /model l
    document = Document('/model l')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '/model l'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    assert any(c.text == 'list' for c in completions), "应该包含 list"
    print("✓ /model list 补全成功")

    return True


def test_shell_command_completion():
    """Test shell command completion for /cmd"""
    completer = ClaudeQwenCompleter()

    print("\n[测试 3] 补全 /cmd 命令")
    print("=" * 50)

    # Test completing /cmd l
    document = Document('/cmd l')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '/cmd l'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    assert any(c.text == 'ls' for c in completions), "应该包含 ls"
    print("✓ /cmd ls 补全成功")

    return True


def test_all_commands_completion():
    """Test completing all commands with empty prefix"""
    completer = ClaudeQwenCompleter()

    print("\n[测试 4] 补全所有命令")
    print("=" * 50)

    # Test completing /
    document = Document('/')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '/'")
    print(f"补全结果 ({len(completions)} 个):")

    # Show first 10 commands
    for comp in completions[:10]:
        print(f"  - {comp.text} ({comp.display_meta})")

    if len(completions) > 10:
        print(f"  ... 还有 {len(completions) - 10} 个命令")

    assert len(completions) > 10, "应该有多个命令可补全"
    print(f"✓ 找到 {len(completions)} 个命令")

    return True


def test_cmdremote_completion():
    """Test /cmdremote command completion"""
    completer = ClaudeQwenCompleter()

    print("\n[测试 5] 补全 /cmdremote 命令")
    print("=" * 50)

    # Test completing /cmdremote o
    document = Document('/cmdremote o')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '/cmdremote o'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    assert any(c.text == 'ollama' for c in completions), "应该包含 ollama"
    print("✓ /cmdremote ollama 补全成功")

    return True


def test_combined_completer():
    """Test combined completer"""
    command_completer = ClaudeQwenCompleter()
    path_completer = PathCompleter('/')
    combined = CombinedCompleter([command_completer, path_completer])

    print("\n[测试 6] 组合补全器")
    print("=" * 50)

    # Test completing /h (should get commands)
    document = Document('/h')
    completions = list(combined.get_completions(document, None))

    print(f"输入: '/h'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text}")

    assert len(completions) > 0, "应该有补全结果"
    print("✓ 组合补全器工作正常")

    return True


def test_exact_match():
    """Test exact command match"""
    completer = ClaudeQwenCompleter()

    print("\n[测试 7] 精确匹配")
    print("=" * 50)

    # Test completing exact command
    document = Document('/help')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '/help'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    assert any(c.text == '/help' for c in completions), "应该包含 /help"
    print("✓ 精确匹配成功")

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("Tab 补全功能测试")
    print("=" * 50)

    results = []

    # Run tests
    try:
        results.append(("命令补全", test_command_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("命令补全", False))

    try:
        results.append(("模型子命令补全", test_model_subcommand_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("模型子命令补全", False))

    try:
        results.append(("Shell 命令补全", test_shell_command_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("Shell 命令补全", False))

    try:
        results.append(("所有命令补全", test_all_commands_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("所有命令补全", False))

    try:
        results.append(("远程命令补全", test_cmdremote_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("远程命令补全", False))

    try:
        results.append(("组合补全器", test_combined_completer()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("组合补全器", False))

    try:
        results.append(("精确匹配", test_exact_match()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("精确匹配", False))

    # Print summary
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
