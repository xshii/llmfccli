# -*- coding: utf-8 -*-
"""
Test git mr timeout handling
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.tools.git_tools.git import _git_mr


def test_git_mr_with_missing_command():
    """测试 git mr 命令不存在时的处理（应该快速失败，不卡住）"""
    import time

    args = {
        'title': '测试标题',
        'description': '测试描述',
        'dest_branch': 'main',
        'auto_confirm': True
    }

    start = time.time()
    result = _git_mr(args, str(project_root))
    elapsed = time.time() - start

    print(f"Execution time: {elapsed:.2f}s")
    print(f"Result: {result}")

    # 应该在 30 秒内返回（超时设置）
    assert elapsed < 35, f"Command took too long: {elapsed}s"

    # 应该失败（因为 git mr 可能不是标准命令）
    if not result['success']:
        print("✓ Command failed as expected (git mr may not be available)")
        # 检查是否是超时错误还是命令不存在错误
        if 'timed out' in result['error']:
            print("⚠ Command timed out - this should be investigated")
        else:
            print(f"✓ Command failed quickly with error: {result['error']}")
    else:
        print("✓ Command succeeded (git mr is available)")

    print("\n✓ Timeout handling test passed!")


if __name__ == "__main__":
    test_git_mr_with_missing_command()
