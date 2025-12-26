# -*- coding: utf-8 -*-
"""
GitTool - Git 版本控制工具类
"""

import json
from typing import Dict, Any, Optional, List, Literal, Union
from pydantic import BaseModel, Field, field_validator

from backend.tools.base import BaseTool
from .git import git, GitError


class GitParams(BaseModel):
    """Git 工具参数"""
    action: Literal[
        'status', 'add', 'commit', 'reset',
        'branch', 'checkout', 'push', 'pull', 'fetch',
        'rebase', 'stash', 'cherry-pick',
        'log', 'diff', 'show', 'clean', 'mr'
    ] = Field(description="Git 操作类型")
    args: Optional[Dict[str, Any]] = Field(
        default=None,
        description="""操作参数说明（所有 action 均支持可选 flags:str 传递额外标志）:
- status: short(bool), branch(bool). flags: --porcelain --long
- add: files(list,条件必需), all(bool). flags: -u --update
- commit: message(str,必需), amend(bool), no_edit(bool). flags: --allow-empty --no-verify
- reset: mode(str:soft/mixed/hard), commit(str), files(list). flags: --keep
- branch: operation(str:list/create/delete/rename), name(str,条件必需), all(bool), force(bool). flags: -v -r --remote
- checkout: branch(str,条件必需), files(list,条件必需), create(bool), force(bool). flags: --track -t
- push: remote(str), branch(str), force(bool). flags: -u --set-upstream --tags
- pull: remote(str), branch(str), rebase(bool). flags: --ff-only --no-ff
- fetch: remote(str), all(bool), prune(bool). flags: --tags --depth=N
- log: n(int,必需). flags: --oneline --graph --all --author=X --since=X
- diff: commit(str), files(list). flags: --staged --cached --stat --name-only --name-status
- show: commit(str). flags: --stat --name-only --format=X
- stash: operation(str:push/pop/apply/list/drop/clear), message(str), index(int). flags: -u --include-untracked
- rebase: operation(str:start/continue/abort/skip), branch(str,条件必需). flags: --onto=X
- cherry-pick: operation(str:pick/continue/abort), commits(list,条件必需). flags: -n --no-commit
- clean: flags(str,默认-fdx). flags: -f -d -x -fd -fdx
- mr: title(str,必需), description(str,必需), dest_branch(str,必需,优先从 system reminder 提取 Main branch)"""
    )

    @field_validator('args', mode='before')
    @classmethod
    def parse_args_json(cls, v: Union[str, Dict, None]) -> Optional[Dict[str, Any]]:
        """Parse args from JSON string if needed (LLM sometimes sends stringified JSON)"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                # If parsed result is not a dict, return as-is for Pydantic to validate
                return v
            except json.JSONDecodeError:
                # Not valid JSON, return as-is for Pydantic to validate
                return v
        return v


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
    def priority(self) -> int:
        return 30

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
            'clean': lambda a: True,  # clean 总是需要确认（会删除文件）
            'mr': lambda a: True,  # mr 是高危操作，总是需要确认
        }

        checker = dangerous_conditions.get(action)
        if checker:
            return checker(args)

        return False
