# -*- coding: utf-8 -*-
"""
GrepSearch Tool - Search for patterns in files using ripgrep
"""

import os
import subprocess
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from backend.constants import Limit, ToolDefaults
from backend.tools.base import BaseTool, FileSystemError, ToolResult


class GrepSearchParams(BaseModel):
    """GrepSearch tool parameters"""
    pattern: str = Field(
        description="Search pattern (regex)"
    )
    scope: str = Field(
        description="Search scope directory (e.g., '.', 'src/', 'backend/')"
    )
    file_pattern: Optional[str] = Field(
        None,
        description="Optional file pattern filter (e.g., '*.cpp', '*.h')"
    )


class GrepSearchTool(BaseTool):
    """Search for patterns in files using ripgrep"""

    @property
    def name(self) -> str:
        return "grep_search"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': 'Search for pattern (regex) in files.',
            'zh': '在文件中搜索模式（正则表达式）。'
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'pattern': {
                'en': 'Search pattern (regex)',
                'zh': '搜索模式（regex）',
            },
            'scope': {
                'en': 'Search scope directory (e.g., \'.\', \'src/\', \'backend/\')',
                'zh': '搜索范围目录（如 \'.\', \'src/\', \'backend/\'）',
            },
            'file_pattern': {
                'en': 'Optional file pattern filter (e.g., \'*.cpp\')',
                'zh': '可选的文件模式过滤（如 \'*.cpp\'）',
            },
        }
    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def priority(self) -> int:
        return 85

    @property
    def parameters_model(self):
        return GrepSearchParams

    def execute(self, pattern: str, scope: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for pattern in files using ripgrep

        Args:
            pattern: Search pattern (regex supported)
            scope: Search scope directory (e.g., '.', 'src/', 'backend/')
            file_pattern: Optional file pattern filter (e.g., '*.cpp', '*.h')

        Returns:
            Dict containing search results with file paths, line numbers, and matched content

        Raises:
            FileSystemError: If scope is outside project root or search fails
        """
        # Resolve scope path and validate security
        try:
            scope_path = self.resolve_and_validate_path(scope)
        except ValueError as e:
            raise FileSystemError(str(e))

        # Check scope exists
        if not os.path.exists(scope_path):
            raise FileSystemError(f"Scope not found: {scope}")

        # Build rg command
        cmd = ['rg', '--json', pattern, scope_path]
        if file_pattern:
            cmd.extend(['--glob', file_pattern])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=ToolDefaults.GREP_TIMEOUT
            )

            matches = []
            for line in result.stdout.splitlines():
                if line.strip():
                    import json
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'match':
                            matches.append({
                                'file': data['data']['path']['text'],
                                'line': data['data']['line_number'],
                                'content': data['data']['lines']['text'].strip()
                            })
                    except json.JSONDecodeError:
                        pass

            # Format results as text
            if not matches:
                return ToolResult.success(f"No matches found for '{pattern}'")

            max_results = Limit.SEARCH_RESULTS_MAX
            lines = [f"{m['file']}:{m['line']}: {m['content']}" for m in matches[:max_results]]
            if len(matches) > max_results:
                lines.append(f"... ({len(matches) - max_results} more matches)")

            return ToolResult.success('\n'.join(lines))

        except subprocess.TimeoutExpired:
            raise FileSystemError(f"Search timeout (>{ToolDefaults.GREP_TIMEOUT}s)")
        except FileNotFoundError:
            raise FileSystemError("rg (ripgrep) not installed")
        except Exception as e:
            raise FileSystemError(f"Search failed: {e}")
