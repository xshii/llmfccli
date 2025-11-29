# -*- coding: utf-8 -*-
"""
工具 Schema 增强器

为工具 schema 添加详细的示例、约束和说明
"""

from typing import Dict, Any


class SchemaEnhancer:
    """Schema 增强器，为工具添加详细的使用示例"""

    # 工具使用示例
    TOOL_EXAMPLES = {
        'view_file': {
            'examples': [
                {
                    'description': '读取整个文件',
                    'arguments': {
                        'path': 'src/main.cpp'
                    }
                },
                {
                    'description': '读取文件的特定行范围（10-50行）',
                    'arguments': {
                        'path': 'src/main.cpp',
                        'line_range': [10, 50]
                    }
                },
                {
                    'description': '读取文件从第10行到文件末尾',
                    'arguments': {
                        'path': 'src/main.cpp',
                        'line_range': [10, -1]
                    }
                }
            ],
            'parameter_constraints': {
                'path': {
                    'type': 'string',
                    'required': True,
                    'description': '文件路径（相对于项目根目录或绝对路径）',
                    'examples': ['src/main.cpp', 'include/header.h', './test.cpp']
                },
                'line_range': {
                    'type': 'array',
                    'required': False,
                    'description': '行范围 [start, end]，使用 -1 表示文件末尾',
                    'examples': [[10, 50], [1, 100], [10, -1]],
                    'constraints': 'start >= 1, end >= start 或 end == -1'
                }
            }
        },
        'edit_file': {
            'examples': [
                {
                    'description': '替换函数实现',
                    'arguments': {
                        'path': 'src/main.cpp',
                        'old_str': 'void process() {\n    // old implementation\n}',
                        'new_str': 'void process() {\n    // new implementation\n    std::cout << "Processing...";\n}'
                    }
                }
            ],
            'parameter_constraints': {
                'path': {
                    'type': 'string',
                    'required': True,
                    'description': '文件路径',
                    'examples': ['src/main.cpp', 'include/header.h']
                },
                'old_str': {
                    'type': 'string',
                    'required': True,
                    'description': '要替换的字符串（必须在文件中唯一出现）',
                    'constraints': '必须在文件中恰好出现一次，否则会报错'
                },
                'new_str': {
                    'type': 'string',
                    'required': True,
                    'description': '替换后的字符串'
                },
                'confirm': {
                    'type': 'boolean',
                    'required': False,
                    'description': '是否需要用户确认',
                    'default': True
                }
            },
            'common_errors': [
                'old_str 在文件中不存在',
                'old_str 在文件中出现多次（不唯一）',
                '换行符使用错误（应该使用 \\n）'
            ]
        },
        'create_file': {
            'examples': [
                {
                    'description': '创建 C++ 源文件',
                    'arguments': {
                        'path': 'src/new_module.cpp',
                        'content': '#include <iostream>\n\nint main() {\n    std::cout << "Hello";\n    return 0;\n}'
                    }
                }
            ],
            'parameter_constraints': {
                'path': {
                    'type': 'string',
                    'required': True,
                    'description': '文件路径（如果父目录不存在会自动创建）'
                },
                'content': {
                    'type': 'string',
                    'required': True,
                    'description': '文件内容'
                }
            }
        },
        'grep_search': {
            'examples': [
                {
                    'description': '在 src 目录搜索类定义',
                    'arguments': {
                        'pattern': 'class.*Handler',
                        'scope': 'src/'
                    }
                },
                {
                    'description': '在所有 .cpp 文件中搜索函数定义',
                    'arguments': {
                        'pattern': 'void.*process',
                        'scope': '.',
                        'file_pattern': '*.cpp'
                    }
                }
            ],
            'parameter_constraints': {
                'pattern': {
                    'type': 'string',
                    'required': True,
                    'description': '搜索模式（正则表达式）',
                    'examples': ['class.*Handler', 'void.*process', '#include.*iostream']
                },
                'scope': {
                    'type': 'string',
                    'required': True,
                    'description': '搜索范围目录',
                    'examples': ['.', 'src/', 'backend/', 'include/']
                },
                'file_pattern': {
                    'type': 'string',
                    'required': False,
                    'description': '文件模式过滤',
                    'examples': ['*.cpp', '*.h', '*.{cpp,h}']
                }
            }
        },
        'list_dir': {
            'examples': [
                {
                    'description': '列出当前目录',
                    'arguments': {
                        'path': '.'
                    }
                },
                {
                    'description': '列出 src 目录，最大深度 2',
                    'arguments': {
                        'path': 'src/',
                        'max_depth': 2
                    }
                }
            ],
            'parameter_constraints': {
                'path': {
                    'type': 'string',
                    'required': False,
                    'description': '目录路径',
                    'default': '.',
                    'examples': ['.', 'src/', 'include/']
                },
                'max_depth': {
                    'type': 'integer',
                    'required': False,
                    'description': '最大遍历深度',
                    'default': 3,
                    'examples': [1, 2, 3, 5]
                }
            }
        }
    }

    @classmethod
    def enhance_schema(cls, tool_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强工具 schema，添加示例和约束

        Args:
            tool_name: 工具名称
            schema: 原始 schema

        Returns:
            增强后的 schema
        """
        if tool_name not in cls.TOOL_EXAMPLES:
            return schema

        enhanced = schema.copy()
        tool_info = cls.TOOL_EXAMPLES[tool_name]

        # 添加示例到描述中
        if 'function' in enhanced:
            func = enhanced['function']

            # 添加使用示例到描述
            if 'examples' in tool_info:
                examples_text = "\n\n使用示例:\n"
                for i, example in enumerate(tool_info['examples'], 1):
                    examples_text += f"{i}. {example['description']}:\n"
                    examples_text += f"   {example['arguments']}\n"

                func['description'] = func.get('description', '') + examples_text

            # 增强参数约束
            if 'parameter_constraints' in tool_info and 'parameters' in func:
                params = func['parameters']
                if 'properties' in params:
                    for param_name, constraints in tool_info['parameter_constraints'].items():
                        if param_name in params['properties']:
                            # 添加更详细的描述
                            param = params['properties'][param_name]
                            enhanced_desc = constraints.get('description', param.get('description', ''))

                            if 'examples' in constraints:
                                enhanced_desc += f"\n示例: {constraints['examples']}"

                            if 'constraints' in constraints:
                                enhanced_desc += f"\n约束: {constraints['constraints']}"

                            if 'default' in constraints:
                                enhanced_desc += f"\n默认值: {constraints['default']}"

                            param['description'] = enhanced_desc

        return enhanced

    @classmethod
    def get_tool_usage_guide(cls, tool_name: str) -> str:
        """获取工具的详细使用指南"""
        if tool_name not in cls.TOOL_EXAMPLES:
            return f"工具 '{tool_name}' 没有可用的使用指南"

        tool_info = cls.TOOL_EXAMPLES[tool_name]
        guide = f"=== {tool_name} 使用指南 ===\n\n"

        # 参数约束
        if 'parameter_constraints' in tool_info:
            guide += "参数说明:\n"
            for param_name, constraints in tool_info['parameter_constraints'].items():
                required = "必需" if constraints.get('required', False) else "可选"
                guide += f"  {param_name} ({required}, {constraints.get('type', 'any')}): "
                guide += constraints.get('description', '') + "\n"

                if 'default' in constraints:
                    guide += f"    默认值: {constraints['default']}\n"

                if 'examples' in constraints:
                    guide += f"    示例: {constraints['examples']}\n"

                if 'constraints' in constraints:
                    guide += f"    约束: {constraints['constraints']}\n"

            guide += "\n"

        # 使用示例
        if 'examples' in tool_info:
            guide += "使用示例:\n"
            for i, example in enumerate(tool_info['examples'], 1):
                guide += f"{i}. {example['description']}\n"
                guide += f"   {example['arguments']}\n\n"

        # 常见错误
        if 'common_errors' in tool_info:
            guide += "常见错误:\n"
            for error in tool_info['common_errors']:
                guide += f"  - {error}\n"

        return guide
