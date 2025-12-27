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


def _parse_flags(flags: str) -> List[str]:
    """Parse flags string into list of arguments.

    Supports formats like:
    - "oneline graph" -> ["--oneline", "--graph"]
    - "--oneline --graph" -> ["--oneline", "--graph"]
    - "-fd" -> ["-fd"]
    - "-f -d" -> ["-f", "-d"]
    """
    if not flags:
        return []

    result = []
    for flag in flags.split():
        flag = flag.strip()
        if not flag:
            continue
        # Already has dash prefix
        if flag.startswith('-'):
            result.append(flag)
        # Add -- prefix for long flags (more than 1 char)
        elif len(flag) > 1 and not flag[0].isdigit():
            result.append(f'--{flag}')
        # Single char gets single dash
        else:
            result.append(f'-{flag}')
    return result


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
        'clean': _git_clean,
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


def _run_git_command(cmd: List[str], cwd: str, timeout: int = 30, env: dict = None,
                     stdin_devnull: bool = False) -> Dict[str, Any]:
    """
    Execute git command

    Args:
        cmd: Git command arguments (without 'git' prefix)
        cwd: Working directory
        timeout: Command timeout in seconds
        env: Optional environment variables
        stdin_devnull: If True, redirect stdin to /dev/null to prevent waiting for input

    Returns:
        Dict with execution results
    """
    try:
        result = subprocess.run(
            ['git'] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            stdin=subprocess.DEVNULL if stdin_devnull else None,
            env=env
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
    cmd.extend(_parse_flags(args.get('flags', '')))
    return _run_git_command(cmd, project_root)


def _git_add(args: Dict, project_root: str) -> Dict[str, Any]:
    """Add files to staging area"""
    cmd = ['add']

    # DEBUG: Log incoming args
    if os.getenv('DEBUG_GIT'):
        print(f"[DEBUG git add] args: {args}")
        print(f"[DEBUG git add] files type: {type(args.get('files'))}")
        print(f"[DEBUG git add] files value: {args.get('files')}")

    if args.get('all'):
        cmd.append('-A')
    else:
        files = args.get('files', [])
        if isinstance(files, str):
            files = [files]
        if not files:
            return {
                'success': False,
                'output': '',
                'error': 'No files specified (use files or all)',
                'returncode': 1
            }
        cmd.extend(files)

    cmd.extend(_parse_flags(args.get('flags', '')))

    # DEBUG: Log final command
    if os.getenv('DEBUG_GIT'):
        print(f"[DEBUG git add] final cmd: {cmd}")

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
    if args.get('no_edit'):
        cmd.append('--no-edit')

    cmd.extend(_parse_flags(args.get('flags', '')))
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

    commit = args.get('commit', 'HEAD')

    files = args.get('files', [])
    if files:
        # Reset specific files (unstage)
        cmd = ['reset', commit, '--']
        if isinstance(files, str):
            files = [files]
        cmd.extend(files)
    else:
        cmd.append(commit)

    cmd.extend(_parse_flags(args.get('flags', '')))
    return _run_git_command(cmd, project_root)


def _git_branch(args: Dict, project_root: str) -> Dict[str, Any]:
    """Branch operations"""
    operation = args.get('operation', 'list')
    cmd = ['branch']

    if operation == 'list':
        if args.get('all'):
            cmd.append('--all')

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

    cmd.extend(_parse_flags(args.get('flags', '')))
    return _run_git_command(cmd, project_root)


def _git_checkout(args: Dict, project_root: str) -> Dict[str, Any]:
    """Checkout branch or restore files"""
    branch = args.get('branch')
    files = args.get('files', [])

    if not branch and not files:
        return {'success': False, 'output': '', 'error': 'branch or files required', 'returncode': 1}

    cmd = ['checkout']

    if branch:
        # Checkout branch
        if args.get('create'):
            cmd.append('-b')
        if args.get('force'):
            cmd.append('-f')
        cmd.append(branch)
    else:
        # Restore files
        if isinstance(files, str):
            files = [files]
        cmd.append('--')
        cmd.extend(files)

    cmd.extend(_parse_flags(args.get('flags', '')))
    return _run_git_command(cmd, project_root)


def _git_push(args: Dict, project_root: str) -> Dict[str, Any]:
    """Push to remote"""
    cmd = ['push']

    if args.get('force'):
        cmd.append('--force')

    cmd.extend(_parse_flags(args.get('flags', '')))

    remote = args.get('remote', 'origin')
    branch = args.get('branch', '')

    cmd.append(remote)
    if branch:
        cmd.append(branch)

    return _run_git_command(cmd, project_root, timeout=60)


def _git_pull(args: Dict, project_root: str) -> Dict[str, Any]:
    """Pull from remote"""
    cmd = ['pull']

    if args.get('rebase'):
        cmd.append('--rebase')

    cmd.extend(_parse_flags(args.get('flags', '')))

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

    cmd.extend(_parse_flags(args.get('flags', '')))

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

        cmd.extend(_parse_flags(args.get('flags', '')))
        cmd.append(branch)

    return _run_git_command(cmd, project_root, timeout=120)


def _git_stash(args: Dict, project_root: str) -> Dict[str, Any]:
    """Stash operations"""
    operation = args.get('operation', 'push')
    cmd = ['stash']

    if operation == 'push':
        cmd.append('push')
        message = args.get('message')
        if message:
            cmd.extend(['-m', message])
        cmd.extend(_parse_flags(args.get('flags', '')))

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

        cmd.extend(_parse_flags(args.get('flags', '')))
        cmd.extend(commits)

    return _run_git_command(cmd, project_root)


def _git_log(args: Dict, project_root: str) -> Dict[str, Any]:
    """Show commit logs"""
    cmd = ['log']

    # Number of commits (required)
    n = args.get('n')
    if not n:
        return {'success': False, 'output': '', 'error': 'n (number of commits) is required', 'returncode': 1}
    cmd.append(f'-{n}')

    # Default to --oneline if no format specified in flags
    flags = args.get('flags', '')
    if not flags or ('oneline' not in flags and 'format' not in flags):
        cmd.append('--oneline')

    cmd.extend(_parse_flags(flags))
    return _run_git_command(cmd, project_root)


def _git_diff(args: Dict, project_root: str) -> Dict[str, Any]:
    """Show changes"""
    cmd = ['diff']

    cmd.extend(_parse_flags(args.get('flags', '')))

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

    cmd.extend(_parse_flags(args.get('flags', '')))
    return _run_git_command(cmd, project_root)


def _git_mr(args: Dict, project_root: str) -> Dict[str, Any]:
    """Create merge request (custom operation)

    Args:
        args: {
            'title': str,           # MR title (-T), prefer Chinese
            'description': str,     # MR description (-D), prefer Chinese
            'dest_branch': str,     # Destination branch (--dest), extract from context if available
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

    # Default flags: -y (auto confirm) -f (force)
    cmd.extend(['-y', '-f'])

    # Add destination branch
    cmd.extend(['--dest', dest_branch])

    # Add title
    cmd.extend(['-T', title])

    # Add description
    cmd.extend(['-D', description])

    # Setup environment to disable interactive prompts
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'  # Disable git credential prompts
    env['GIT_ASKPASS'] = 'echo'       # Disable password prompts

    # Execute with environment variables, timeout, and stdin redirected to prevent hanging
    return _run_git_command(cmd, project_root, timeout=30, env=env, stdin_devnull=True)


def _git_clean(args: Dict, project_root: str) -> Dict[str, Any]:
    """Clean untracked files"""
    cmd = ['clean']

    # Default flags: -fdx (force, directories, ignored files)
    flags = args.get('flags', '-fdx')

    # Ensure -f is always present (git requires it)
    parsed_flags = _parse_flags(flags)
    has_force = any(f in ['-f', '--force'] or 'f' in f for f in parsed_flags)
    if not has_force:
        cmd.append('-f')

    cmd.extend(parsed_flags)
    return _run_git_command(cmd, project_root)
