#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test file name completion functionality
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.cli_completer import FileNameCompleter
from prompt_toolkit.document import Document


def create_test_project():
    """Create a temporary test project structure"""
    temp_dir = tempfile.mkdtemp(prefix='test_completion_')

    # Create directory structure
    os.makedirs(os.path.join(temp_dir, 'src'))
    os.makedirs(os.path.join(temp_dir, 'tests'))
    os.makedirs(os.path.join(temp_dir, 'docs'))
    os.makedirs(os.path.join(temp_dir, 'backend'))

    # Create test files
    test_files = [
        'src/network_handler.cpp',
        'src/network_handler.h',
        'src/file_manager.cpp',
        'src/main.cpp',
        'tests/test_network.cpp',
        'tests/test_file.cpp',
        'docs/README.md',
        'docs/USAGE.md',
        'backend/server.py',
        'backend/client.py',
        'config.yaml',
        'setup.py',
    ]

    for file_path in test_files:
        full_path = os.path.join(temp_dir, file_path)
        Path(full_path).touch()

    return temp_dir


def test_filename_completion():
    """Test basic file name completion"""
    # Create test project
    temp_dir = create_test_project()
    completer = FileNameCompleter(temp_dir, cache_duration=1)

    print("\n[测试 1] 基本文件名补全")
    print("=" * 50)

    # Test completing "net"
    document = Document('找到 net')
    completions = list(completer.get_completions(document, None))

    print(f"输入: '找到 net'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions[:5]:
        print(f"  - {comp.text} ({comp.display_meta})")

    # Should find network_handler files
    assert any('network' in c.text for c in completions), "应该包含 network 相关文件"
    print("✓ 文件名补全成功")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_extension_filtering():
    """Test completion with file extensions"""
    temp_dir = create_test_project()
    completer = FileNameCompleter(temp_dir, cache_duration=1)

    print("\n[测试 2] 文件扩展名优先级")
    print("=" * 50)

    # Test completing "main"
    document = Document('main')
    completions = list(completer.get_completions(document, None))

    print(f"输入: 'main'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    # Should prioritize .cpp files
    cpp_files = [c for c in completions if c.text.endswith('.cpp')]
    assert len(cpp_files) > 0, "应该包含 .cpp 文件"
    print(f"✓ 找到 {len(cpp_files)} 个 C++ 文件")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_path_completion():
    """Test partial path completion"""
    temp_dir = create_test_project()
    completer = FileNameCompleter(temp_dir, cache_duration=1)

    print("\n[测试 3] 路径补全")
    print("=" * 50)

    # Test completing "src/net"
    document = Document('src/net')
    completions = list(completer.get_completions(document, None))

    print(f"输入: 'src/net'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions:
        print(f"  - {comp.text} ({comp.display_meta})")

    # Should find files in src/ starting with net
    assert any('src/network' in c.text for c in completions), "应该包含 src/network 文件"
    print("✓ 路径补全成功")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_caching():
    """Test file list caching"""
    temp_dir = create_test_project()
    completer = FileNameCompleter(temp_dir, cache_duration=5)

    print("\n[测试 4] 缓存机制")
    print("=" * 50)

    # First scan
    import time
    start = time.time()
    files1 = completer._get_files()
    time1 = time.time() - start

    # Second scan (should use cache)
    start = time.time()
    files2 = completer._get_files()
    time2 = time.time() - start

    print(f"首次扫描: {len(files1)} 个文件, 耗时 {time1*1000:.2f}ms")
    print(f"缓存扫描: {len(files2)} 个文件, 耗时 {time2*1000:.2f}ms")

    assert len(files1) == len(files2), "缓存应该返回相同数量的文件"
    assert time2 < time1 or time2 < 0.001, "缓存应该更快"
    print("✓ 缓存机制工作正常")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_skip_directories():
    """Test skipping certain directories"""
    temp_dir = create_test_project()

    # Create directories that should be skipped
    os.makedirs(os.path.join(temp_dir, '.git'))
    os.makedirs(os.path.join(temp_dir, 'node_modules'))
    os.makedirs(os.path.join(temp_dir, '__pycache__'))

    # Create files in skip dirs
    Path(os.path.join(temp_dir, '.git', 'config')).touch()
    Path(os.path.join(temp_dir, 'node_modules', 'package.json')).touch()
    Path(os.path.join(temp_dir, '__pycache__', 'cache.pyc')).touch()

    completer = FileNameCompleter(temp_dir, cache_duration=1)

    print("\n[测试 5] 跳过特定目录")
    print("=" * 50)

    files = completer._get_files()

    print(f"扫描到 {len(files)} 个文件")

    # Should not include files from skip dirs
    assert not any('.git' in f for f in files), "不应该包含 .git 目录的文件"
    assert not any('node_modules' in f for f in files), "不应该包含 node_modules 目录的文件"
    assert not any('__pycache__' in f for f in files), "不应该包含 __pycache__ 目录的文件"

    print("✓ 成功跳过 .git, node_modules, __pycache__ 目录")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_match_scoring():
    """Test match scoring algorithm"""
    temp_dir = create_test_project()
    completer = FileNameCompleter(temp_dir, cache_duration=1)

    print("\n[测试 6] 匹配评分算法")
    print("=" * 50)

    # Test various match patterns
    test_cases = [
        ('src/network_handler.cpp', 'network', True),
        ('src/network_handler.cpp', 'net', True),
        ('src/file_manager.cpp', 'network', False),
        ('tests/test_network.cpp', 'test_net', True),
    ]

    for file_path, query, should_match in test_cases:
        score = completer._match_score(file_path, query)
        matched = score >= 0

        status = "✓" if matched == should_match else "✗"
        print(f"{status} '{file_path}' vs '{query}': score={score}")

        assert matched == should_match, f"匹配结果不符合预期: {file_path} vs {query}"

    print("✓ 匹配评分正确")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_real_project():
    """Test with real project (current directory)"""
    completer = FileNameCompleter(str(project_root), cache_duration=1)

    print("\n[测试 7] 真实项目测试")
    print("=" * 50)

    # Test completing "cli"
    document = Document('cli')
    completions = list(completer.get_completions(document, None))

    print(f"输入: 'cli'")
    print(f"补全结果 ({len(completions)} 个):")
    for comp in completions[:10]:
        print(f"  - {comp.text} ({comp.display_meta})")

    assert len(completions) > 0, "应该找到包含 'cli' 的文件"
    print(f"✓ 在真实项目中找到 {len(completions)} 个匹配文件")

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("文件名补全功能测试")
    print("=" * 50)

    results = []

    # Run tests
    try:
        results.append(("基本文件名补全", test_filename_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("基本文件名补全", False))

    try:
        results.append(("文件扩展名优先级", test_extension_filtering()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("文件扩展名优先级", False))

    try:
        results.append(("路径补全", test_path_completion()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("路径补全", False))

    try:
        results.append(("缓存机制", test_caching()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("缓存机制", False))

    try:
        results.append(("跳过特定目录", test_skip_directories()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("跳过特定目录", False))

    try:
        results.append(("匹配评分算法", test_match_scoring()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("匹配评分算法", False))

    try:
        results.append(("真实项目测试", test_real_project()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("真实项目测试", False))

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
