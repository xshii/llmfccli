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

    def get_confirmation_signature(self, arguments: Dict[str, Any]) -> str:
        """按 action 分组确认，例如 git:push, git:commit"""
        action = arguments.get('action', '')
        return f"{self.name}:{action}"

    def is_dangerous_operation(self, arguments: Dict[str, Any]) -> bool:
        """检查 Git 操作是否危险"""
        action = arguments.get('action', '')
        args = arguments.get('args', {}) or {}

        dangerous_conditions = {
            'reset': lambda a: a.get('mode') == 'hard',
            'push': lambda a: a.get('force') == True,
            'branch': lambda a: a.get('operation') == 'delete' and a.get('force'),
            'rebase': lambda a: True,  # rebase 总是需要确认
            'stash': lambda a: a.get('operation') in ['drop', 'clear'],
            'cherry-pick': lambda a: True,  # cherry-pick 总是需要确认
        }

        checker = dangerous_conditions.get(action)
        if checker:
            return checker(args)

        return False
