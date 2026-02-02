# -*- coding: utf-8 -*-
"""
Git version control operations

此模块为向后兼容层，实际实现在 commands/ 子目录中。
"""

import os
from typing import Any, Dict

from backend.tools.base import ToolResult

from .commands import (
    GitError,
    git_status,
    git_add,
    git_commit,
    git_reset,
    git_branch,
    git_checkout,
    git_rebase,
    git_stash,
    git_cherry_pick,
    git_push,
    git_pull,
    git_fetch,
    git_mr,
    git_log,
    git_diff,
    git_show,
    git_clean,
)

# 重新导出供外部使用
__all__ = ['git', 'GitError']


# Action handlers mapping
_HANDLERS = {
    'status': git_status,
    'add': git_add,
    'commit': git_commit,
    'reset': git_reset,
    'branch': git_branch,
    'checkout': git_checkout,
    'push': git_push,
    'pull': git_pull,
    'fetch': git_fetch,
    'rebase': git_rebase,
    'stash': git_stash,
    'cherry-pick': git_cherry_pick,
    'log': git_log,
    'diff': git_diff,
    'show': git_show,
    'clean': git_clean,
    'mr': git_mr,
}


def git(action: str, args: Dict[str, Any] = None, project_root: str = None) -> ToolResult:
    """
    Execute git operations

    Args:
        action: Git action to perform (status, add, commit, push, etc.)
        args: Action-specific arguments
        project_root: Project root directory

    Returns:
        ToolResult with success and output
    """
    if args is None:
        args = {}

    # Validate project_root
    if not project_root:
        raise GitError("project_root is required")

    project_root = os.path.abspath(project_root)
    if not os.path.isdir(project_root):
        raise GitError(f"Invalid project root: {project_root}")

    # Route to specific handler
    handler = _HANDLERS.get(action)
    if not handler:
        return ToolResult.fail(f'Unknown git action: {action}')

    try:
        return handler(args, project_root)
    except Exception as e:
        return ToolResult.fail(str(e))
