# -*- coding: utf-8 -*-
"""
Path completer for directory navigation
"""

import glob
import os
from typing import Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class PathCompleter(Completer):
    """Completer for file paths"""

    def __init__(self, project_root: str = None):
        """
        Initialize path completer

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or os.getcwd()

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """Generate path completions"""
        text = document.text_before_cursor
        words = text.split()

        if not words:
            return

        # Check if we're completing a /root command
        if words[0] == '/root' and len(words) <= 2:
            partial_path = words[1] if len(words) == 2 else ''

            # Expand ~ to home directory
            if partial_path.startswith('~'):
                partial_path = os.path.expanduser(partial_path)

            # Get directory and prefix
            if os.path.isdir(partial_path):
                directory = partial_path
                prefix = ''
            else:
                directory = os.path.dirname(partial_path) or '.'
                prefix = os.path.basename(partial_path)

            # Find matching paths
            try:
                pattern = os.path.join(directory, prefix + '*')
                matches = glob.glob(pattern)

                for match in sorted(matches)[:50]:
                    if os.path.isdir(match):
                        display = os.path.basename(match) or match
                        completion_text = match + '/'
                        yield Completion(
                            completion_text,
                            start_position=-len(partial_path),
                            display=display + '/',
                            display_meta='Directory'
                        )
            except (OSError, PermissionError):
                pass
