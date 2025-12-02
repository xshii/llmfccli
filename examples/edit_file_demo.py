#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit_file 工具的使用示例

演示 REPLACE MODE 和 INSERT MODE 的实际使用场景
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.tools.filesystem_tools.edit_file import EditFileTool
from backend.tools.filesystem_tools.view_file import ViewFileTool


def print_file_content(file_path, title):
    """打印文件内容"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            print(f"{i:3d} | {line}", end='')
    print()


def example_1_replace_single_line():
    """
    示例 1: 替换单行 - REPLACE MODE
    场景：修改函数名
    """
    print("\n" + "🔸" * 30)
    print("示例 1: 替换单行（修改函数名）")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        # 创建示例文件
        test_file = Path(project_root) / 'calculator.py'
        test_file.write_text("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
""")

        print_file_content(test_file, "原始文件")

        # 使用 REPLACE MODE 修改第 5 行的函数名
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path='calculator.py',
            line_range=[5, 5],  # REPLACE MODE: 替换第 5 行
            new_content='def sub(a, b):',
            confirm=False
        )

        print(f"\n✅ 操作: {result['message']}")
        print(f"   模式: {result['operation_mode']}")
        print(f"   替换了 {result['old_line_count']} 行，新增 {result['new_line_count']} 行")

        print_file_content(test_file, "修改后的文件")


def example_2_replace_multiple_lines():
    """
    示例 2: 替换多行 - REPLACE MODE
    场景：重构函数实现
    """
    print("\n" + "🔸" * 30)
    print("示例 2: 替换多行（重构函数）")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'auth.py'
        test_file.write_text("""def login(username, password):
    if username == "admin":
        if password == "123456":
            return True
    return False
""")

        print_file_content(test_file, "原始文件（不安全的实现）")

        # 使用 REPLACE MODE 重构函数体
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path='auth.py',
            line_range=[2, 4],  # REPLACE MODE: 替换第 2-4 行
            new_content="""    # 使用安全的密码验证
    user = get_user(username)
    if user and verify_password(password, user.password_hash):
        return True""",
            confirm=False
        )

        print(f"\n✅ 操作: {result['message']}")
        print(f"   模式: {result['operation_mode']}")
        print(f"   替换了 {result['old_line_count']} 行，新增 {result['new_line_count']} 行")

        print_file_content(test_file, "修改后的文件（安全的实现）")


def example_3_insert_after_line():
    """
    示例 3: 在指定行后插入 - INSERT MODE
    场景：在函数后添加新函数
    """
    print("\n" + "🔸" * 30)
    print("示例 3: 在函数后添加新函数")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'math_utils.py'
        test_file.write_text("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

        print_file_content(test_file, "原始文件")

        # 使用 INSERT MODE 在第 2 行后插入新函数
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path='math_utils.py',
            line_range=[3, 2],  # INSERT MODE: 在第 2 行后插入
            new_content="""
def multiply(a, b):
    return a * b""",
            confirm=False
        )

        print(f"\n✅ 操作: {result['message']}")
        print(f"   模式: {result['operation_mode']}")
        print(f"   保留了原有行，插入了 {result['new_line_count']} 行")

        print_file_content(test_file, "修改后的文件（第 2 行保持不变）")


def example_4_insert_at_beginning():
    """
    示例 4: 在文件开头插入 - INSERT MODE
    场景：添加文件头部注释和导入语句
    """
    print("\n" + "🔸" * 30)
    print("示例 4: 在文件开头添加文档和导入")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'server.py'
        test_file.write_text("""def start_server(port):
    print(f"Starting server on port {port}")
    # Server implementation
""")

        print_file_content(test_file, "原始文件（缺少文档和导入）")

        # 使用 INSERT MODE 在开头插入
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path='server.py',
            line_range=[1, 0],  # INSERT MODE: 在文件开头插入
            new_content="""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Server module for handling HTTP requests
\"\"\"

import socket
import threading
""",
            confirm=False
        )

        print(f"\n✅ 操作: {result['message']}")
        print(f"   模式: {result['operation_mode']}")
        print(f"   在开头插入了 {result['new_line_count']} 行")

        print_file_content(test_file, "修改后的文件")


def example_5_insert_import_statement():
    """
    示例 5: 在导入区域添加新导入 - INSERT MODE
    场景：添加缺失的导入语句
    """
    print("\n" + "🔸" * 30)
    print("示例 5: 添加新的导入语句")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'app.py'
        test_file.write_text("""import os
import sys

def main():
    config = load_config()
    start_app(config)
""")

        print_file_content(test_file, "原始文件（缺少 json 导入）")

        # 使用 INSERT MODE 在第 2 行后添加新导入
        tool = EditFileTool(project_root=project_root)
        result = tool.execute(
            path='app.py',
            line_range=[3, 2],  # INSERT MODE: 在第 2 行后插入
            new_content='import json',
            confirm=False
        )

        print(f"\n✅ 操作: {result['message']}")
        print(f"   模式: {result['operation_mode']}")

        print_file_content(test_file, "修改后的文件")


def example_6_add_exception_handling():
    """
    示例 6: 在代码块中插入异常处理 - INSERT MODE
    场景：为现有代码添加 try-except
    """
    print("\n" + "🔸" * 30)
    print("示例 6: 添加异常处理")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        test_file = Path(project_root) / 'file_reader.py'
        test_file.write_text("""def read_config(path):
    with open(path, 'r') as f:
        return json.load(f)
""")

        print_file_content(test_file, "原始文件（没有异常处理）")

        # 步骤 1: 在第 1 行后插入 try:
        tool = EditFileTool(project_root=project_root)
        result1 = tool.execute(
            path='file_reader.py',
            line_range=[2, 1],
            new_content='    try:',
            confirm=False
        )
        print(f"\n✅ 步骤 1: {result1['message']}")

        # 步骤 2: 在第 4 行后插入 except:
        result2 = tool.execute(
            path='file_reader.py',
            line_range=[5, 4],
            new_content="""    except FileNotFoundError:
        raise ValueError(f"Config file not found: {path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in config: {path}")""",
            confirm=False
        )
        print(f"✅ 步骤 2: {result2['message']}")

        print_file_content(test_file, "修改后的文件（添加了异常处理）")


def example_7_comparison():
    """
    示例 7: 对比 REPLACE 和 INSERT 的区别
    """
    print("\n" + "🔸" * 30)
    print("示例 7: REPLACE vs INSERT 对比")
    print("🔸" * 30)

    with tempfile.TemporaryDirectory() as project_root:
        # 场景 A: 使用 REPLACE MODE
        file_a = Path(project_root) / 'example_a.py'
        file_a.write_text("""line1
line2
line3
line4
""")
        print_file_content(file_a, "场景 A: 使用 REPLACE MODE [2, 2]")

        tool = EditFileTool(project_root=project_root)
        tool.execute(
            path='example_a.py',
            line_range=[2, 2],  # REPLACE: 第 2 行被替换
            new_content='NEW_LINE',
            confirm=False
        )
        print_file_content(file_a, "结果: 第 2 行被替换，原内容丢失")

        # 场景 B: 使用 INSERT MODE
        file_b = Path(project_root) / 'example_b.py'
        file_b.write_text("""line1
line2
line3
line4
""")
        print_file_content(file_b, "场景 B: 使用 INSERT MODE [3, 2]")

        tool.execute(
            path='example_b.py',
            line_range=[3, 2],  # INSERT: 在第 2 行后插入
            new_content='NEW_LINE',
            confirm=False
        )
        print_file_content(file_b, "结果: 第 2 行保留，新行插入在第 3 行")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("edit_file 工具使用示例")
    print("="*60)

    example_1_replace_single_line()
    example_2_replace_multiple_lines()
    example_3_insert_after_line()
    example_4_insert_at_beginning()
    example_5_insert_import_statement()
    example_6_add_exception_handling()
    example_7_comparison()

    print("\n" + "="*60)
    print("📚 总结")
    print("="*60)
    print("""
REPLACE MODE (替换模式):
  • line_range=[5, 5]    - 替换第 5 行
  • line_range=[2, 4]    - 替换第 2-4 行
  • 适用场景: 修改现有代码、重构实现

INSERT MODE (插入模式):
  • line_range=[3, 2]    - 在第 2 行后插入（保留第 2 行）
  • line_range=[1, 0]    - 在文件开头插入
  • 适用场景: 添加新函数、添加导入、添加注释
    """)
