# -*- coding: utf-8 -*-
"""
Tab completion support for Claude-Qwen CLI
"""

import os
import time
from pathlib import Path
from typing import Iterable, List, Set
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
            '/cache': 'Show file completion cache info',
            '/root': 'View or set project root directory',
            '/reset-confirmations': 'Reset all tool execution confirmations',
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
        """
        Generate completions based on current input

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor

        # If empty or not starting with /, no completions
        if not text:
            return

        # Complete slash commands
        if text.startswith('/'):
            # Split while preserving information about trailing spaces
            words = text.split()
            has_trailing_space = text.endswith(' ')

            # Determine if we're completing main command or subcommand
            if len(words) == 0:
                word = '/'
                # Complete main command
                for cmd, desc in self.commands.items():
                    if cmd.startswith(word):
                        yield Completion(
                            cmd,
                            start_position=-len(word),
                            display=cmd,
                            display_meta=desc
                        )
            elif len(words) == 1 and not has_trailing_space:
                # Still completing the main command
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
                # Complete subcommands (either we have 2+ words, or 1 word + trailing space)
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


class FileNameCompleter(Completer):
    """Completer for file names in project directory"""

    def __init__(self, project_root: str = None, cache_duration: int = None):
        """
        Initialize file name completer

        Args:
            project_root: Project root directory
            cache_duration: Cache duration in seconds (None for adaptive)
        """
        self.project_root = project_root or os.getcwd()
        self.base_cache_duration = cache_duration  # User-specified or None for adaptive
        self.cache_duration = cache_duration or 60  # Initial default
        self._file_cache: List[str] = []
        self._cache_time: float = 0
        self._last_scan_duration: float = 0  # Track scan performance
        self._adaptive_cache = cache_duration is None  # Enable adaptive caching

        # File extensions to prioritize
        self.priority_extensions = {
            '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx',  # C/C++
            '.py', '.pyx', '.pyi',  # Python
            '.js', '.ts', '.jsx', '.tsx',  # JavaScript/TypeScript
            '.java', '.kt',  # JVM languages
            '.go', '.rs',  # Go, Rust
            '.yaml', '.yml', '.json', '.toml', '.ini',  # Config
            '.md', '.rst', '.txt',  # Documentation
            '.sh', '.bash', '.zsh',  # Shell scripts
        }

        # Directories to skip
        self.skip_dirs = {
            '.git', '.svn', '.hg',  # VCS
            '__pycache__', '.pytest_cache', '.mypy_cache',  # Python cache
            'node_modules', '.venv', 'venv', 'env',  # Dependencies
            'build', 'dist', '.eggs', '*.egg-info',  # Build artifacts
            '.vscode', '.idea',  # IDE
        }

    def _should_skip_dir(self, dir_name: str) -> bool:
        """Check if directory should be skipped"""
        return dir_name in self.skip_dirs or dir_name.startswith('.')

    def _calculate_adaptive_cache_duration(self, file_count: int, scan_duration: float) -> int:
        """
        Calculate adaptive cache duration based on project size and scan time

        Args:
            file_count: Number of files scanned
            scan_duration: Time taken to scan (in seconds)

        Returns:
            Optimal cache duration in seconds
        """
        # Base duration by file count
        if file_count < 100:
            # Small project: 30 seconds
            base_duration = 30
        elif file_count < 1000:
            # Medium project: 60 seconds
            base_duration = 60
        elif file_count < 5000:
            # Large project: 120 seconds (2 minutes)
            base_duration = 120
        else:
            # Very large project: 300 seconds (5 minutes)
            base_duration = 300

        # Adjust based on scan performance
        # If scan takes longer, increase cache time
        if scan_duration > 0.5:
            # Very slow scan (>500ms): double the cache time
            base_duration *= 2
        elif scan_duration > 0.1:
            # Slow scan (>100ms): increase by 50%
            base_duration = int(base_duration * 1.5)

        # Cap at reasonable limits
        return min(max(base_duration, 30), 600)  # Between 30s and 10min

    def _scan_files(self) -> List[str]:
        """
        Scan project directory for files

        Returns:
            List of relative file paths
        """
        files = []
        try:
            root_path = Path(self.project_root)

            # Walk directory tree
            for root, dirs, filenames in os.walk(root_path):
                # Filter out skip directories
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

                # Add files
                for filename in filenames:
                    # Skip hidden files
                    if filename.startswith('.'):
                        continue

                    # Get relative path
                    file_path = Path(root) / filename
                    try:
                        rel_path = file_path.relative_to(root_path)
                        files.append(str(rel_path))
                    except ValueError:
                        continue

                # Limit scanning depth to avoid very deep trees
                current_depth = len(Path(root).relative_to(root_path).parts)
                if current_depth >= 5:
                    dirs.clear()

        except (OSError, PermissionError):
            pass

        return files

    def _get_files(self) -> List[str]:
        """
        Get file list (with caching)

        Returns:
            List of relative file paths
        """
        current_time = time.time()

        # Check if cache is valid
        if self._file_cache and (current_time - self._cache_time) < self.cache_duration:
            return self._file_cache

        # Rebuild cache and measure scan time
        scan_start = time.time()
        self._file_cache = self._scan_files()
        scan_duration = time.time() - scan_start
        self._last_scan_duration = scan_duration
        self._cache_time = current_time

        # Update cache duration if adaptive mode is enabled
        if self._adaptive_cache:
            file_count = len(self._file_cache)
            self.cache_duration = self._calculate_adaptive_cache_duration(
                file_count, scan_duration
            )

        return self._file_cache

    def get_cache_info(self) -> dict:
        """
        Get cache information for debugging/display

        Returns:
            Dictionary with cache stats
        """
        return {
            'file_count': len(self._file_cache),
            'cache_duration': self.cache_duration,
            'last_scan_duration_ms': self._last_scan_duration * 1000,
            'adaptive_mode': self._adaptive_cache,
            'cache_age_seconds': time.time() - self._cache_time if self._cache_time > 0 else 0,
        }

    def _match_score(self, file_path: str, query: str) -> int:
        """
        Calculate match score for file path

        Args:
            file_path: File path to match
            query: Query string

        Returns:
            Match score (higher is better, -1 for no match)
        """
        file_lower = file_path.lower()
        query_lower = query.lower()

        # Exact match (highest priority)
        if file_lower == query_lower:
            return 1000

        # Starts with query
        if file_lower.startswith(query_lower):
            return 900

        # Filename starts with query
        filename = os.path.basename(file_path).lower()
        if filename.startswith(query_lower):
            return 800

        # Contains query
        if query_lower in file_lower:
            score = 500

            # Bonus for priority extensions
            ext = os.path.splitext(file_path)[1]
            if ext in self.priority_extensions:
                score += 100

            # Bonus for shorter paths
            score += max(0, 50 - len(file_path))

            return score

        # No match
        return -1

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Generate file name completions

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects for file names
        """
        text = document.text_before_cursor

        # Skip if starts with / (slash commands)
        if text.startswith('/'):
            return

        # Get the last word (potential file path)
        words = text.split()
        if not words:
            return

        # Get query (last word or partial path)
        query = words[-1]

        # Skip very short queries to avoid too many results
        if len(query) < 2:
            return

        # Get file list
        files = self._get_files()

        # Score and filter files
        scored_files = []
        for file_path in files:
            score = self._match_score(file_path, query)
            if score >= 0:
                scored_files.append((score, file_path))

        # Sort by score (descending) and take top 30
        scored_files.sort(reverse=True, key=lambda x: x[0])
        top_files = scored_files[:30]

        # Generate completions
        for score, file_path in top_files:
            # Determine display metadata
            ext = os.path.splitext(file_path)[1]
            if ext in self.priority_extensions:
                meta = f"File ({ext})"
            else:
                meta = "File"

            yield Completion(
                file_path,
                start_position=-len(query),
                display=file_path,
                display_meta=meta
            )


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
