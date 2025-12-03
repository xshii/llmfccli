# -*- coding: utf-8 -*-
"""
Git version control operations
"""

import subprocess
import os
from typing import Dict, Any, List, Union
from pathlib import Path


class GitError(Exception):
    """Base exception for git operations"""
    pass


def git(action: str, args: Dict[str, Any] = None, project_root: str = None) -> Dict[str, Any]:
    """
    Execute git operations

    Args:
        action: Git action to perform (status, add, commit, push, etc.)
        args: Action-specific arguments
        project_root: Project root directory

    Returns:
        Dict with 'success', 'output', 'error', 'returncode'
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
    handlers = {
        'status': _git_status,
        'add': _git_add,
        'commit': _git_commit,
        'reset': _git_reset,
        'branch': _git_branch,
        'checkout': _git_checkout,
        'push': _git_push,
        'pull': _git_pull,
        'fetch': _git_fetch,
        'rebase': _git_rebase,
        'stash': _git_stash,
        'cherry-pick': _git_cherry_pick,
        'log': _git_log,
        'diff': _git_diff,
        'show': _git_show,
        'mr': _git_mr,
    }

    handler = handlers.get(action)
    if not handler:
        return {
            'success': False,
            'output': '',
            'error': f'Unknown git action: {action}',
            'returncode': 1
        }

    try:
        return handler(args, project_root)
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'returncode': 1
        }


def _run_git_command(cmd: List[str], cwd: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute git command

    Args:
        cmd: Git command arguments (without 'git' prefix)
        cwd: Working directory
        timeout: Command timeout in seconds

    Returns:
        Dict with execution results
    """
    try:
        result = subprocess.run(
            ['git'] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': f'Command timed out after {timeout} seconds',
            'returncode': 124
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'returncode': 1
        }


def _git_status(args: Dict, project_root: str) -> Dict[str, Any]:
    """Get git status"""
    cmd = ['status']
    if args.get('short', True):
        cmd.append('--short')
    if args.get('branch', True):
        cmd.append('--branch')
    return _run_git_command(cmd, project_root)


def _git_add(args: Dict, project_root: str) -> Dict[str, Any]:
    """Add files to staging area"""
    cmd = ['add']

    if args.get('all'):
        cmd.append('-A')
    elif args.get('update'):
        cmd.append('-u')
    else:
        files = args.get('files', [])
        if isinstance(files, str):
            files = [files]
        if not files:
            return {
                'success': False,
                'output': '',
                'error': 'No files specified',
                'returncode': 1
            }
        cmd.extend(files)

    if args.get('patch'):
        cmd.append('--patch')

    return _run_git_command(cmd, project_root)


def _git_commit(args: Dict, project_root: str) -> Dict[str, Any]:
    """Create a commit"""
    message = args.get('message')
    if not message:
        return {
            'success': False,
            'output': '',
            'error': 'Commit message is required',
            'returncode': 1
        }

    cmd = ['commit', '-m', message]

    if args.get('amend'):
        cmd.append('--amend')
    if args.get('no_verify'):
        cmd.append('--no-verify')
    if args.get('allow_empty'):
        cmd.append('--allow-empty')

    return _run_git_command(cmd, project_root)


def _git_reset(args: Dict, project_root: str) -> Dict[str, Any]:
    """Reset current HEAD"""
    cmd = ['reset']

    mode = args.get('mode', 'mixed')
    if mode == 'soft':
        cmd.append('--soft')
    elif mode == 'hard':
        cmd.append('--hard')
    elif mode == 'mixed':
        cmd.append('--mixed')

    target = args.get('target', 'HEAD')

    files = args.get('files', [])
    if files:
        # Reset specific files (unstage)
        cmd = ['reset', target, '--']
        if isinstance(files, str):
            files = [files]
        cmd.extend(files)
    else:
        cmd.append(target)

    return _run_git_command(cmd, project_root)


def _git_branch(args: Dict, project_root: str) -> Dict[str, Any]:
    """Branch operations"""
    operation = args.get('operation', 'list')
    cmd = ['branch']

    if operation == 'list':
        if args.get('all'):
            cmd.append('--all')
        if args.get('verbose'):
            cmd.append('-v')

    elif operation == 'create':
        name = args.get('name')
        if not name:
            return {'success': False, 'output': '', 'error': 'Branch name required', 'returncode': 1}
        cmd.append(name)
        if args.get('force'):
            cmd.insert(1, '-f')

    elif operation == 'delete':
        name = args.get('name')
        if not name:
            return {'success': False, 'output': '', 'error': 'Branch name required', 'returncode': 1}
        cmd.append('-d' if not args.get('force') else '-D')
        cmd.append(name)

    elif operation == 'rename':
        old_name = args.get('name')
        new_name = args.get('new_name')
        if not new_name:
            return {'success': False, 'output': '', 'error': 'New branch name required', 'returncode': 1}
        cmd.append('-m')
        if old_name:
            cmd.extend([old_name, new_name])
        else:
            cmd.append(new_name)

    return _run_git_command(cmd, project_root)


def _git_checkout(args: Dict, project_root: str) -> Dict[str, Any]:
    """Checkout branch or restore files"""
    target = args.get('target')
    if not target:
        return {'success': False, 'output': '', 'error': 'Target required', 'returncode': 1}

    cmd = ['checkout']

    if args.get('create'):
        cmd.append('-b')
    if args.get('force'):
        cmd.append('-f')

    cmd.append(target)

    track = args.get('track')
    if track:
        cmd.extend(['--track', track])

    return _run_git_command(cmd, project_root)


def _git_push(args: Dict, project_root: str) -> Dict[str, Any]:
    """Push to remote"""
    cmd = ['push']

    remote = args.get('remote', 'origin')
    branch = args.get('branch', '')

    if args.get('set_upstream'):
        cmd.append('-u')
    if args.get('force'):
        cmd.append('--force')
    if args.get('tags'):
        cmd.append('--tags')

    cmd.append(remote)
    if branch:
        cmd.append(branch)

    return _run_git_command(cmd, project_root, timeout=60)


def _git_pull(args: Dict, project_root: str) -> Dict[str, Any]:
    """Pull from remote"""
    cmd = ['pull']

    if args.get('rebase'):
        cmd.append('--rebase')
    if args.get('ff_only'):
        cmd.append('--ff-only')

    remote = args.get('remote', 'origin')
    branch = args.get('branch', '')

    cmd.append(remote)
    if branch:
        cmd.append(branch)

    return _run_git_command(cmd, project_root, timeout=60)


def _git_fetch(args: Dict, project_root: str) -> Dict[str, Any]:
    """Fetch from remote"""
    cmd = ['fetch']

    if args.get('all'):
        cmd.append('--all')
    if args.get('prune', True):
        cmd.append('--prune')

    remote = args.get('remote', 'origin')
    if not args.get('all'):
        cmd.append(remote)

    return _run_git_command(cmd, project_root, timeout=60)


def _git_rebase(args: Dict, project_root: str) -> Dict[str, Any]:
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
            return {'success': False, 'output': '', 'error': 'Branch required', 'returncode': 1}

        if args.get('interactive'):
            cmd.append('-i')

        onto = args.get('onto')
        if onto:
            cmd.extend(['--onto', onto])

        cmd.append(branch)

    return _run_git_command(cmd, project_root, timeout=120)


def _git_stash(args: Dict, project_root: str) -> Dict[str, Any]:
    """Stash operations"""
    operation = args.get('operation', 'save')
    cmd = ['stash']

    if operation == 'save':
        cmd.append('push')
        message = args.get('message')
        if message:
            cmd.extend(['-m', message])
        if args.get('include_untracked'):
            cmd.append('-u')

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

    return _run_git_command(cmd, project_root)


def _git_cherry_pick(args: Dict, project_root: str) -> Dict[str, Any]:
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
            return {'success': False, 'output': '', 'error': 'Commits required', 'returncode': 1}

        if args.get('no_commit'):
            cmd.append('--no-commit')

        cmd.extend(commits)

    return _run_git_command(cmd, project_root)


def _git_log(args: Dict, project_root: str) -> Dict[str, Any]:
    """Show commit logs"""
    cmd = ['log']

    count = args.get('count', 10)
    cmd.append(f'-{count}')

    if args.get('oneline', True):
        cmd.append('--oneline')
    if args.get('graph'):
        cmd.append('--graph')
    if args.get('all'):
        cmd.append('--all')

    author = args.get('author')
    if author:
        cmd.extend(['--author', author])

    since = args.get('since')
    if since:
        cmd.extend(['--since', since])

    file_path = args.get('file')
    if file_path:
        cmd.extend(['--', file_path])

    return _run_git_command(cmd, project_root)


def _git_diff(args: Dict, project_root: str) -> Dict[str, Any]:
    """Show changes"""
    cmd = ['diff']

    if args.get('staged'):
        cmd.append('--cached')
    if args.get('stat'):
        cmd.append('--stat')
    if args.get('name_only'):
        cmd.append('--name-only')

    commit = args.get('commit')
    if commit:
        cmd.append(commit)

    files = args.get('files', [])
    if files:
        if isinstance(files, str):
            files = [files]
        cmd.append('--')
        cmd.extend(files)

    return _run_git_command(cmd, project_root)


def _git_show(args: Dict, project_root: str) -> Dict[str, Any]:
    """Show commit details"""
    cmd = ['show']

    commit = args.get('commit', 'HEAD')
    cmd.append(commit)

    if args.get('stat'):
        cmd.append('--stat')

    return _run_git_command(cmd, project_root)


def _git_mr(args: Dict, project_root: str) -> Dict[str, Any]:
    """Create merge request (custom operation)

    Args:
        args: {
            'title': str,           # MR title (-T), prefer Chinese
            'description': str,     # MR description (-D), prefer Chinese
            'dest_branch': str,     # Destination branch (--dest), extract from context if available
            'auto_confirm': bool    # Auto confirm flag (-y)
        }
    """
    cmd = ['mr']

    # Validate required parameters
    title = args.get('title')
    if not title:
        return {
            'success': False,
            'output': '',
            'error': 'Title is required for merge request (-T)',
            'returncode': 1
        }

    dest_branch = args.get('dest_branch')
    if not dest_branch:
        return {
            'success': False,
            'output': '',
            'error': 'Destination branch is required (--dest)',
            'returncode': 1
        }

    description = args.get('description')
    if not description:
        return {
            'success': False,
            'output': '',
            'error': 'Description is required (-D)',
            'returncode': 1
        }

    # Auto confirm flag
    if args.get('auto_confirm', False):
        cmd.append('-y')

    # Add destination branch
    cmd.extend(['--dest', dest_branch])

    # Add title
    cmd.extend(['-T', title])

    # Add description
    cmd.extend(['-D', description])

    # Execute with longer timeout for MR operations
    return _run_git_command(cmd, project_root, timeout=120)
