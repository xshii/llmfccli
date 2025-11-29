#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试路径压缩功能 - 基于字符长度的智能裁剪
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.cli.path_utils import PathUtils


def test_path_compression():
    """测试路径压缩的各种场景"""

    project_root = '/home/user/llmfccli'
    path_utils = PathUtils(project_root)

    print("=" * 70)
    print("测试路径压缩 - 基于50字符长度限制")
    print("=" * 70)

    test_cases = [
        # (输入路径, 期望行为, 最大长度)
        # 项目内路径 - 短路径（不压缩）
        (
            f"{project_root}/backend/tools.py",
            "不压缩（19字符 < 50）",
            50,
            "backend/tools.py"
        ),
        # 项目内路径 - 中等长度（不压缩）
        (
            f"{project_root}/tests/unit/test_basic.py",
            "不压缩（27字符 < 50）",
            50,
            "tests/unit/test_basic.py"
        ),
        # 项目内路径 - 需要压缩
        (
            f"{project_root}/backend/agent/tools/filesystem/view_file.py",
            "压缩（49字符接近50）",
            50,
            None  # 动态检查长度
        ),
        # 项目内路径 - 深层嵌套
        (
            f"{project_root}/a/very/long/deeply/nested/path/to/some/file.py",
            "压缩（55字符 > 50）",
            50,
            None
        ),
        # 项目外路径 - 短路径（不压缩）
        (
            "/usr/lib/python3.11/site-packages/module.py",
            "不压缩（44字符 < 50）",
            50,
            "/usr/lib/python3.11/site-packages/module.py"
        ),
        # 项目外路径 - 需要压缩
        (
            "/home/user/other/project/src/backend/api/v1/endpoints/users.py",
            "压缩（64字符 > 50）",
            50,
            None
        ),
        # 自定义长度限制
        (
            f"{project_root}/backend/agent/tools.py",
            "20字符限制，需要压缩",
            20,
            None
        ),
        (
            f"{project_root}/backend/agent/tools.py",
            "30字符限制，不需要压缩",
            30,
            "backend/agent/tools.py"
        ),
    ]

    passed = 0
    failed = 0

    for i, (path, description, max_len, expected) in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {description}")
        print(f"  输入路径: {path}")
        print(f"  最大长度: {max_len}")

        compressed = path_utils.compress_path(path, max_length=max_len)
        print(f"  压缩结果: {compressed}")
        print(f"  结果长度: {len(compressed)}")

        # 检查压缩后长度是否符合要求
        if len(compressed) > max_len:
            print(f"  ❌ 失败：压缩后长度 {len(compressed)} 超过限制 {max_len}")
            failed += 1
            continue

        # 如果有期望结果，检查是否匹配
        if expected is not None:
            if compressed == expected:
                print(f"  ✅ 通过：结果符合预期")
                passed += 1
            else:
                print(f"  ❌ 失败：期望 '{expected}'，实际 '{compressed}'")
                failed += 1
        else:
            # 只检查长度限制
            print(f"  ✅ 通过：长度符合要求")
            passed += 1

    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 70)

    # 额外测试：验证压缩策略的智能性
    print("\n" + "=" * 70)
    print("额外测试：验证压缩策略的智能性")
    print("=" * 70)

    # Test: 逐步增加路径长度，观察压缩效果
    print("\n[智能测试 1] 逐步增加路径深度，观察压缩点")
    base = f"{project_root}/backend"
    paths = [
        f"{base}/tools.py",
        f"{base}/agent/tools.py",
        f"{base}/agent/tools/registry.py",
        f"{base}/agent/tools/filesystem/view.py",
        f"{base}/agent/tools/filesystem/edit/advanced.py",
    ]

    for path in paths:
        # 计算相对路径
        rel_path = os.path.relpath(path, project_root)
        compressed = path_utils.compress_path(path, max_length=30)
        print(f"  原始: {rel_path:45s} ({len(rel_path):2d}字符)")
        print(f"  压缩: {compressed:45s} ({len(compressed):2d}字符)")
        print()

    # Test: 文件名很长的情况
    print("\n[智能测试 2] 文件名本身很长的情况")
    long_filename = f"{project_root}/src/this_is_a_very_long_filename_that_exceeds_limit.py"
    compressed = path_utils.compress_path(long_filename, max_length=30)
    print(f"  原始: {os.path.relpath(long_filename, project_root)}")
    print(f"  压缩: {compressed} ({len(compressed)}字符)")
    assert len(compressed) <= 30, "文件名压缩失败"
    print("  ✅ 文件名正确截断")

    # Test: 边界情况 - 刚好50字符
    print("\n[智能测试 3] 边界情况测试")
    # 构造一个刚好50字符的路径
    # backend/agent/tools/filesystem/view_file.py = 44字符
    exact_path = f"{project_root}/backend/agent/tools/filesystem/test.py"
    rel = os.path.relpath(exact_path, project_root)
    print(f"  路径: {rel} ({len(rel)}字符)")

    compressed = path_utils.compress_path(exact_path, max_length=len(rel))
    print(f"  压缩(max={len(rel)}): {compressed}")
    assert compressed == rel, "相同长度不应压缩"
    print("  ✅ 边界情况正确处理")

    compressed = path_utils.compress_path(exact_path, max_length=len(rel) - 1)
    print(f"  压缩(max={len(rel)-1}): {compressed} ({len(compressed)}字符)")
    assert len(compressed) <= len(rel) - 1, "压缩后应符合长度限制"
    print("  ✅ 超出1字符正确压缩")

    print("\n" + "=" * 70)
    if failed == 0:
        print("✅ 所有测试通过！")
    else:
        print(f"❌ 有 {failed} 个测试失败")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    success = test_path_compression()
    sys.exit(0 if success else 1)
