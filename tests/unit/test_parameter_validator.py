#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试参数验证器
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.parameter_validator import ParameterValidator


def test_view_file_parameter_fix():
    """测试 view_file 参数修正"""
    print("\n[Test 1] view_file 参数修正")

    # Test 1.1: file -> path
    args = {'file': 'main.cpp'}
    fixed, warning = ParameterValidator.validate_and_fix('view_file', args)
    print(f"  输入: {args}")
    print(f"  输出: {fixed}")
    print(f"  警告: {warning}")
    assert fixed == {'path': 'main.cpp'}, "file 应该被修正为 path"
    print("  ✓ file -> path 修正正确")

    # Test 1.2: lines -> line_range
    args = {'path': 'main.cpp', 'lines': [10, 20]}
    fixed, warning = ParameterValidator.validate_and_fix('view_file', args)
    print(f"\n  输入: {args}")
    print(f"  输出: {fixed}")
    assert fixed == {'path': 'main.cpp', 'line_range': [10, 20]}, "lines 应该被修正为 line_range"
    print("  ✓ lines -> line_range 修正正确")

    # Test 1.3: start_line + end_line -> line_range
    args = {'path': 'main.cpp', 'start_line': 10, 'end_line': 20}
    fixed, warning = ParameterValidator.validate_and_fix('view_file', args)
    print(f"\n  输入: {args}")
    print(f"  输出: {fixed}")
    assert fixed == {'path': 'main.cpp', 'line_range': [10, 20]}, "start_line/end_line 应该被合并为 line_range"
    print("  ✓ start_line + end_line -> line_range 修正正确")


def test_edit_file_parameter_fix():
    """测试 edit_file 参数修正"""
    print("\n[Test 2] edit_file 参数修正")

    # Test 2.1: find/replace -> old_str/new_str
    args = {'file': 'test.cpp', 'find': 'old', 'replace': 'new'}
    fixed, warning = ParameterValidator.validate_and_fix('edit_file', args)
    print(f"  输入: {args}")
    print(f"  输出: {fixed}")
    expected = {'path': 'test.cpp', 'old_str': 'old', 'new_str': 'new'}
    assert fixed == expected, f"应该修正为 {expected}"
    print("  ✓ 参数修正正确")

    # Test 2.2: confirm 字符串转布尔
    args = {'path': 'test.cpp', 'old_str': 'a', 'new_str': 'b', 'confirm': 'true'}
    fixed, warning = ParameterValidator.validate_and_fix('edit_file', args)
    print(f"\n  输入: {args}")
    print(f"  输出: {fixed}")
    assert fixed['confirm'] == True, "字符串 'true' 应该转为布尔值 True"
    assert isinstance(fixed['confirm'], bool), "confirm 应该是布尔类型"
    print("  ✓ 类型转换正确")


def test_grep_search_parameter_fix():
    """测试 grep_search 参数修正"""
    print("\n[Test 3] grep_search 参数修正")

    args = {'search': 'class', 'directory': 'src/'}
    fixed, warning = ParameterValidator.validate_and_fix('grep_search', args)
    print(f"  输入: {args}")
    print(f"  输出: {fixed}")
    expected = {'pattern': 'class', 'scope': 'src/'}
    assert fixed == expected, f"应该修正为 {expected}"
    print("  ✓ 参数修正正确")


def test_list_dir_parameter_fix():
    """测试 list_dir 参数修正"""
    print("\n[Test 4] list_dir 参数修正")

    # Test 4.1: directory -> path
    args = {'directory': 'src/', 'depth': 2}
    fixed, warning = ParameterValidator.validate_and_fix('list_dir', args)
    print(f"  输入: {args}")
    print(f"  输出: {fixed}")
    expected = {'path': 'src/', 'max_depth': 2}
    assert fixed == expected, f"应该修正为 {expected}"
    print("  ✓ 参数修正正确")

    # Test 4.2: max_depth 字符串转整数
    args = {'path': 'src/', 'max_depth': '5'}
    fixed, warning = ParameterValidator.validate_and_fix('list_dir', args)
    print(f"\n  输入: {args}")
    print(f"  输出: {fixed}")
    assert fixed['max_depth'] == 5, "字符串 '5' 应该转为整数 5"
    assert isinstance(fixed['max_depth'], int), "max_depth 应该是整数类型"
    print("  ✓ 类型转换正确")


def test_parameter_hints():
    """测试参数提示"""
    print("\n[Test 5] 参数使用提示")

    hints = ParameterValidator.get_parameter_hints('view_file')
    print(f"  view_file 提示:\n{hints}")
    assert 'path' in hints, "提示中应包含 path 参数"
    assert 'line_range' in hints, "提示中应包含 line_range 参数"
    print("  ✓ 参数提示正确")


def test_error_feedback():
    """测试错误反馈生成"""
    print("\n[Test 6] 错误反馈生成")

    args = {'file': 'main.cpp', 'lines': [10, 20]}
    feedback = ParameterValidator.generate_error_feedback(
        'view_file',
        '未知参数 file',
        args
    )
    print(f"  错误反馈:\n{feedback}")
    assert 'view_file' in feedback, "反馈中应包含工具名称"
    assert 'path' in feedback, "反馈中应包含正确的参数名"
    print("  ✓ 错误反馈正确")


def test_correct_parameters():
    """测试正确参数不会被修改"""
    print("\n[Test 7] 正确参数保持不变")

    args = {'path': 'main.cpp', 'line_range': [10, 20]}
    fixed, warning = ParameterValidator.validate_and_fix('view_file', args)
    print(f"  输入: {args}")
    print(f"  输出: {fixed}")
    assert fixed == args, "正确的参数不应该被修改"
    assert warning is None, "正确的参数不应该产生警告"
    print("  ✓ 正确参数保持不变")


if __name__ == '__main__':
    print("=" * 60)
    print("参数验证器测试")
    print("=" * 60)

    try:
        test_view_file_parameter_fix()
        test_edit_file_parameter_fix()
        test_grep_search_parameter_fix()
        test_list_dir_parameter_fix()
        test_parameter_hints()
        test_error_feedback()
        test_correct_parameters()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
