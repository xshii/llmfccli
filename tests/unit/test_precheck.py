#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreCheck 工具测试
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.utils.precheck import PreCheck, PreCheckResult


def test_precheck_result():
    """测试 PreCheckResult 基本功能"""
    print("=" * 60)
    print("测试 1: PreCheckResult 基本功能")
    print("=" * 60)

    # Test success result
    result = PreCheckResult(
        name="Test Check",
        success=True,
        message="Test passed",
        details={"key": "value"}
    )

    assert result.name == "Test Check"
    assert result.success is True
    assert result.message == "Test passed"
    assert result.details["key"] == "value"

    output = str(result)
    assert "✓" in output
    assert "Test Check" in output

    print(output)
    print("✓ PreCheckResult 基本功能测试通过\n")


def test_ssh_tunnel_check():
    """测试 SSH 隧道检查"""
    print("=" * 60)
    print("测试 2: SSH 隧道检查")
    print("=" * 60)

    result = PreCheck.check_ssh_tunnel(host="localhost", port=11434)

    print(f"结果: {result}")
    if result.details:
        for key, value in result.details.items():
            print(f"  {key}: {value}")

    # SSH tunnel may or may not be established
    # Just verify the check runs without error
    assert result.name == "SSH Tunnel"
    assert isinstance(result.success, bool)
    assert isinstance(result.message, str)

    print("✓ SSH 隧道检查测试通过\n")


def test_ollama_connection_check():
    """测试 Ollama 连接检查"""
    print("=" * 60)
    print("测试 3: Ollama 连接检查")
    print("=" * 60)

    result = PreCheck.check_ollama_connection(base_url="http://localhost:11434")

    print(f"结果: {result}")
    if result.details:
        for key, value in result.details.items():
            print(f"  {key}: {value}")

    assert result.name == "Ollama Connection"
    assert isinstance(result.success, bool)
    assert isinstance(result.message, str)

    if result.success:
        assert "models" in result.details
        print(f"✓ 发现 {len(result.details['models'])} 个模型")

    print("✓ Ollama 连接检查测试通过\n")


def test_ollama_model_check():
    """测试 Ollama 模型检查"""
    print("=" * 60)
    print("测试 4: Ollama 模型检查")
    print("=" * 60)

    result = PreCheck.check_ollama_model(
        model_name="qwen3:latest",
        base_url="http://localhost:11434"
    )

    print(f"结果: {result}")
    if result.details:
        for key, value in result.details.items():
            print(f"  {key}: {value}")

    assert result.name == "Ollama Model"
    assert isinstance(result.success, bool)

    print("✓ Ollama 模型检查测试通过\n")


def test_ollama_hello():
    """测试 Ollama hello 请求"""
    print("=" * 60)
    print("测试 5: Ollama Hello 测试")
    print("=" * 60)

    result = PreCheck.test_ollama_hello(
        model_name="qwen3:latest",
        base_url="http://localhost:11434"
    )

    print(f"结果: {result}")
    if result.details:
        for key, value in result.details.items():
            print(f"  {key}: {value}")

    assert result.name == "Ollama Hello Test"
    assert isinstance(result.success, bool)

    if result.success:
        assert result.details.get("response_length", 0) > 0
        print("✓ 模型成功响应")

    print("✓ Ollama Hello 测试通过\n")


def test_project_structure_check():
    """测试项目结构检查"""
    print("=" * 60)
    print("测试 6: 项目结构检查")
    print("=" * 60)

    # Test with current project root
    project_root = os.path.join(os.path.dirname(__file__), '../..')
    result = PreCheck.check_project_structure(project_root)

    print(f"结果: {result}")
    if result.details:
        for key, value in result.details.items():
            print(f"  {key}: {value}")

    assert result.name == "Project Structure"
    assert result.success is True  # Our project should have valid structure

    print("✓ 项目结构检查测试通过\n")


def test_run_all_checks():
    """测试运行所有检查"""
    print("=" * 60)
    print("测试 7: 运行所有检查")
    print("=" * 60)

    project_root = os.path.join(os.path.dirname(__file__), '../..')
    results = PreCheck.run_all_checks(
        model_name="qwen3:latest",
        project_root=project_root
    )

    assert len(results) == 5  # Should have 5 checks

    for result in results:
        print(f"  {result}")

    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    print(f"\n通过: {passed}/{len(results)}")
    print(f"失败: {failed}/{len(results)}")

    print("✓ 所有检查执行完成\n")


def test_print_results():
    """测试结果打印功能"""
    print("=" * 60)
    print("测试 8: 结果打印功能")
    print("=" * 60)

    results = [
        PreCheckResult("Check 1", True, "Success", {"detail": "value1"}),
        PreCheckResult("Check 2", False, "Failed", {"detail": "value2"}),
        PreCheckResult("Check 3", True, "Success", {"detail": "value3"}),
    ]

    all_passed = PreCheck.print_results(results, verbose=True)

    assert all_passed is False  # One check failed

    print("✓ 结果打印功能测试通过\n")


def main():
    """运行所有测试"""
    tests = [
        ("PreCheckResult 基本功能", test_precheck_result),
        ("SSH 隧道检查", test_ssh_tunnel_check),
        ("Ollama 连接检查", test_ollama_connection_check),
        ("Ollama 模型检查", test_ollama_model_check),
        ("Ollama Hello 测试", test_ollama_hello),
        ("项目结构检查", test_project_structure_check),
        ("运行所有检查", test_run_all_checks),
        ("结果打印功能", test_print_results),
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print("PreCheck 工具测试套件")
    print("=" * 60)
    print(f"总计: {len(tests)} 个测试\n")

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ {name} - FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"✗ {name} - ERROR: {e}\n")

    # Summary
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print(f"\n❌ {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
