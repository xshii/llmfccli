# -*- coding: utf-8 -*-
"""
GrepSearch Tool - 文件内容搜索
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
    """GrepSearch 工具参数"""
    pattern: str = Field(description="搜索模式（regex）")
    scope: str = Field(description="搜索范围目录（如 '.', 'src/', 'backend/'）")
    file_pattern: Optional[str] = Field(None, description="可选的文件模式过滤（如 '*.cpp'）")


class GrepSearchTool(BaseTool):
    """文件内容搜索工具"""

    @property
    def name(self) -> str:
        return "grep_search"

    @property
    def description(self) -> str:
        return "Search for pattern in files (regex supported)"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def parameters_model(self):
        return GrepSearchParams

    def execute(self, pattern: str, scope: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """执行文件搜索"""
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
