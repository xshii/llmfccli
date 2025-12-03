# -*- coding: utf-8 -*-
"""
Integration test for system reminder
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.cli.main import CLI


def test_system_reminder_injection():
    """测试 system reminder 是否正确注入到上下文中"""

    # 创建 CLI 实例（跳过预检查避免依赖）
    cli = CLI(project_root=str(project_root), skip_precheck=True)

    # 获取 IDE 上下文
    context = cli._get_ide_context()

    print("Generated context:")
    print("=" * 60)
    print(context)
    print("=" * 60)

    # 验证包含 system-reminder 标签
    assert "<system-reminder>" in context
    assert "</system-reminder>" in context

    # 验证包含基本信息
    assert "Project root:" in context
    assert "Current working directory:" in context

    # 验证包含 system reminder 配置的信息
    assert "Main branch" in context or "Project type" in context or "git mr" in context

    print("\n✓ System reminder injection test passed!")


if __name__ == "__main__":
    test_system_reminder_injection()
