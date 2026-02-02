# -*- coding: utf-8 -*-
"""
Git commit-related commands: status, add, commit, reset
"""

from typing import Dict

from backend.tools.base import ToolResult
from .base import parse_flags, run_git_command


def git_status(args: Dict, project_root: str) -> ToolResult:
    """Get git status"""
    cmd = ['status']
    if args.get('short', True):
        cmd.append('--short')
    if args.get('branch', True):
        cmd.append('--branch')
    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)


def git_add(args: Dict, project_root: str) -> ToolResult:
    """Add files to staging area"""
    cmd = ['add']

    if args.get('all'):
        cmd.append('-A')
    else:
        files = args.get('files', [])
        if isinstance(files, str):
            files = [files]
        if not files:
            return ToolResult.fail('No files specified (use files or all)')
        cmd.extend(files)

    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)


def git_commit(args: Dict, project_root: str) -> ToolResult:
    """Create a commit"""
    message = args.get('message')
    if not message:
        return ToolResult.fail('Commit message is required')

    cmd = ['commit', '-m', message]

    if args.get('amend'):
        cmd.append('--amend')
    if args.get('no_edit'):
        cmd.append('--no-edit')

    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)


def git_reset(args: Dict, project_root: str) -> ToolResult:
    """Reset current HEAD"""
    cmd = ['reset']

    mode = args.get('mode', 'mixed')
    if mode == 'soft':
        cmd.append('--soft')
    elif mode == 'hard':
        cmd.append('--hard')
    elif mode == 'mixed':
        cmd.append('--mixed')

    commit = args.get('commit', 'HEAD')

    files = args.get('files', [])
    if files:
        cmd = ['reset', commit, '--']
        if isinstance(files, str):
            files = [files]
        cmd.extend(files)
    else:
        cmd.append(commit)

    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)
