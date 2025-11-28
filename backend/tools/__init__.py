# -*- coding: utf-8 -*-
"""
Tools module for file operations, code execution, and analysis

Tool implementations are organized in subdirectories:
- filesystem_tools/  - File operations (view, edit, create, grep, list)
- executor_tools/    - Command execution (bash, cmake, ctest)
- git_tools/         - Git version control operations
- vscode_tools/      - VSCode integration
- agent_tools/       - Agent-specific tools (compact)
"""

from .filesystem_tools import (
    view_file,
    edit_file,
    create_file,
    grep_search,
    list_dir,
)

from .executor_tools import (
    bash_run,
    cmake_build,
    run_tests,
)

from .git_tools import git

from . import vscode_tools as vscode

__all__ = [
    # Filesystem
    'view_file',
    'edit_file',
    'create_file',
    'grep_search',
    'list_dir',
    # Executor
    'bash_run',
    'cmake_build',
    'run_tests',
    # Git
    'git',
    # VSCode
    'vscode',
]
