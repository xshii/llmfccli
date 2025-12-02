# -*- coding: utf-8 -*-
"""
GrepSearch Tool - Search for patterns in files using ripgrep
"""

import os
import re
import subprocess
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


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
            'en': (
                "Search for pattern in files using ripgrep. Returns structured JSON results "
                "(file path, line number, matched content). Preferred over bash_run for code search. "
                "Use bash_run instead ONLY when you need pipes (grep | head | wc) or complex shell combinations.\n\n"
                'GOOD: pattern="class.*Calculator", file_pattern="*.cpp"\n'
                'GOOD: pattern="void initialize\\(", scope="src/"\n'
                'BAD: Using bash_run with grep for simple pattern search'
            ),
            'zh': (
                "使用 ripgrep 搜索文件内容。返回结构化 JSON 结果（文件路径、行号、匹配内容）。"
                "优先使用此工具进行代码搜索。仅当需要管道（grep | head | wc）或复杂 shell 组合时才使用 bash_run。\n\n"
                '好例子：pattern="class.*Calculator", file_pattern="*.cpp"\n'
                '好例子：pattern="void initialize\\(", scope="src/"\n'
                '坏例子：简单搜索却使用 bash_run grep'
            )
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
        # Resolve scope path
        if not os.path.isabs(scope) and self.project_root:
            scope_path = os.path.join(self.project_root, scope)
        else:
            scope_path = scope

        scope_path = os.path.abspath(scope_path)

        # Security check
        if self.project_root:
            project_root = os.path.abspath(self.project_root)
            if not scope_path.startswith(project_root):
                raise FileSystemError(f"Scope {scope} is outside project root")

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
                timeout=30
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

            return {
                'success': True,
                'pattern': pattern,
                'scope': scope_path,
                'matches': matches[:50],  # Limit results
                'total': len(matches)
            }

        except subprocess.TimeoutExpired:
            raise FileSystemError("Search timeout (>30s)")
        except FileNotFoundError:
            raise FileSystemError("rg (ripgrep) not installed")
        except Exception as e:
            raise FileSystemError(f"Search failed: {e}")
