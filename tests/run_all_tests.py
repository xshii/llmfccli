#!/usr/bin/env python3
"""
测试运行器 - 按顺序执行所有测试用例
"""

import sys
import os
import subprocess

# 单元测试列表
UNIT_TESTS = [
    ('unit/test_tools_only.py', '文件系统工具测试'),
    ('unit/test_ollama_hello.py', 'Ollama 连接测试'),
    ('unit/test_basic.py', '基础功能测试'),
]

# 端到端测试用例列表（按依赖顺序）
E2E_TESTS = [
    ('e2e/test_case_1.py', '文件定位与功能实现'),
    ('e2e/test_case_2.py', '编译错误自动修复'),
    ('e2e/test_case_3.py', '单元测试生成'),
    ('e2e/test_case_4.py', '集成测试生成'),
    ('e2e/test_case_5.py', '上下文保持'),
    ('e2e/test_case_6.py', '错误恢复'),
]


def run_tests():
    """运行所有测试用例"""

    tests_dir = os.path.dirname(__file__)
    passed = 0
    failed = 0
    errors = 0

    print("=" * 60)
    print("Claude-Qwen 测试套件")
    print("=" * 60)

    # 合并所有测试
    all_tests = UNIT_TESTS + E2E_TESTS

    print(f"\n📋 单元测试: {len(UNIT_TESTS)} 个")
    print(f"📋 端到端测试: {len(E2E_TESTS)} 个")
    print(f"📋 总计: {len(all_tests)} 个\n")

    for test_file, description in all_tests:
        test_path = os.path.join(tests_dir, test_file)
        
        print(f"\n运行: {description}")
        print(f"文件: {test_file}")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 分钟超时
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
    total_tests = len(all_tests)
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{total_tests}")
    print(f"失败: {failed}/{total_tests}")
    print(f"错误: {errors}/{total_tests}")
    
    if failed > 0 or errors > 0:
        print("\n部分测试失败，请检查输出")
        return 1
    else:
        print("\n所有测试通过！")
        return 0


if __name__ == '__main__':
    sys.exit(run_tests())
