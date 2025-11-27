#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test adaptive cache duration functionality
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.cli_completer import FileNameCompleter


def create_small_project():
    """Create a small test project (< 100 files)"""
    temp_dir = tempfile.mkdtemp(prefix='test_small_')
    for i in range(50):
        Path(os.path.join(temp_dir, f'file_{i}.txt')).touch()
    return temp_dir


def create_medium_project():
    """Create a medium test project (100-1000 files)"""
    temp_dir = tempfile.mkdtemp(prefix='test_medium_')
    for i in range(500):
        Path(os.path.join(temp_dir, f'file_{i}.txt')).touch()
    return temp_dir


def create_large_project():
    """Create a large test project (1000-5000 files)"""
    temp_dir = tempfile.mkdtemp(prefix='test_large_')

    # Create multiple subdirectories
    for dir_i in range(10):
        dir_path = os.path.join(temp_dir, f'dir_{dir_i}')
        os.makedirs(dir_path)
        for file_i in range(150):
            Path(os.path.join(dir_path, f'file_{file_i}.txt')).touch()

    return temp_dir


def test_small_project_cache():
    """Test cache duration for small project"""
    temp_dir = create_small_project()
    completer = FileNameCompleter(temp_dir, cache_duration=None)

    print("\n[测试 1] 小型项目缓存策略")
    print("=" * 60)

    # Trigger scan
    files = completer._get_files()
    cache_info = completer.get_cache_info()

    print(f"文件数量: {cache_info['file_count']}")
    print(f"扫描耗时: {cache_info['last_scan_duration_ms']:.2f} ms")
    print(f"缓存时长: {cache_info['cache_duration']} 秒")
    print(f"自适应模式: {cache_info['adaptive_mode']}")

    # Small project should have ~30s cache
    assert cache_info['file_count'] == 50, f"Expected 50 files, got {cache_info['file_count']}"
    assert 25 <= cache_info['cache_duration'] <= 60, \
        f"Small project cache should be 30-60s, got {cache_info['cache_duration']}"
    assert cache_info['adaptive_mode'] is True, "Adaptive mode should be enabled"

    print("✓ 小型项目使用 30 秒缓存")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_medium_project_cache():
    """Test cache duration for medium project"""
    temp_dir = create_medium_project()
    completer = FileNameCompleter(temp_dir, cache_duration=None)

    print("\n[测试 2] 中型项目缓存策略")
    print("=" * 60)

    # Trigger scan
    files = completer._get_files()
    cache_info = completer.get_cache_info()

    print(f"文件数量: {cache_info['file_count']}")
    print(f"扫描耗时: {cache_info['last_scan_duration_ms']:.2f} ms")
    print(f"缓存时长: {cache_info['cache_duration']} 秒")
    print(f"自适应模式: {cache_info['adaptive_mode']}")

    # Medium project should have ~60s cache (may increase if scan is slow)
    assert cache_info['file_count'] == 500, f"Expected 500 files, got {cache_info['file_count']}"
    assert 50 <= cache_info['cache_duration'] <= 120, \
        f"Medium project cache should be 60-120s, got {cache_info['cache_duration']}"

    print("✓ 中型项目使用 60+ 秒缓存")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_large_project_cache():
    """Test cache duration for large project"""
    temp_dir = create_large_project()
    completer = FileNameCompleter(temp_dir, cache_duration=None)

    print("\n[测试 3] 大型项目缓存策略")
    print("=" * 60)

    # Trigger scan
    files = completer._get_files()
    cache_info = completer.get_cache_info()

    print(f"文件数量: {cache_info['file_count']}")
    print(f"扫描耗时: {cache_info['last_scan_duration_ms']:.2f} ms")
    print(f"缓存时长: {cache_info['cache_duration']} 秒")
    print(f"自适应模式: {cache_info['adaptive_mode']}")

    # Large project should have 120s+ cache
    assert cache_info['file_count'] == 1500, f"Expected 1500 files, got {cache_info['file_count']}"
    assert 100 <= cache_info['cache_duration'] <= 300, \
        f"Large project cache should be 120-300s, got {cache_info['cache_duration']}"

    print("✓ 大型项目使用 120+ 秒缓存")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_fixed_cache_mode():
    """Test that fixed cache mode doesn't change"""
    temp_dir = create_small_project()

    # Use fixed 90s cache
    completer = FileNameCompleter(temp_dir, cache_duration=90)

    print("\n[测试 4] 固定缓存模式")
    print("=" * 60)

    # Trigger scan
    files = completer._get_files()
    cache_info = completer.get_cache_info()

    print(f"文件数量: {cache_info['file_count']}")
    print(f"缓存时长: {cache_info['cache_duration']} 秒")
    print(f"自适应模式: {cache_info['adaptive_mode']}")

    # Cache should remain at 90s
    assert cache_info['cache_duration'] == 90, \
        f"Fixed cache should be 90s, got {cache_info['cache_duration']}"
    assert cache_info['adaptive_mode'] is False, "Adaptive mode should be disabled"

    print("✓ 固定缓存模式保持不变（90 秒）")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_cache_refresh():
    """Test that cache refreshes after expiration"""
    temp_dir = create_small_project()
    completer = FileNameCompleter(temp_dir, cache_duration=None)

    print("\n[测试 5] 缓存刷新机制")
    print("=" * 60)

    # First scan
    files1 = completer._get_files()
    cache_info1 = completer.get_cache_info()
    print(f"首次扫描: {cache_info1['file_count']} 文件, 缓存 {cache_info1['cache_duration']}s")

    # Should use cache (immediate second call)
    start = time.time()
    files2 = completer._get_files()
    elapsed = time.time() - start

    print(f"缓存读取耗时: {elapsed*1000:.2f} ms")
    assert elapsed < 0.01, "Cache read should be very fast"
    assert files1 == files2, "Cache should return same files"

    print("✓ 缓存机制工作正常")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def test_real_project_adaptive():
    """Test adaptive cache on real project"""
    completer = FileNameCompleter(str(project_root), cache_duration=None)

    print("\n[测试 6] 真实项目自适应缓存")
    print("=" * 60)

    # Scan real project
    files = completer._get_files()
    cache_info = completer.get_cache_info()

    print(f"文件数量: {cache_info['file_count']}")
    print(f"扫描耗时: {cache_info['last_scan_duration_ms']:.2f} ms")
    print(f"缓存时长: {cache_info['cache_duration']} 秒 ({cache_info['cache_duration']//60} 分钟)")
    print(f"自适应模式: {cache_info['adaptive_mode']}")

    # Should have reasonable cache time
    assert cache_info['cache_duration'] >= 30, "Cache should be at least 30s"
    assert cache_info['cache_duration'] <= 600, "Cache should not exceed 10min"

    print(f"✓ 真实项目使用 {cache_info['cache_duration']} 秒缓存")

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("自适应缓存功能测试")
    print("=" * 60)

    results = []

    # Run tests
    try:
        results.append(("小型项目缓存", test_small_project_cache()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("小型项目缓存", False))

    try:
        results.append(("中型项目缓存", test_medium_project_cache()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("中型项目缓存", False))

    try:
        results.append(("大型项目缓存", test_large_project_cache()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("大型项目缓存", False))

    try:
        results.append(("固定缓存模式", test_fixed_cache_mode()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("固定缓存模式", False))

    try:
        results.append(("缓存刷新机制", test_cache_refresh()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("缓存刷新机制", False))

    try:
        results.append(("真实项目自适应", test_real_project_adaptive()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("真实项目自适应", False))

    # Print summary
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

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
