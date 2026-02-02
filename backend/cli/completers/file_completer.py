# -*- coding: utf-8 -*-
"""
File name completer with adaptive caching
"""

import os
import time
from pathlib import Path
from typing import Iterable, List

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class FileNameCompleter(Completer):
    """Completer for file names in project directory"""

    # File extensions to prioritize
    PRIORITY_EXTENSIONS = {
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
    SKIP_DIRS = {
        '.git', '.svn', '.hg',  # VCS
        '__pycache__', '.pytest_cache', '.mypy_cache',  # Python cache
        'node_modules', '.venv', 'venv', 'env',  # Dependencies
        'build', 'dist', '.eggs', '*.egg-info',  # Build artifacts
        '.vscode', '.idea',  # IDE
    }

    def __init__(self, project_root: str = None, cache_duration: int = None):
        """
        Initialize file name completer

        Args:
            project_root: Project root directory
            cache_duration: Cache duration in seconds (None for adaptive)
        """
        self.project_root = project_root or os.getcwd()
        self.base_cache_duration = cache_duration
        self.cache_duration = cache_duration or 60
        self._file_cache: List[str] = []
        self._cache_time: float = 0
        self._last_scan_duration: float = 0
        self._adaptive_cache = cache_duration is None

    def _should_skip_dir(self, dir_name: str) -> bool:
        """Check if directory should be skipped"""
        return dir_name in self.SKIP_DIRS or dir_name.startswith('.')

    def _calculate_adaptive_cache_duration(self, file_count: int, scan_duration: float) -> int:
        """Calculate adaptive cache duration based on project size and scan time"""
        if file_count < 100:
            base_duration = 30
        elif file_count < 1000:
            base_duration = 60
        elif file_count < 5000:
            base_duration = 120
        else:
            base_duration = 300

        if scan_duration > 0.5:
            base_duration *= 2
        elif scan_duration > 0.1:
            base_duration = int(base_duration * 1.5)

        return min(max(base_duration, 30), 600)

    def _scan_files(self) -> List[str]:
        """Scan project directory for files"""
        files = []
        try:
            root_path = Path(self.project_root)

            for root, dirs, filenames in os.walk(root_path):
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

                for filename in filenames:
                    if filename.startswith('.'):
                        continue

                    file_path = Path(root) / filename
                    try:
                        rel_path = file_path.relative_to(root_path)
                        files.append(str(rel_path))
                    except ValueError:
                        continue

                current_depth = len(Path(root).relative_to(root_path).parts)
                if current_depth >= 5:
                    dirs.clear()

        except (OSError, PermissionError):
            pass

        return files

    def _get_files(self) -> List[str]:
        """Get file list (with caching)"""
        current_time = time.time()

        if self._file_cache and (current_time - self._cache_time) < self.cache_duration:
            return self._file_cache

        scan_start = time.time()
        self._file_cache = self._scan_files()
        scan_duration = time.time() - scan_start
        self._last_scan_duration = scan_duration
        self._cache_time = current_time

        if self._adaptive_cache:
            file_count = len(self._file_cache)
            self.cache_duration = self._calculate_adaptive_cache_duration(
                file_count, scan_duration
            )

        return self._file_cache

    def get_cache_info(self) -> dict:
        """Get cache information for debugging/display"""
        return {
            'file_count': len(self._file_cache),
            'cache_duration': self.cache_duration,
            'last_scan_duration_ms': self._last_scan_duration * 1000,
            'adaptive_mode': self._adaptive_cache,
            'cache_age_seconds': time.time() - self._cache_time if self._cache_time > 0 else 0,
        }

    def _match_score(self, file_path: str, query: str) -> int:
        """Calculate match score for file path"""
        file_lower = file_path.lower()
        query_lower = query.lower()

        if file_lower == query_lower:
            return 1000

        if file_lower.startswith(query_lower):
            return 900

        filename = os.path.basename(file_path).lower()
        if filename.startswith(query_lower):
            return 800

        if query_lower in file_lower:
            score = 500

            ext = os.path.splitext(file_path)[1]
            if ext in self.PRIORITY_EXTENSIONS:
                score += 100

            score += max(0, 50 - len(file_path))

            return score

        return -1

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """Generate file name completions"""
        text = document.text_before_cursor

        if text.startswith('/'):
            return

        words = text.split()
        if not words:
            return

        query = words[-1]

        if len(query) < 2:
            return

        files = self._get_files()

        scored_files = []
        for file_path in files:
            score = self._match_score(file_path, query)
            if score >= 0:
                scored_files.append((score, file_path))

        scored_files.sort(reverse=True, key=lambda x: x[0])
        top_files = scored_files[:30]

        for score, file_path in top_files:
            ext = os.path.splitext(file_path)[1]
            if ext in self.PRIORITY_EXTENSIONS:
                meta = f"File ({ext})"
            else:
                meta = "File"

            yield Completion(
                file_path,
                start_position=-len(query),
                display=file_path,
                display_meta=meta
            )
