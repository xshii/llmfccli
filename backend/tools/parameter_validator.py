# -*- coding: utf-8 -*-
"""
工具参数验证和自动修正模块

处理模型传递的常见参数错误，尝试自动修正
"""

from typing import Dict, Any, Tuple, Optional
import json


class ParameterValidator:
    """参数验证器，用于检测和修正常见的参数错误"""

    # 常见的参数名映射（错误 -> 正确）
    PARAMETER_MAPPING = {
        'view_file': {
            'file': 'path',
            'file_path': 'path',
            'filepath': 'path',
            'filename': 'path',
            'lines': 'line_range',
            'line_numbers': 'line_range',
            'start_line': lambda args: ('line_range', [args.get('start_line'), args.get('end_line', -1)]),
            'end_line': lambda args: None,  # 已在 start_line 中处理
        },
        'edit_file': {
            'file': 'path',
            'file_path': 'path',
            'find': 'old_str',
            'search': 'old_str',
            'old': 'old_str',
            'replace': 'new_str',
            'replacement': 'new_str',
            'new': 'new_str',
        },
        'create_file': {
            'file': 'path',
            'file_path': 'path',
            'filepath': 'path',
            'data': 'content',
            'text': 'content',
            'body': 'content',
        },
        'grep_search': {
            'search': 'pattern',
            'query': 'pattern',
            'regex': 'pattern',
            'directory': 'scope',
            'dir': 'scope',
            'path': 'scope',
            'in': 'scope',
            'filter': 'file_pattern',
            'glob': 'file_pattern',
        },
        'list_dir': {
            'directory': 'path',
            'dir': 'path',
            'folder': 'path',
            'depth': 'max_depth',
        }
    }

    @classmethod
    def validate_and_fix(cls, tool_name: str, arguments: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        验证并尝试修正参数

        Args:
            tool_name: 工具名称
            arguments: 原始参数

        Returns:
            (修正后的参数, 警告信息)
        """
        if tool_name not in cls.PARAMETER_MAPPING:
            # 未知工具，不做修正
            return arguments, None

        mapping = cls.PARAMETER_MAPPING[tool_name]
        fixed_args = {}
        warnings = []

        for key, value in arguments.items():
            if key in mapping:
                # 需要映射
                correct_key = mapping[key]

                if callable(correct_key):
                    # 复杂映射（如 start_line/end_line -> line_range）
                    result = correct_key(arguments)
                    if result:
                        correct_name, correct_value = result
                        fixed_args[correct_name] = correct_value
                        warnings.append(f"参数 '{key}' 已自动修正为 '{correct_name}'")
                else:
                    # 简单映射
                    fixed_args[correct_key] = value
                    warnings.append(f"参数 '{key}' 已自动修正为 '{correct_key}'")
            else:
                # 参数名正确
                fixed_args[key] = value

        # 类型修正
        fixed_args, type_warnings = cls._fix_types(tool_name, fixed_args)
        warnings.extend(type_warnings)

        warning_msg = "; ".join(warnings) if warnings else None
        return fixed_args, warning_msg

    @classmethod
    def _fix_types(cls, tool_name: str, arguments: Dict[str, Any]) -> Tuple[Dict[str, Any], list]:
        """修正参数类型"""
        fixed_args = arguments.copy()
        warnings = []

        # view_file 特殊处理
        if tool_name == 'view_file' and 'line_range' in fixed_args:
            line_range = fixed_args['line_range']

            # 处理字符串形式的 line_range
            if isinstance(line_range, str):
                try:
                    # 尝试解析 JSON
                    fixed_args['line_range'] = json.loads(line_range)
                    warnings.append("line_range 从字符串转换为数组")
                except:
                    # 尝试解析 "10-20" 或 "10,20" 格式
                    if '-' in line_range:
                        parts = line_range.split('-')
                    elif ',' in line_range:
                        parts = line_range.split(',')
                    else:
                        parts = []

                    if len(parts) == 2:
                        try:
                            fixed_args['line_range'] = [int(parts[0]), int(parts[1])]
                            warnings.append(f"line_range 从字符串 '{line_range}' 转换为数组")
                        except ValueError:
                            pass

            # 确保是整数数组
            elif isinstance(line_range, (list, tuple)) and len(line_range) == 2:
                fixed_args['line_range'] = [int(line_range[0]), int(line_range[1])]

        # edit_file 的 confirm 参数
        if tool_name == 'edit_file' and 'confirm' in fixed_args:
            confirm = fixed_args['confirm']

            # 字符串转布尔
            if isinstance(confirm, str):
                if confirm.lower() in ('true', 'yes', '1'):
                    fixed_args['confirm'] = True
                    warnings.append("confirm 从字符串转换为布尔值 true")
                elif confirm.lower() in ('false', 'no', '0'):
                    fixed_args['confirm'] = False
                    warnings.append("confirm 从字符串转换为布尔值 false")

        # list_dir 的 max_depth 参数
        if tool_name == 'list_dir' and 'max_depth' in fixed_args:
            max_depth = fixed_args['max_depth']

            # 字符串转整数
            if isinstance(max_depth, str):
                try:
                    fixed_args['max_depth'] = int(max_depth)
                    warnings.append(f"max_depth 从字符串 '{max_depth}' 转换为整数")
                except ValueError:
                    pass

        return fixed_args, warnings

    @classmethod
    def get_parameter_hints(cls, tool_name: str) -> str:
        """获取工具的参数使用提示"""
        hints = {
            'view_file': """
参数说明:
  - path (必需): 文件路径，如 "src/main.cpp"
  - line_range (可选): 行范围 [起始, 结束]，如 [10, 50]

示例: {"path": "src/main.cpp", "line_range": [10, 50]}
""",
            'edit_file': """
参数说明:
  - path (必需): 文件路径
  - old_str (必需): 要替换的字符串（必须在文件中唯一）
  - new_str (必需): 替换后的字符串
  - confirm (可选): 是否确认，布尔值 true/false

示例: {"path": "main.cpp", "old_str": "old code", "new_str": "new code"}
""",
            'create_file': """
参数说明:
  - path (必需): 文件路径
  - content (必需): 文件内容

示例: {"path": "new.cpp", "content": "#include <iostream>"}
""",
            'grep_search': """
参数说明:
  - pattern (必需): 搜索模式（正则表达式）
  - scope (必需): 搜索范围，如 ".", "src/"
  - file_pattern (可选): 文件过滤，如 "*.cpp"

示例: {"pattern": "class.*Handler", "scope": "src/", "file_pattern": "*.cpp"}
""",
            'list_dir': """
参数说明:
  - path (可选): 目录路径，默认 "."
  - max_depth (可选): 最大深度，默认 3

示例: {"path": "src/", "max_depth": 2}
"""
        }

        return hints.get(tool_name, "无可用的参数提示")

    @classmethod
    def generate_error_feedback(cls, tool_name: str, error_msg: str, arguments: Dict[str, Any]) -> str:
        """
        生成友好的错误反馈，帮助模型纠正错误

        Args:
            tool_name: 工具名称
            error_msg: 原始错误信息
            arguments: 使用的参数

        Returns:
            友好的错误反馈信息
        """
        feedback = f"工具 '{tool_name}' 调用失败: {error_msg}\n\n"
        feedback += f"你使用的参数:\n{json.dumps(arguments, ensure_ascii=False, indent=2)}\n\n"
        feedback += cls.get_parameter_hints(tool_name)
        feedback += "\n请检查参数名称和类型是否正确，然后重试。"

        return feedback
