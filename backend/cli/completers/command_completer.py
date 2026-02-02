# -*- coding: utf-8 -*-
"""
Slash command completer for CLI
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
            '/cache': 'Show file completion cache info',
            '/root': 'View or set project root directory',
            '/exit': 'Exit the program',
            '/quit': 'Exit the program',
            '/model': 'Manage Ollama models',
            '/cmd': 'Execute local terminal command (persistent session)',
            '/cmdpwd': 'Show current directory of persistent shell',
            '/cmdclear': 'Reset persistent shell session',
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
        """Generate completions based on current input"""
        text = document.text_before_cursor

        if not text:
            return

        # Complete slash commands
        if text.startswith('/'):
            words = text.split()
            has_trailing_space = text.endswith(' ')

            if len(words) == 0:
                word = '/'
                for cmd, desc in self.commands.items():
                    if cmd.startswith(word):
                        yield Completion(
                            cmd,
                            start_position=-len(word),
                            display=cmd,
                            display_meta=desc
                        )
            elif len(words) == 1 and not has_trailing_space:
                word = words[0]
                for cmd, desc in self.commands.items():
                    if cmd.startswith(word):
                        yield Completion(
                            cmd,
                            start_position=-len(word),
                            display=cmd,
                            display_meta=desc
                        )
            else:
                main_cmd = words[0].lower()

                # /model subcommands
                if main_cmd == '/model':
                    partial = words[1] if len(words) >= 2 else ''
                    for subcmd, desc in self.model_subcommands.items():
                        if subcmd.startswith(partial):
                            yield Completion(
                                subcmd,
                                start_position=-len(partial),
                                display=subcmd,
                                display_meta=desc
                            )

                # /cmd and /cmdremote shell command suggestions
                elif main_cmd in ['/cmd', '/cmdremote']:
                    partial = words[1] if len(words) >= 2 else ''
                    for shell_cmd in self.shell_commands:
                        if shell_cmd.startswith(partial):
                            yield Completion(
                                shell_cmd,
                                start_position=-len(partial),
                                display=shell_cmd,
                                display_meta='Shell command'
                            )
