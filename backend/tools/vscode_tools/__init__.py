# -*- coding: utf-8 -*-
"""
VSCode integration tools
"""

from .vscode import (
    VSCodeError,
    get_active_file,
    get_selection,
    show_diff,
    apply_changes,
    open_file,
    get_workspace_folder
)

__all__ = [
    'VSCodeError',
    'get_active_file',
    'get_selection',
    'show_diff',
    'apply_changes',
    'open_file',
    'get_workspace_folder'
]
