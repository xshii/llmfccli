# -*- coding: utf-8 -*-
"""
Git branch-related commands: branch, checkout, rebase, stash, cherry-pick
"""

from typing import Dict

from backend.tools.base import ToolResult
from .base import parse_flags, run_git_command


def git_branch(args: Dict, project_root: str) -> ToolResult:
    """Branch operations"""
    operation = args.get('operation', 'list')
    cmd = ['branch']

    if operation == 'list':
        if args.get('all'):
            cmd.append('--all')

    elif operation == 'create':
        name = args.get('name')
        if not name:
            return ToolResult.fail('Branch name required')
        cmd.append(name)
        if args.get('force'):
            cmd.insert(1, '-f')

    elif operation == 'delete':
        name = args.get('name')
        if not name:
            return ToolResult.fail('Branch name required')
        cmd.append('-d' if not args.get('force') else '-D')
        cmd.append(name)

    elif operation == 'rename':
        old_name = args.get('name')
        new_name = args.get('new_name')
        if not new_name:
            return ToolResult.fail('New branch name required')
        cmd.append('-m')
        if old_name:
            cmd.extend([old_name, new_name])
        else:
            cmd.append(new_name)

    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)


def git_checkout(args: Dict, project_root: str) -> ToolResult:
    """Checkout branch or restore files"""
    branch = args.get('branch')
    files = args.get('files', [])

    if not branch and not files:
        return ToolResult.fail('branch or files required')

    cmd = ['checkout']

    if branch:
        if args.get('create'):
            cmd.append('-b')
        if args.get('force'):
            cmd.append('-f')
        cmd.append(branch)
    else:
        if isinstance(files, str):
            files = [files]
        cmd.append('--')
        cmd.extend(files)

    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)


def git_rebase(args: Dict, project_root: str) -> ToolResult:
    """Rebase operations"""
    operation = args.get('operation', 'start')
    cmd = ['rebase']

    if operation == 'continue':
        cmd.append('--continue')
    elif operation == 'abort':
        cmd.append('--abort')
    elif operation == 'skip':
        cmd.append('--skip')
    elif operation == 'start':
        branch = args.get('branch')
        if not branch:
            return ToolResult.fail('Branch required')

        cmd.extend(parse_flags(args.get('flags', '')))
        cmd.append(branch)

    return run_git_command(cmd, project_root, timeout=120)


def git_stash(args: Dict, project_root: str) -> ToolResult:
    """Stash operations"""
    operation = args.get('operation', 'push')
    cmd = ['stash']

    if operation == 'push':
        cmd.append('push')
        message = args.get('message')
        if message:
            cmd.extend(['-m', message])
        cmd.extend(parse_flags(args.get('flags', '')))

    elif operation == 'pop':
        cmd.append('pop')
        index = args.get('index')
        if index is not None:
            cmd.append(f'stash@{{{index}}}')

    elif operation == 'apply':
        cmd.append('apply')
        index = args.get('index')
        if index is not None:
            cmd.append(f'stash@{{{index}}}')

    elif operation == 'list':
        cmd.append('list')

    elif operation == 'drop':
        cmd.append('drop')
        index = args.get('index')
        if index is not None:
            cmd.append(f'stash@{{{index}}}')

    elif operation == 'clear':
        cmd.append('clear')

    return run_git_command(cmd, project_root)


def git_cherry_pick(args: Dict, project_root: str) -> ToolResult:
    """Cherry-pick commits"""
    operation = args.get('operation', 'pick')
    cmd = ['cherry-pick']

    if operation == 'continue':
        cmd.append('--continue')
    elif operation == 'abort':
        cmd.append('--abort')
    elif operation == 'pick':
        commits = args.get('commits', [])
        if isinstance(commits, str):
            commits = [commits]
        if not commits:
            return ToolResult.fail('Commits required')

        cmd.extend(parse_flags(args.get('flags', '')))
        cmd.extend(commits)

    return run_git_command(cmd, project_root)
