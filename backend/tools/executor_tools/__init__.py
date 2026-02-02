# -*- coding: utf-8 -*-
"""
Executor tools for running commands and building projects
"""

# Exceptions
# Tool classes
from .bash_run import BashRunTool, bash_run

# Session management
from .bash_session import BashSession, close_all_sessions, close_session, get_session
from .cmake_build_tool import CmakeBuildTool, cmake_build

# Compiler utilities
from .compiler_parser import format_error_summary, parse_compile_errors
from .exceptions import ExecutorError
from .run_tests_tool import RunTestsTool, run_tests

__all__ = [
    # Exceptions
    'ExecutorError',
    # Session management
    'BashSession',
    'get_session',
    'close_session',
    'close_all_sessions',
    # Compiler utilities
    'parse_compile_errors',
    'format_error_summary',
    # Tool classes
    'BashRunTool',
    'CmakeBuildTool',
    'RunTestsTool',
    # Backward compatible function APIs
    'bash_run',
    'cmake_build',
    'run_tests',
]
