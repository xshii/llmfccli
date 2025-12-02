# -*- coding: utf-8 -*-
"""
EditFile Tool - Line-based file editing with Unix line endings
"""

import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field, validator

from backend.tools.base import BaseTool


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


class EditFileParams(BaseModel):
    """EditFile tool parameters"""
    path: str = Field(
        description="File path (relative to project root or absolute path)",
        json_schema_extra={"format": "filepath"}
    )
    line_range: List[int] = Field(
        description="Line range as [start_line, end_line] (1-based, inclusive). Example: [10, 15] edits lines 10 through 15",
        min_items=2,
        max_items=2
    )
    new_content: str = Field(
        description="New content to replace the specified line range (use \\n for line breaks)"
    )
    confirm: bool = Field(
        True,
        description="Whether to confirm before editing (default true)"
    )

    @validator('line_range')
    def validate_line_range(cls, v):
        if len(v) != 2:
            raise ValueError("line_range must contain exactly 2 elements: [start_line, end_line]")
        start_line, end_line = v
        if start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {start_line}")
        if end_line < start_line:
            raise ValueError(f"end_line ({end_line}) must be >= start_line ({start_line})")
        return v


class EditFileTool(BaseTool):
    """Edit file by replacing a line range with new content"""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Replaces a range of lines in a file with new content. You must use view_file at least once before editing. '
                'Specify line_range as [start_line, end_line] (1-based, inclusive) to define the range. '
                'Use Unix line endings (\\n) in new_content. Lines are preserved with \\n separator.\n\n'
                'GOOD: line_range=[10, 15] edits lines 10-15 with accurate line numbers from view_file\n'
                'GOOD: new_content="def foo():\\n    return 42" (explicit \\n)\n'
                'BAD: Using wrong line numbers without checking view_file first'
            ),
            'zh': (
                '替换文件中的行范围为新内容。必须先使用 view_file 读取文件。'
                '指定 line_range 为 [start_line, end_line]（从1开始，包含边界）定义范围。'
                '在 new_content 中使用 Unix 行结束符（\\n）。行之间用 \\n 分隔。\n\n'
                '好例子：line_range=[10, 15] 使用 view_file 中准确的行号编辑 10-15 行\n'
                '好例子：new_content="def foo():\\n    return 42"（显式 \\n）\n'
                '坏例子：不先查看 view_file 就使用错误的行号'
            )
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'line_range': {
                'en': 'Line range as [start_line, end_line] (1-based, inclusive). Example: [10, 15]',
                'zh': '行范围 [起始行, 结束行]（从1开始，包含边界）。示例：[10, 15]',
            },
            'new_content': {
                'en': 'New content to replace the line range (use \\n for line breaks)',
                'zh': '替换行范围的新内容（使用 \\n 作为换行符）',
            },
            'confirm': {
                'en': 'Whether to confirm before editing (default true)',
                'zh': '是否需要用户确认（默认 true）',
            },
        }

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def priority(self) -> int:
        return 90

    @property
    def parameters_model(self):
        return EditFileParams

    def execute(self, path: str, line_range: List[int], new_content: str, confirm: bool = True) -> Dict[str, Any]:
        """
        Execute file editing by replacing a line range

        Args:
            path: File path (relative to project root or absolute)
            line_range: Line range as [start_line, end_line] (1-based, inclusive)
            new_content: New content to replace the line range
            confirm: Whether to confirm before editing (default: True)

        Returns:
            Dict containing success status and edit details

        Raises:
            FileSystemError: If file not found, invalid line range, or write fails
        """
        # Extract start and end lines
        start_line, end_line = line_range

        # Resolve path
        if not os.path.isabs(path) and self.project_root:
            full_path = os.path.join(self.project_root, path)
        else:
            full_path = path

        full_path = os.path.abspath(full_path)

        # Security check
        if self.project_root:
            project_root = os.path.abspath(self.project_root)
            if not full_path.startswith(project_root):
                raise FileSystemError(f"Path {path} is outside project root")

        # Check file exists
        if not os.path.exists(full_path):
            raise FileSystemError(f"File not found: {path}")

        # Validate line range
        if start_line < 1:
            raise FileSystemError(f"start_line must be >= 1, got {start_line}")
        if end_line < start_line:
            raise FileSystemError(f"end_line ({end_line}) must be >= start_line ({start_line})")

        # Read file with Unix line endings
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
                content = f.read()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {path}: {e}")

        # Split into lines (preserve empty lines)
        lines = content.splitlines(keepends=False)
        total_lines = len(lines)

        # Validate line range against file size
        if start_line > total_lines:
            raise FileSystemError(
                f"start_line ({start_line}) exceeds file length ({total_lines} lines)"
            )
        if end_line > total_lines:
            raise FileSystemError(
                f"end_line ({end_line}) exceeds file length ({total_lines} lines)"
            )

        # Prepare new content lines (split by \n, preserve empty lines)
        new_lines = new_content.split('\n') if new_content else ['']

        # Replace the line range (convert to 0-based indexing)
        before = lines[:start_line - 1]
        after = lines[end_line:]
        result_lines = before + new_lines + after

        # Join with Unix line endings
        new_file_content = '\n'.join(result_lines)

        # Ensure file ends with newline if it originally did
        if content and content[-1] == '\n':
            new_file_content += '\n'

        # Write file with Unix line endings
        try:
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_file_content)

            old_line_count = end_line - start_line + 1
            new_line_count = len(new_lines)

            return {
                'success': True,
                'path': full_path,
                'line_range': line_range,
                'start_line': start_line,
                'end_line': end_line,
                'old_line_count': old_line_count,
                'new_line_count': new_line_count,
                'lines_changed': new_line_count - old_line_count,
                'message': f"Successfully edited {os.path.basename(full_path)} (lines {start_line}-{end_line})"
            }
        except Exception as e:
            raise FileSystemError(f"Failed to write file {path}: {e}")


# Export function interface for backward compatibility
def edit_file(path: str, line_range: List[int], new_content: str, project_root: str = None) -> Dict[str, Any]:
    """
    Edit file by replacing a line range with new content

    Args:
        path: File path (relative to project root or absolute)
        line_range: Line range as [start_line, end_line] (1-based, inclusive)
        new_content: New content to replace the line range
        project_root: Project root directory

    Returns:
        Dict containing success status and edit details
    """
    tool = EditFileTool(project_root=project_root)
    return tool.execute(path=path, line_range=line_range, new_content=new_content, confirm=False)
