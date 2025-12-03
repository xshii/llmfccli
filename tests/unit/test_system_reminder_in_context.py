# -*- coding: utf-8 -*-
"""
Test system reminder injection into context
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_context_generation():
    """测试生成包含 system reminder 的上下文"""
    import os
    from backend.system_reminder import get_system_reminder

    # 模拟 _get_ide_context 的逻辑
    context_parts = []

    # 添加 project root 和 cwd
    context_parts.append(f'Project root: {project_root}')
    current_cwd = os.getcwd()
    context_parts.append(f'Current working directory: {current_cwd}')

    # 添加 system reminder
    system_reminder = get_system_reminder()
    if system_reminder:
        context_parts.append(system_reminder)

    # 组合上下文
    if context_parts:
        context_msg = '\n'.join(context_parts)
        full_context = f"<system-reminder>\n{context_msg}\n</system-reminder>"

    print("Generated context:")
    print("=" * 60)
    print(full_context)
    print("=" * 60)

    # 验证
    assert "<system-reminder>" in full_context
    assert "</system-reminder>" in full_context
    assert "Project root:" in full_context
    assert "Current working directory:" in full_context

    # 验证包含 system reminder 配置的信息（至少一项）
    has_reminder_content = any([
        "Main branch" in full_context,
        "Project type" in full_context
    ])
    assert has_reminder_content, "Should contain at least one system reminder item"

    print("\n✓ Context generation test passed!")


if __name__ == "__main__":
    test_context_generation()
