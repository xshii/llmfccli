# -*- coding: utf-8 -*-
"""
ViewFile Tool - 读取文件内容
"""

import os
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


class ViewFileParams(BaseModel):
    """ViewFile 工具参数"""
    path: str = Field(
        description="File path (relative to project root or absolute path)",
        json_schema_extra={"format": "filepath"}
    )
    line_range: Optional[Tuple[int, int]] = Field(
        None,
        description="Optional line range [start_line, end_line] (1-indexed, use -1 for end of file)"
    )


class ViewFileTool(BaseTool):
    """读取文件内容工具"""

    @property
    def name(self) -> str:
        return "view_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': 'Read file contents with optional line range',
            'zh': '读取文件内容（可指定行范围）'
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'line_range': {
                'en': 'Optional line range [start_line, end_line] (1-indexed, use -1 for end of file)',
                'zh': '可选的行范围 [start_line, end_line]（1-indexed，使用 -1 表示文件末尾）',
            },
        }
    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def parameters_model(self):
        return ViewFileParams

    def execute(self, path: str, line_range: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """执行文件读取"""
        # Resolve path
        if not os.path.isabs(path) and self.project_root:
            path = os.path.join(self.project_root, path)

        path = os.path.abspath(path)

        # Security check - prevent path traversal
        if self.project_root:
            project_root = os.path.abspath(self.project_root)
            if not path.startswith(project_root):
                raise FileSystemError(f"Path {path} is outside project root {project_root}")

        # Check file exists
        if not os.path.exists(path):
            raise FileSystemError(f"File not found: {path}")

        if not os.path.isfile(path):
            raise FileSystemError(f"Not a file: {path}")

        # Read file
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {path}: {e}")

        total_lines = len(lines)

        # Apply line range
        if line_range:
            start, end = line_range
            # Handle negative indices
            if end == -1:
                end = total_lines

            # Validate range
            if start < 1 or start > total_lines:
                raise FileSystemError(f"Invalid start line {start} (file has {total_lines} lines)")

            if end < start or end > total_lines:
                raise FileSystemError(f"Invalid end line {end}")

            # Extract lines (convert to 0-indexed)
            selected_lines = lines[start-1:end]
            content = ''.join(selected_lines)
            actual_range = (start, end)
        else:
            content = ''.join(lines)
            actual_range = (1, total_lines)

        return {
            'content': content,
            'path': path,
            'total_lines': total_lines,
            'line_range': actual_range,
        }
