# -*- coding: utf-8 -*-
"""
VSCode integration tools
"""

from .vscode import (
    VSCodeError,
    apply_changes,
    get_active_file,
    get_selection,
    get_workspace_folder,
    open_file,
    show_diff,
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
