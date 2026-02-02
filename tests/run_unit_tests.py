#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器 - 支持单元测试和系统测试

用法:
    python run_unit_tests.py           # 仅运行单元测试（不需要 Ollama/VSCode）
    python run_unit_tests.py --ollama  # 运行需要 Ollama 的 e2e 测试
    python run_unit_tests.py --vscode  # 运行需要 VSCode 的 e2e 测试
    python run_unit_tests.py --all     # 运行所有测试
"""

import sys
import os
import subprocess
import argparse
from glob import glob
from pathlib import Path


# 需要 Ollama 连接的测试文件模式（OllamaClient 初始化时会 warmup）
OLLAMA_PATTERNS = [
    'unit/test_ollama_hello.py',
    'unit/test_llm_factory.py',       # create_client 触发 warmup
    'unit/test_multi_backend.py',     # OllamaClient 初始化触发 warmup
    'e2e/test_case_*.py',
    'e2e/test_e2e_cases.py',
]

# 需要 VSCode 连接的测试文件模式
VSCODE_PATTERNS = [
    'e2e/test_vscode_integration.py',
]

# 需要 Node.js 的测试（编译 VSCode 扩展等）
NODEJS_PATTERNS = [
    'extension/test_typescript_integration.py',
]

# 慢速测试（执行时间 > 5 秒，但不需要外部服务）
SLOW_PATTERNS = [
    'unit/test_persistent_shell.py',  # ~25s，测试 shell session
    'unit/test_executor.py',           # ~7s，测试 bash 命令执行
]

# 需要跳过的测试（fixture 中的测试文件等）
SKIP_PATTERNS = [
    'fixtures/*',
    '__pycache__/*',
]


def get_tests_dir():
    """获取测试目录"""
    return Path(__file__).parent


def discover_tests(patterns, base_dir=None):
    """根据模式发现测试文件"""
    base_dir = base_dir or get_tests_dir()
    tests = []
    for pattern in patterns:
        matches = glob(str(base_dir / pattern))
        tests.extend(matches)
    return sorted(set(tests))


def is_skipped(test_path):
    """检查测试是否应该跳过"""
    test_path = str(test_path)
    for pattern in SKIP_PATTERNS:
        if pattern.replace('*', '') in test_path:
            return True
    return False


def matches_pattern(test_path, patterns):
    """检查测试是否匹配任一模式"""
    test_path = Path(test_path)
    tests_dir = get_tests_dir()

    try:
        rel_path = test_path.relative_to(tests_dir)
    except ValueError:
        return False

    for pattern in patterns:
        matched = list(tests_dir.glob(pattern))
        if test_path in matched or str(test_path) in [str(m) for m in matched]:
            return True
    return False


def discover_unit_tests(exclude_slow=False):
    """发现纯单元测试（不需要外部依赖）

    Args:
        exclude_slow: 是否排除慢速测试
    """
    tests_dir = get_tests_dir()
    all_tests = []

    # 发现 unit 目录下的测试
    unit_tests = glob(str(tests_dir / 'unit' / 'test_*.py'))
    all_tests.extend(unit_tests)

    # 添加 extension 测试
    ext_tests = glob(str(tests_dir / 'extension' / 'test_*.py'))
    all_tests.extend(ext_tests)

    # 过滤掉需要外部依赖的测试
    filtered = []
    for test in all_tests:
        if is_skipped(test):
            continue
        if matches_pattern(test, OLLAMA_PATTERNS):
            continue
        if matches_pattern(test, VSCODE_PATTERNS):
            continue
        if matches_pattern(test, NODEJS_PATTERNS):
            continue
        if exclude_slow and matches_pattern(test, SLOW_PATTERNS):
            continue
        filtered.append(test)

    return sorted(filtered)


def discover_nodejs_tests():
    """发现需要 Node.js 的测试"""
    tests_dir = get_tests_dir()
    tests = []
    for pattern in NODEJS_PATTERNS:
        matches = glob(str(tests_dir / pattern))
        tests.extend(matches)
    return sorted(set(tests))


def discover_ollama_tests():
    """发现需要 Ollama 的测试"""
    tests_dir = get_tests_dir()
    tests = []
    for pattern in OLLAMA_PATTERNS:
        matches = glob(str(tests_dir / pattern))
        tests.extend(matches)
    return sorted(set(tests))


def discover_vscode_tests():
    """发现需要 VSCode 的测试"""
    tests_dir = get_tests_dir()
    tests = []
    for pattern in VSCODE_PATTERNS:
        matches = glob(str(tests_dir / pattern))
        tests.extend(matches)
    return sorted(set(tests))


def get_test_description(test_path):
    """从测试文件获取描述"""
    test_path = Path(test_path)
    name = test_path.stem.replace('test_', '').replace('_', ' ').title()
    parent = test_path.parent.name
    return f"[{parent}] {name}"


def run_tests(test_list, title, timeout=60):
    """运行指定的测试列表"""
    passed = 0
    failed = 0
    errors = 0

    print("=" * 60)
    print(title)
    print("=" * 60)
    print(f"总计: {len(test_list)} 个测试\n")

    for test_path in test_list:
        description = get_test_description(test_path)
        rel_path = Path(test_path).relative_to(get_tests_dir())

        print(f"\n运行: {description}")
        print(f"文件: {rel_path}")
        print("-" * 60)

        try:
            import time
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.time() - start_time

            # 输出测试结果
            if result.stdout:
                print(result.stdout)

            if result.returncode == 0:
                passed += 1
                print(f"✓ {description} - PASSED ({elapsed:.1f}s)")
            else:
                failed += 1
                print(f"✗ {description} - FAILED ({elapsed:.1f}s)")
                if result.stderr:
                    print("错误输出:")
                    print(result.stderr)

        except subprocess.TimeoutExpired:
            errors += 1
            print(f"✗ {description} - TIMEOUT")
        except Exception as e:
            errors += 1
            print(f"✗ {description} - ERROR: {e}")

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(test_list)}")
    print(f"失败: {failed}/{len(test_list)}")
    print(f"错误: {errors}/{len(test_list)}")

    return failed == 0 and errors == 0


def main():
    parser = argparse.ArgumentParser(
        description='Claude-Qwen 测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run_unit_tests.py           # 仅运行单元测试
    python run_unit_tests.py --fast    # 仅运行快速单元测试（跳过 >5s 的测试）
    python run_unit_tests.py --ollama  # 运行 Ollama 系统测试
    python run_unit_tests.py --vscode  # 运行 VSCode 系统测试
    python run_unit_tests.py --all     # 运行所有测试
    python run_unit_tests.py --list    # 列出所有测试
        """
    )
    parser.add_argument('--fast', action='store_true',
                        help='跳过慢速测试（>5秒），快速验证')
    parser.add_argument('--ollama', action='store_true',
                        help='运行需要 Ollama 连接的系统测试')
    parser.add_argument('--vscode', action='store_true',
                        help='运行需要 VSCode 连接的系统测试')
    parser.add_argument('--nodejs', action='store_true',
                        help='运行需要 Node.js 的测试（VSCode 扩展编译等）')
    parser.add_argument('--all', action='store_true',
                        help='运行所有测试')
    parser.add_argument('--list', action='store_true',
                        help='列出所有测试而不运行')
    args = parser.parse_args()

    # 发现测试
    unit_tests = discover_unit_tests(exclude_slow=args.fast)
    ollama_tests = discover_ollama_tests()
    vscode_tests = discover_vscode_tests()
    nodejs_tests = discover_nodejs_tests()

    if args.list:
        # 分离快速和慢速测试
        slow_tests = discover_tests(SLOW_PATTERNS)
        fast_unit_tests = [t for t in unit_tests if t not in slow_tests]

        print("=" * 60)
        print("可用测试")
        print("=" * 60)
        print(f"\n快速单元测试 ({len(fast_unit_tests)} 个) - 无外部依赖，<5秒:")
        for t in fast_unit_tests:
            print(f"  - {Path(t).relative_to(get_tests_dir())}")
        print(f"\n慢速单元测试 ({len(slow_tests)} 个) - 无外部依赖，>5秒:")
        for t in slow_tests:
            print(f"  - {Path(t).relative_to(get_tests_dir())}")
        print(f"\nOllama 系统测试 ({len(ollama_tests)} 个) - 需要 Ollama:")
        for t in ollama_tests:
            print(f"  - {Path(t).relative_to(get_tests_dir())}")
        print(f"\nVSCode 系统测试 ({len(vscode_tests)} 个) - 需要 VSCode:")
        for t in vscode_tests:
            print(f"  - {Path(t).relative_to(get_tests_dir())}")
        print(f"\nNode.js 测试 ({len(nodejs_tests)} 个) - 需要 Node.js:")
        for t in nodejs_tests:
            print(f"  - {Path(t).relative_to(get_tests_dir())}")
        return 0

    results = []

    if args.all:
        # 运行所有测试
        if unit_tests:
            results.append(run_tests(unit_tests, "单元测试", timeout=60))
        if nodejs_tests:
            results.append(run_tests(nodejs_tests, "Node.js 测试", timeout=120))
        if ollama_tests:
            results.append(run_tests(ollama_tests, "Ollama 系统测试", timeout=300))
        if vscode_tests:
            results.append(run_tests(vscode_tests, "VSCode 系统测试", timeout=120))
    elif args.ollama:
        if ollama_tests:
            results.append(run_tests(ollama_tests, "Ollama 系统测试", timeout=300))
        else:
            print("未找到 Ollama 系统测试")
            return 1
    elif args.vscode:
        if vscode_tests:
            results.append(run_tests(vscode_tests, "VSCode 系统测试", timeout=120))
        else:
            print("未找到 VSCode 系统测试")
            return 1
    elif args.nodejs:
        if nodejs_tests:
            results.append(run_tests(nodejs_tests, "Node.js 测试", timeout=120))
        else:
            print("未找到 Node.js 测试")
            return 1
    else:
        # 默认只运行单元测试（无外部依赖）
        if unit_tests:
            results.append(run_tests(unit_tests, "单元测试", timeout=60))
        else:
            print("未找到单元测试")
            return 1

    # 返回结果
    if all(results):
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
