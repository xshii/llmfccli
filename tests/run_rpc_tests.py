#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPC 测试运行器 - 仅运行 RPC 相关测试（快速，不需要 VSCode）
"""

import sys
import os
import subprocess

# RPC 测试列表
RPC_TESTS = [
    ('test_rpc_integration.py', 'RPC 基础功能测试'),
    ('unit/test_vscode.py', 'VSCode 工具 Mock 模式测试'),
    ('test_rpc_e2e_simple.py', 'RPC E2E 集成测试'),
]


def run_rpc_tests():
    """运行 RPC 测试"""

    tests_dir = os.path.dirname(__file__)
    passed = 0
    failed = 0
    errors = 0

    print("=" * 70)
    print("Claude-Qwen RPC 测试套件")
    print("=" * 70)
    print("测试 CLI 与 VSCode 扩展之间的 JSON-RPC 通信")
    print(f"总计: {len(RPC_TESTS)} 个测试\n")

    for test_file, description in RPC_TESTS:
        test_path = os.path.join(tests_dir, test_file)

        print(f"\n运行: {description}")
        print(f"文件: {test_file}")
        print("-" * 70)

        try:
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=30  # RPC 测试 30 秒超时
            )

            # 输出测试结果
            print(result.stdout)

            if result.returncode == 0:
                passed += 1
                print(f"✓ {description} - PASSED")
            else:
                failed += 1
                print(f"✗ {description} - FAILED")
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
    print("\n" + "=" * 70)
    print("RPC 测试总结")
    print("=" * 70)
    print(f"通过: {passed}/{len(RPC_TESTS)}")
    print(f"失败: {failed}/{len(RPC_TESTS)}")
    print(f"错误: {errors}/{len(RPC_TESTS)}")

    if failed > 0 or errors > 0:
        print("\n⚠️  部分测试失败，请检查输出")
        print("\n💡 提示:")
        print("  - 这些测试使用 Mock 模式，不需要真实的 VSCode 环境")
        print("  - 如需测试真实 RPC 通信，请参考 docs/RPC_TESTING.md")
        return 1
    else:
        print("\n✅ 所有 RPC 测试通过！")
        print("\n📚 下一步:")
        print("  - 构建 VSCode 扩展: cd vscode-extension && npm install && npm run compile")
        print("  - 安装扩展: code --install-extension claude-qwen-0.1.0.vsix")
        print("  - 在 VSCode 中测试: Cmd+Shift+P → 'Claude-Qwen: Start Assistant'")
        print("  - 详细说明: docs/RPC_TESTING.md")
        return 0


if __name__ == '__main__':
    sys.exit(run_rpc_tests())
