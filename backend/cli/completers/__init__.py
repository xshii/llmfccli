# -*- coding: utf-8 -*-
"""
CLI Completers

Tab completion support for Claude-Qwen CLI:
- ClaudeQwenCompleter: Slash commands (/help, /model, etc.)
- PathCompleter: Directory path completion
- FileNameCompleter: File name completion with adaptive caching
- CombinedCompleter: Merges multiple completers
"""

from .command_completer import ClaudeQwenCompleter
from .path_completer import PathCompleter
from .file_completer import FileNameCompleter
from .combined import CombinedCompleter

__all__ = [
    'ClaudeQwenCompleter',
    'PathCompleter',
    'FileNameCompleter',
    'CombinedCompleter',
]
