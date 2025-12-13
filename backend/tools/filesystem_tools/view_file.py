# -*- coding: utf-8 -*-
"""
ViewFile Tool - Read file contents with optional line range
"""

import os
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


class ViewFileParams(BaseModel):
    """ViewFile tool parameters"""
    path: str = Field(
        description="File path (relative to project root or absolute path)",
        json_schema_extra={"format": "filepath"}
    )
    line_range: Optional[Tuple[int, int]] = Field(
        None,
        description="Optional line range [start_line, end_line] (1-indexed, use -1 for end of file)"
    )


class ViewFileTool(BaseTool):
    """Read file contents with optional line range"""

    @property
    def name(self) -> str:
        return "view_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Read file contents with line numbers. Useful to see current content and line numbers before editing.\n\n'
                'Examples:\n'
                '  path="src/main.py"  # View entire file\n'
                '  path="src/main.py", line_range=[100, 150]  # View lines 100-150 of large file'
            ),
            'zh': (
                '读取文件内容（包含行号）。在编辑前查看当前内容和行号很有用。\n\n'
                '示例：\n'
                '  path="src/main.py"  # 查看整个文件\n'
                '  path="src/main.py", line_range=[100, 150]  # 查看大文件的第 100-150 行'
            )
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
    def priority(self) -> int:
        return 95  # Highest priority - most frequently used, required before edit_file

    @property
    def parameters_model(self):
        return ViewFileParams

    def execute(self, path: str, line_range: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Read file contents with optional line range

        Args:
            path: File path (relative to project root or absolute)
            line_range: Optional [start_line, end_line] tuple (1-indexed, use -1 for EOF)

        Returns:
            Dict containing file content, path, total lines, and actual line range

        Raises:
            FileSystemError: If file not found, invalid range, or read fails
        """
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
            # Try to find similar file
            from backend.cli.path_utils import PathUtils
            path_utils = PathUtils(self.project_root or os.getcwd())
            original_path = path
            similar = path_utils.find_similar_file(path)
            if similar:
                # Use the similar file
                path = os.path.join(self.project_root or os.getcwd(), similar)
                path = os.path.abspath(path)
            else:
                raise FileSystemError(f"File not found: {original_path}")

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
