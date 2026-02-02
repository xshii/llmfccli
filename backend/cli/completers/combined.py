# -*- coding: utf-8 -*-
"""
Combined completer that merges multiple completers
"""

from typing import Iterable, List

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class CombinedCompleter(Completer):
    """Combines multiple completers"""

    def __init__(self, completers: List[Completer]):
        """
        Initialize combined completer

        Args:
            completers: List of completer instances
        """
        self.completers = completers

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """Generate completions from all completers"""
        for completer in self.completers:
            for completion in completer.get_completions(document, complete_event):
                yield completion
