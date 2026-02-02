# -*- coding: utf-8 -*-
"""
Git remote-related commands: push, pull, fetch, mr
"""

import os
from typing import Dict

from backend.tools.base import ToolResult
from .base import parse_flags, run_git_command


def git_push(args: Dict, project_root: str) -> ToolResult:
    """Push to remote"""
    cmd = ['push']

    if args.get('force'):
        cmd.append('--force')

    cmd.extend(parse_flags(args.get('flags', '')))

    remote = args.get('remote', 'origin')
    branch = args.get('branch', '')

    cmd.append(remote)
    if branch:
        cmd.append(branch)

    return run_git_command(cmd, project_root, timeout=60)


def git_pull(args: Dict, project_root: str) -> ToolResult:
    """Pull from remote"""
    cmd = ['pull']

    if args.get('rebase'):
        cmd.append('--rebase')

    cmd.extend(parse_flags(args.get('flags', '')))

    remote = args.get('remote', 'origin')
    branch = args.get('branch', '')

    cmd.append(remote)
    if branch:
        cmd.append(branch)

    return run_git_command(cmd, project_root, timeout=60)


def git_fetch(args: Dict, project_root: str) -> ToolResult:
    """Fetch from remote"""
    cmd = ['fetch']

    if args.get('all'):
        cmd.append('--all')
    if args.get('prune', True):
        cmd.append('--prune')

    cmd.extend(parse_flags(args.get('flags', '')))

    remote = args.get('remote', 'origin')
    if not args.get('all'):
        cmd.append(remote)

    return run_git_command(cmd, project_root, timeout=60)


def git_mr(args: Dict, project_root: str) -> ToolResult:
    """Create merge request (custom operation)

    Args:
        args: {
            'title': str,           # MR title (-T), prefer Chinese
            'description': str,     # MR description (-D), prefer Chinese
            'dest_branch': str,     # Destination branch (--dest)
        }
    """
    cmd = ['mr']

    title = args.get('title')
    if not title:
        return ToolResult.fail('Title is required for merge request (-T)')

    dest_branch = args.get('dest_branch')
    if not dest_branch:
        return ToolResult.fail('Destination branch is required (--dest)')

    description = args.get('description')
    if not description:
        return ToolResult.fail('Description is required (-D)')

    # Default flags: -y (auto confirm) -f (force)
    cmd.extend(['-y', '-f'])

    cmd.extend(['--dest', dest_branch])
    cmd.extend(['-T', title])
    cmd.extend(['-D', description])

    # Setup environment to disable interactive prompts
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_ASKPASS'] = 'echo'

    return run_git_command(cmd, project_root, timeout=30, env=env, stdin_devnull=True)
