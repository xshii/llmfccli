# -*- coding: utf-8 -*-
"""
Test system_reminder module
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.cli.system_reminder import SystemReminder, get_system_reminder, get_main_branch


def test_load_config():
    """测试加载配置"""
    reminder = SystemReminder()
    assert reminder._config is not None
    print("✓ Config loaded successfully")


def test_get_main_branch():
    """测试获取主分支名称"""
    branch = get_main_branch()
    print(f"✓ Main branch: {branch}")
    assert isinstance(branch, str)


def test_get_git_hints():
    """测试获取 Git 提示"""
    reminder = SystemReminder()
    hints = reminder.get_git_hints()
    print(f"✓ Git hints ({len(hints)}):")
    for hint in hints:
        print(f"  - {hint}")


def test_get_project_hints():
    """测试获取项目提示"""
    reminder = SystemReminder()
    hints = reminder.get_project_hints()
    print(f"✓ Project hints ({len(hints)}):")
    for hint in hints:
        print(f"  - {hint}")


def test_get_custom_hints():
    """测试获取自定义提示"""
    reminder = SystemReminder()
    hints = reminder.get_custom_hints()
    print(f"✓ Custom hints ({len(hints)}):")
    for hint in hints:
        print(f"  - {hint}")


def test_generate_system_reminder():
    """测试生成完整的 system reminder"""
    reminder_text = get_system_reminder()
    print("✓ Generated system reminder:")
    print("-" * 60)
    if reminder_text:
        print(reminder_text)
    else:
        print("(empty)")
    print("-" * 60)


if __name__ == "__main__":
    print("Testing SystemReminder module...")
    print()

    test_load_config()
    test_get_main_branch()
    test_get_git_hints()
    test_get_project_hints()
    test_get_custom_hints()
    test_generate_system_reminder()

    print()
    print("All tests passed! ✓")
