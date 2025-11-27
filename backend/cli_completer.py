# -*- coding: utf-8 -*-
"""
Tab completion support for Claude-Qwen CLI
"""

from typing import Iterable
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class ClaudeQwenCompleter(Completer):
    """Custom completer for Claude-Qwen CLI commands"""

    def __init__(self):
        """Initialize completer with command definitions"""
        # Define all slash commands
        self.commands = {
            '/help': 'Display help message',
            '/clear': 'Clear conversation history',
            '/compact': 'Manually trigger context compression',
            '/usage': 'Show token usage',
            '/root': 'View or set project root directory',
            '/reset-confirmations': 'Reset all tool execution confirmations',
            '/exit': 'Exit the program',
            '/quit': 'Exit the program',
            '/model': 'Manage Ollama models',
            '/cmd': 'Execute local terminal command',
            '/cmdremote': 'Execute remote terminal command (SSH)',
            '/expand': 'Expand last collapsed tool output',
            '/collapse': 'Collapse last expanded tool output',
            '/toggle': 'Toggle last tool output state',
            '/vscode': 'Open current project in VSCode',
            '/testvs': 'Test VSCode extension integration',
        }

        # Define /model subcommands
        self.model_subcommands = {
            'list': 'List all Ollama models',
            'create': 'Create claude-qwen model',
            'show': 'Show model details',
            'delete': 'Delete a model',
            'pull': 'Pull a model from registry',
            'health': 'Check Ollama server health',
        }

        # Common shell commands for /cmd and /cmdremote
        self.shell_commands = [
            'ls', 'cd', 'pwd', 'cat', 'grep', 'find', 'ps', 'top',
            'df', 'du', 'git', 'docker', 'systemctl', 'nvidia-smi',
            'ollama', 'python', 'python3', 'pip', 'pip3', 'npm',
            'tree', 'htop', 'netstat', 'ping', 'curl', 'wget',
            'tail', 'head', 'less', 'vim', 'nano', 'echo', 'chmod',
            'chown', 'mkdir', 'rm', 'cp', 'mv', 'touch', 'which',
        ]

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Generate completions based on current input

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor
        words = text.split()

        # If empty or not starting with /, no completions
        if not text:
            return

        # Complete slash commands
        if text.startswith('/'):
            if len(words) <= 1:
                # Complete main command
                word = words[0] if words else '/'
                for cmd, desc in self.commands.items():
                    if cmd.startswith(word):
                        yield Completion(
                            cmd,
                            start_position=-len(word),
                            display=cmd,
                            display_meta=desc
                        )
            else:
                # Complete subcommands
                main_cmd = words[0].lower()

                # /model subcommands
                if main_cmd == '/model' and len(words) <= 2:
                    partial = words[1] if len(words) == 2 else ''
                    for subcmd, desc in self.model_subcommands.items():
                        if subcmd.startswith(partial):
                            yield Completion(
                                subcmd,
                                start_position=-len(partial),
                                display=subcmd,
                                display_meta=desc
                            )

                # /cmd and /cmdremote shell command suggestions
                elif main_cmd in ['/cmd', '/cmdremote'] and len(words) <= 2:
                    partial = words[1] if len(words) == 2 else ''
                    for shell_cmd in self.shell_commands:
                        if shell_cmd.startswith(partial):
                            yield Completion(
                                shell_cmd,
                                start_position=-len(partial),
                                display=shell_cmd,
                                display_meta='Shell command'
                            )


class PathCompleter(Completer):
    """Completer for file paths"""

    def __init__(self, project_root: str = None):
        """
        Initialize path completer

        Args:
            project_root: Project root directory
        """
        import os
        self.project_root = project_root or os.getcwd()

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Generate path completions

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects for file paths
        """
        import os
        import glob

        text = document.text_before_cursor
        words = text.split()

        # Only complete for /root command or when there's a path-like input
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

                for match in sorted(matches)[:50]:  # Limit to 50 results
                    # Show only directories for /root
                    if os.path.isdir(match):
                        display = os.path.basename(match) or match
                        # Add trailing slash for directories
                        completion_text = match + '/'
                        yield Completion(
                            completion_text,
                            start_position=-len(partial_path),
                            display=display + '/',
                            display_meta='Directory'
                        )
            except (OSError, PermissionError):
                # Ignore errors accessing directories
                pass


class CombinedCompleter(Completer):
    """Combines multiple completers"""

    def __init__(self, completers: list):
        """
        Initialize combined completer

        Args:
            completers: List of completer instances
        """
        self.completers = completers

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Generate completions from all completers

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects from all completers
        """
        for completer in self.completers:
            for completion in completer.get_completions(document, complete_event):
                yield completion
