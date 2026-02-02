# -*- coding: utf-8 -*-
"""
Git info commands: log, diff, show, clean
"""

from typing import Dict

from backend.tools.base import ToolResult
from .base import parse_flags, run_git_command


def git_log(args: Dict, project_root: str) -> ToolResult:
    """Show commit logs"""
    cmd = ['log']

    n = args.get('n')
    if not n:
        return ToolResult.fail('n (number of commits) is required')
    cmd.append(f'-{n}')

    flags = args.get('flags', '')
    if not flags or ('oneline' not in flags and 'format' not in flags):
        cmd.append('--oneline')

    cmd.extend(parse_flags(flags))
    return run_git_command(cmd, project_root)


def git_diff(args: Dict, project_root: str) -> ToolResult:
    """Show changes"""
    cmd = ['diff']

    cmd.extend(parse_flags(args.get('flags', '')))

    commit = args.get('commit')
    if commit:
        cmd.append(commit)

    files = args.get('files', [])
    if files:
        if isinstance(files, str):
            files = [files]
        cmd.append('--')
        cmd.extend(files)

    return run_git_command(cmd, project_root)


def git_show(args: Dict, project_root: str) -> ToolResult:
    """Show commit details"""
    cmd = ['show']

    commit = args.get('commit', 'HEAD')
    cmd.append(commit)

    cmd.extend(parse_flags(args.get('flags', '')))
    return run_git_command(cmd, project_root)


def git_clean(args: Dict, project_root: str) -> ToolResult:
    """Clean untracked files"""
    cmd = ['clean']

    flags = args.get('flags', '-fdx')

    parsed_flags = parse_flags(flags)
    has_force = any(f in ['-f', '--force'] or 'f' in f for f in parsed_flags)
    if not has_force:
        cmd.append('-f')

    cmd.extend(parsed_flags)
    return run_git_command(cmd, project_root)
