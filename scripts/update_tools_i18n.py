#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新工具文件，添加 get_parameters_i18n 方法
"""

import os
import sys

# 工具文件的参数多语言描述
TOOLS_I18N = {
    'view_file.py': {
        'imports_remove': ['from backend.i18n import field_description'],
        'params_class': 'ViewFileParams',
        'params_fields': [
            ('path', 'File path (relative to project root or absolute path)'),
            ('line_range', 'Optional line range [start_line, end_line] (1-indexed, use -1 for end of file)'),
        ],
        'tool_class': 'ViewFileTool',
        'params_i18n': {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）'
            },
            'line_range': {
                'en': 'Optional line range [start_line, end_line] (1-indexed, use -1 for end of file)',
                'zh': '可选的行范围 [start_line, end_line]（1-indexed，使用 -1 表示文件末尾）'
            }
        }
    },
    'edit_file.py': {
        'params_i18n': {
            'path': {
                'en': 'File path',
                'zh': '文件路径'
            },
            'old_str': {
                'en': 'String to replace (must appear exactly once)',
                'zh': '要替换的字符串（必须唯一出现）'
            },
            'new_str': {
                'en': 'Replacement string',
                'zh': '替换后的字符串'
            },
            'confirm': {
                'en': 'Whether to confirm before editing (default true)',
                'zh': '是否需要用户确认（默认 true）'
            }
        }
    },
    'list_dir.py': {
        'params_i18n': {
            'path': {
                'en': "Directory path (default '.')",
                'zh': "目录路径（默认 '.'）"
            },
            'max_depth': {
                'en': 'Maximum traversal depth (default 3)',
                'zh': '最大遍历深度（默认 3）'
            }
        }
    },
    'create_file.py': {
        'params_i18n': {
            'path': {
                'en': 'File path',
                'zh': '文件路径'
            },
            'content': {
                'en': 'File content',
                'zh': '文件内容'
            }
        }
    },
    'grep_search.py': {
        'params_i18n': {
            'pattern': {
                'en': 'Search pattern (regex)',
                'zh': '搜索模式（regex）'
            },
            'scope': {
                'en': "Search scope directory (e.g., '.', 'src/', 'backend/')",
                'zh': "搜索范围目录（如 '.', 'src/', 'backend/'）"
            },
            'file_pattern': {
                'en': "Optional file pattern filter (e.g., '*.cpp')",
                'zh': "可选的文件模式过滤（如 '*.cpp'）"
            }
        }
    }
}


def add_parameters_i18n_method(tool_file, params_i18n):
    """为工具类添加 get_parameters_i18n 方法"""

    with open(tool_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 移除 field_description 导入
    if 'from backend.i18n import field_description' in content:
        content = content.replace('from backend.i18n import field_description\n', '')
        content = content.replace(', field_description', '')

    # 2. 简化参数定义中的 description（移除 field_description 包装）
    import re

    # 替换 description=field_description({...})
    def replace_field_desc(match):
        # 提取英文描述
        inner = match.group(1)
        # 查找 'en': '...' 部分
        en_match = re.search(r"'en':\s*'([^']+)'", inner)
        if en_match:
            return f'description="{en_match.group(1)}"'
        en_match2 = re.search(r"'en':\s*\"([^\"]+)\"", inner)
        if en_match2:
            return f'description="{en_match2.group(1)}"'
        return match.group(0)

    content = re.sub(
        r'description=field_description\(\{([^}]+)\}\)',
        replace_field_desc,
        content,
        flags=re.DOTALL
    )

    # 3. 在 description_i18n 方法后添加 get_parameters_i18n 方法
    # 找到 description_i18n 方法的位置
    desc_i18n_match = re.search(
        r'(    @property\n    def description_i18n\(self\) -> Dict\[str, str\]:.*?\n        \})\n',
        content,
        re.DOTALL
    )

    if desc_i18n_match:
        # 构建 get_parameters_i18n 方法
        method = '\n\n    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:\n        return {\n'

        for param_name, translations in params_i18n.items():
            method += f"            '{param_name}': {{\n"
            for lang, desc in translations.items():
                # 转义单引号
                desc_escaped = desc.replace("'", "\\'")
                method += f"                '{lang}': '{desc_escaped}',\n"
            method += '            },\n'

        method += '        }'

        # 插入方法
        insert_pos = desc_i18n_match.end()
        content = content[:insert_pos] + method + content[insert_pos:]

    # 写回文件
    with open(tool_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Updated {os.path.basename(tool_file)}")


def main():
    tools_dir = os.path.join(os.path.dirname(__file__), '../backend/tools/filesystem_tools')

    for filename, config in TOOLS_I18N.items():
        tool_file = os.path.join(tools_dir, filename)

        if os.path.exists(tool_file):
            params_i18n = config['params_i18n']
            add_parameters_i18n_method(tool_file, params_i18n)
        else:
            print(f"✗ File not found: {tool_file}")

    print("\n✅ All tools updated!")


if __name__ == '__main__':
    main()
