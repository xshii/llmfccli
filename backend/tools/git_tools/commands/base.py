# -*- coding: utf-8 -*-
"""
Git commands base utilities
"""

import os
import subprocess
from typing import Dict, List

from backend.tools.base import ToolResult


class GitError(Exception):
    """Base exception for git operations"""
    pass


def parse_flags(flags: str) -> List[str]:
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


def run_git_command(cmd: List[str], cwd: str, timeout: int = 30, env: dict = None,
                    stdin_devnull: bool = False) -> ToolResult:
    """
    Execute git command

    Args:
        cmd: Git command arguments (without 'git' prefix)
        cwd: Working directory
        timeout: Command timeout in seconds
        env: Optional environment variables
        stdin_devnull: If True, redirect stdin to /dev/null to prevent waiting for input

    Returns:
        ToolResult with execution results
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

        if result.returncode == 0:
            return ToolResult.success(result.stdout)
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return ToolResult.fail(error_msg)

    except subprocess.TimeoutExpired:
        return ToolResult.fail(f'Command timed out after {timeout} seconds')
    except Exception as e:
        return ToolResult.fail(str(e))
