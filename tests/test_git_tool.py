#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git tool usage examples and tests
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools.git import git, GitError


def setup_test_repo():
    """Create a test git repository"""
    temp_dir = tempfile.mkdtemp(prefix='git_test_')

    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=temp_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=temp_dir, capture_output=True)

    # Create initial file
    test_file = Path(temp_dir) / 'test.txt'
    test_file.write_text('Initial content\n')

    return temp_dir


def example_1_basic_status():
    """示例 1: 查看 Git 状态"""
    print("\n" + "="*60)
    print("示例 1: 查看 Git 状态")
    print("="*60)

    repo_dir = setup_test_repo()

    # 调用 git status
    result = git(action='status', args={}, project_root=repo_dir)

    print(f"✅ 成功: {result['success']}")
    print(f"📄 输出:\n{result['output']}")

    # 清理
    import shutil
    shutil.rmtree(repo_dir)


def example_2_add_and_commit():
    """示例 2: 添加文件并提交"""
    print("\n" + "="*60)
    print("示例 2: 添加文件并提交")
    print("="*60)

    repo_dir = setup_test_repo()

    # 1. Add file
    print("\n1️⃣ 添加文件到暂存区")
    result = git(
        action='add',
        args={'files': ['test.txt']},
        project_root=repo_dir
    )
    print(f"   ✅ 成功: {result['success']}")

    # 2. Commit
    print("\n2️⃣ 创建提交")
    result = git(
        action='commit',
        args={'message': 'Initial commit'},
        project_root=repo_dir
    )
    print(f"   ✅ 成功: {result['success']}")
    print(f"   📄 输出: {result['output'].strip()}")

    # 3. Show log
    print("\n3️⃣ 查看提交历史")
    result = git(
        action='log',
        args={'count': 1, 'oneline': True},
        project_root=repo_dir
    )
    print(f"   ✅ 成功: {result['success']}")
    print(f"   📄 输出: {result['output'].strip()}")

    # 清理
    import shutil
    shutil.rmtree(repo_dir)


def example_3_branch_operations():
    """示例 3: 分支操作"""
    print("\n" + "="*60)
    print("示例 3: 分支操作")
    print("="*60)

    repo_dir = setup_test_repo()

    # Initial commit
    subprocess.run(['git', 'add', 'test.txt'], cwd=repo_dir, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_dir, capture_output=True)

    # 1. List branches
    print("\n1️⃣ 列出分支")
    result = git(
        action='branch',
        args={'operation': 'list'},
        project_root=repo_dir
    )
    print(f"   ✅ 成功: {result['success']}")
    print(f"   📄 输出: {result['output'].strip()}")

    # 2. Create new branch
    print("\n2️⃣ 创建新分支 'feature'")
    result = git(
        action='branch',
        args={'operation': 'create', 'name': 'feature'},
        project_root=repo_dir
    )
    print(f"   ✅ 成功: {result['success']}")

    # 3. Checkout branch
    print("\n3️⃣ 切换到 'feature' 分支")
    result = git(
        action='checkout',
        args={'target': 'feature'},
        project_root=repo_dir
    )
    print(f"   ✅ 成功: {result['success']}")

    # 4. List branches again
    print("\n4️⃣ 再次列出分支")
    result = git(
        action='branch',
        args={'operation': 'list'},
        project_root=repo_dir
    )
    print(f"   📄 输出: {result['output'].strip()}")

    # 清理
    import shutil
    shutil.rmtree(repo_dir)


def example_4_dangerous_operations():
    """示例 4: 危险操作检测"""
    print("\n" + "="*60)
    print("示例 4: 危险操作检测")
    print("="*60)

    from backend.agent.tool_confirmation import ToolConfirmation

    confirmation = ToolConfirmation()

    # 1. 安全的 reset
    print("\n1️⃣ 安全的 reset (mixed)")
    args = {'mode': 'mixed', 'target': 'HEAD~1'}
    is_dangerous = confirmation.is_dangerous_git_operation('reset', args)
    print(f"   ⚠️  危险操作: {is_dangerous}")

    # 2. 危险的 reset --hard
    print("\n2️⃣ 危险的 reset --hard")
    args = {'mode': 'hard', 'target': 'HEAD~1'}
    is_dangerous = confirmation.is_dangerous_git_operation('reset', args)
    print(f"   ⚠️  危险操作: {is_dangerous}")

    # 3. 正常的 push
    print("\n3️⃣ 正常的 push")
    args = {'remote': 'origin', 'branch': 'main'}
    is_dangerous = confirmation.is_dangerous_git_operation('push', args)
    print(f"   ⚠️  危险操作: {is_dangerous}")

    # 4. 危险的 push --force
    print("\n4️⃣ 危险的 push --force")
    args = {'remote': 'origin', 'branch': 'main', 'force': True}
    is_dangerous = confirmation.is_dangerous_git_operation('push', args)
    print(f"   ⚠️  危险操作: {is_dangerous}")

    # 5. Rebase (总是危险)
    print("\n5️⃣ Rebase (总是需要确认)")
    args = {'operation': 'start', 'branch': 'main'}
    is_dangerous = confirmation.is_dangerous_git_operation('rebase', args)
    print(f"   ⚠️  危险操作: {is_dangerous}")


def example_5_confirmation_signatures():
    """示例 5: 确认签名"""
    print("\n" + "="*60)
    print("示例 5: 确认签名 (细粒度控制)")
    print("="*60)

    from backend.agent.tool_confirmation import ToolConfirmation

    confirmation = ToolConfirmation()

    # Git operations with different actions
    operations = [
        ('status', {}),
        ('log', {'count': 10}),
        ('add', {'files': ['test.txt']}),
        ('commit', {'message': 'Test'}),
        ('push', {'remote': 'origin', 'branch': 'main'}),
    ]

    print("\n各个 Git 操作的签名:")
    for action, args in operations:
        arguments = {'action': action, 'args': args}
        signature = confirmation._get_tool_signature('git', arguments)
        print(f"  • {action:12s} → 签名: {signature}")

    print("\n" + "-"*60)
    print("说明:")
    print("  - 每个 action 都有独立的签名")
    print("  - 可以单独设置 '始终允许'")
    print("  - 例如: git:status 允许后，git:push 仍需确认")


def example_6_real_world_workflow():
    """示例 6: 真实工作流程"""
    print("\n" + "="*60)
    print("示例 6: 真实开发工作流程")
    print("="*60)

    repo_dir = setup_test_repo()

    # Setup initial commit
    subprocess.run(['git', 'add', 'test.txt'], cwd=repo_dir, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_dir, capture_output=True)

    # Workflow
    print("\n📋 工作流程:")

    # 1. Check status
    print("\n1️⃣ 检查状态")
    result = git(action='status', args={}, project_root=repo_dir)
    print(f"   ✅ {result['output'].strip()}")

    # 2. Create new file
    print("\n2️⃣ 创建新文件")
    new_file = Path(repo_dir) / 'feature.txt'
    new_file.write_text('New feature\n')
    print(f"   ✅ 创建了 feature.txt")

    # 3. Check status again
    print("\n3️⃣ 再次检查状态")
    result = git(action='status', args={}, project_root=repo_dir)
    print(f"   📄 输出:\n{result['output']}")

    # 4. Add new file
    print("\n4️⃣ 添加新文件")
    result = git(action='add', args={'files': ['feature.txt']}, project_root=repo_dir)
    print(f"   ✅ 成功: {result['success']}")

    # 5. Commit
    print("\n5️⃣ 提交更改")
    result = git(
        action='commit',
        args={'message': 'feat: Add new feature'},
        project_root=repo_dir
    )
    print(f"   ✅ 提交: {result['output'].strip()}")

    # 6. View log
    print("\n6️⃣ 查看历史")
    result = git(action='log', args={'count': 5, 'oneline': True}, project_root=repo_dir)
    print(f"   📄 历史:\n{result['output']}")

    # 7. Show diff
    print("\n7️⃣ 查看最后一次提交的差异")
    result = git(action='show', args={'commit': 'HEAD'}, project_root=repo_dir)
    print(f"   📄 输出 (前 200 字符):\n{result['output'][:200]}...")

    # 清理
    import shutil
    shutil.rmtree(repo_dir)


def example_7_error_handling():
    """示例 7: 错误处理"""
    print("\n" + "="*60)
    print("示例 7: 错误处理")
    print("="*60)

    repo_dir = setup_test_repo()

    # 1. 提交没有 message
    print("\n1️⃣ 尝试提交但缺少 message")
    result = git(action='commit', args={}, project_root=repo_dir)
    print(f"   ✅ 成功: {result['success']}")
    print(f"   ❌ 错误: {result['error']}")

    # 2. 添加不存在的文件
    print("\n2️⃣ 尝试添加不存在的文件")
    result = git(action='add', args={'files': ['nonexistent.txt']}, project_root=repo_dir)
    print(f"   ✅ 成功: {result['success']}")
    if not result['success']:
        print(f"   ❌ 错误: {result['error']}")

    # 3. 切换到不存在的分支
    print("\n3️⃣ 尝试切换到不存在的分支")
    result = git(action='checkout', args={'target': 'nonexistent'}, project_root=repo_dir)
    print(f"   ✅ 成功: {result['success']}")
    if not result['success']:
        print(f"   ❌ 错误: {result['error']}")

    # 清理
    import shutil
    shutil.rmtree(repo_dir)


if __name__ == '__main__':
    print("\n" + "🚀 " + "="*56)
    print("Git Tool 使用示例")
    print("="*60)

    try:
        example_1_basic_status()
        example_2_add_and_commit()
        example_3_branch_operations()
        example_4_dangerous_operations()
        example_5_confirmation_signatures()
        example_6_real_world_workflow()
        example_7_error_handling()

        print("\n" + "="*60)
        print("✅ 所有示例运行完成！")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
