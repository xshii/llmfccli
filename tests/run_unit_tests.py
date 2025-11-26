#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试运行器 - 仅运行单元测试（快速，不需要 LLM）
"""

import sys
import os
import subprocess

# 单元测试列表
UNIT_TESTS = [
    ('unit/test_tools_only.py', '文件系统工具测试'),
    ('unit/test_ollama_hello.py', 'Ollama 连接测试'),
    ('unit/test_basic.py', '基础功能测试'),
    ('unit/test_tool_executor.py', 'ToolExecutor 接口测试'),
    ('unit/test_executor.py', 'Bash/Executor 工具测试'),
    ('unit/test_precheck.py', 'PreCheck 环境检查测试'),
    ('unit/test_confirmation.py', '工具确认系统测试'),
    ('unit/test_enhanced_cli.py', '增强 CLI 功能测试'),
    ('unit/test_vscode.py', 'VSCode 集成测试'),
    ('test_rpc_integration.py', 'RPC 基础功能测试'),
    ('test_rpc_e2e_simple.py', 'RPC E2E 集成测试'),
]


def run_unit_tests():
    """运行单元测试"""

    tests_dir = os.path.dirname(__file__)
    passed = 0
    failed = 0
    errors = 0

    print("=" * 60)
    print("Claude-Qwen 单元测试")
    print("=" * 60)
    print(f"总计: {len(UNIT_TESTS)} 个测试\n")

    for test_file, description in UNIT_TESTS:
        test_path = os.path.join(tests_dir, test_file)

        print(f"\n运行: {description}")
        print(f"文件: {test_file}")
        print("-" * 60)

        try:
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=60  # 单元测试 1 分钟超时
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
    print("\n" + "=" * 60)
    print("单元测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(UNIT_TESTS)}")
    print(f"失败: {failed}/{len(UNIT_TESTS)}")
    print(f"错误: {errors}/{len(UNIT_TESTS)}")

    if failed > 0 or errors > 0:
        print("\n部分测试失败，请检查输出")
        return 1
    else:
        print("\n所有单元测试通过！")
        return 0


if __name__ == '__main__':
    sys.exit(run_unit_tests())
