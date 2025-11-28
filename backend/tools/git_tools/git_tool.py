# -*- coding: utf-8 -*-
"""
GitTool - Git 版本控制工具类
"""

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from .git import git, GitError


class GitParams(BaseModel):
    """Git 工具参数"""
    action: Literal[
        'status', 'add', 'commit', 'reset',
        'branch', 'checkout', 'push', 'pull', 'fetch',
        'rebase', 'stash', 'cherry-pick',
        'log', 'diff', 'show'
    ] = Field(description="Git 操作类型")
    args: Optional[Dict[str, Any]] = Field(
        default=None,
        description="操作参数，例如 {'message': 'commit msg'} 或 {'files': ['a.py']}"
    )


class GitTool(BaseTool):
    """Git 版本控制工具"""

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return "Execute git version control operations (status, add, commit, push, pull, etc.)"

    @property
    def category(self) -> str:
        return "git"

    @property
    def parameters_model(self):
        return GitParams

    def execute(self, action: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行 Git 操作"""
        return git(action, args or {}, self.project_root)
