# -*- coding: utf-8 -*-
"""
Git commands modules

拆分的 git 命令模块:
- base: 基础工具函数
- commit: status, add, commit, reset
- branch: branch, checkout, rebase, stash, cherry-pick
- remote: push, pull, fetch, mr
- info: log, diff, show, clean
"""

from .base import GitError, parse_flags, run_git_command
from .commit import git_status, git_add, git_commit, git_reset
from .branch import git_branch, git_checkout, git_rebase, git_stash, git_cherry_pick
from .remote import git_push, git_pull, git_fetch, git_mr
from .info import git_log, git_diff, git_show, git_clean

__all__ = [
    # Base
    'GitError',
    'parse_flags',
    'run_git_command',
    # Commit operations
    'git_status',
    'git_add',
    'git_commit',
    'git_reset',
    # Branch operations
    'git_branch',
    'git_checkout',
    'git_rebase',
    'git_stash',
    'git_cherry_pick',
    # Remote operations
    'git_push',
    'git_pull',
    'git_fetch',
    'git_mr',
    # Info operations
    'git_log',
    'git_diff',
    'git_show',
    'git_clean',
]
