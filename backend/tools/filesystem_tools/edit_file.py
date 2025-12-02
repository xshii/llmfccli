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
        description="Line range [start_line, end_line]. REPLACE MODE: [10, 15] replaces lines 10-15. INSERT MODE: [3, 2] inserts after line 2",
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
                'Edit file by replacing lines. Line numbers start from 1. Must use view_file first. Use \\n for line breaks.\n\n'
                '**How it works:**\n'
                '  line_range=[start, end] replaces lines start to end (inclusive) with new_content\n\n'
                '**Examples:**\n'
                '  # Replace line 5\n'
                '  line_range=[5, 5], new_content="fixed line"\n\n'
                '  # Replace lines 2-4\n'
                '  line_range=[2, 4], new_content="new\\ncode\\nhere"\n\n'
                '  # Insert after line 2 (keep line 2, add new line after it)\n'
                '  line_range=[2, 2], new_content="original line 2 content\\nimport json"\n\n'
                '  # Insert at beginning\n'
                '  line_range=[1, 1], new_content="#!/usr/bin/env python3\\noriginal line 1 content"\n\n'
                '**Key rule:** To insert without removing existing content, include the original line(s) in new_content.'
            ),
            'zh': (
                '通过替换行来编辑文件。行号从 1 开始。必须先使用 view_file。使用 \\n 换行。\n\n'
                '**工作原理：**\n'
                '  line_range=[start, end] 将第 start 到 end 行（包含）替换为 new_content\n\n'
                '**示例：**\n'
                '  # 替换第 5 行\n'
                '  line_range=[5, 5], new_content="修复的行"\n\n'
                '  # 替换第 2-4 行\n'
                '  line_range=[2, 4], new_content="新\\n代码\\n这里"\n\n'
                '  # 在第 2 行后插入（保留第 2 行，在后面添加新行）\n'
                '  line_range=[2, 2], new_content="原第2行内容\\nimport json"\n\n'
                '  # 在开头插入\n'
                '  line_range=[1, 1], new_content="#!/usr/bin/env python3\\n原第1行内容"\n\n'
                '**关键规则：** 要插入而不删除现有内容，需要在 new_content 中包含原行内容。'
            )
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'line_range': {
                'en': 'Line range [start_line, end_line]. REPLACE: [10, 15] replaces lines 10-15. INSERT: [3, 2] inserts after line 2',
                'zh': '行范围 [起始行, 结束行]。替换：[10, 15] 替换 10-15 行。插入：[3, 2] 在第 2 行后插入',
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

        # Validate line_range
        if end_line < start_line:
            raise FileSystemError(f"end_line ({end_line}) must be >= start_line ({start_line})")

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

        # Read file with Unix line endings
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
                content = f.read()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {path}: {e}")

        # Split into lines (preserve empty lines)
        lines = content.splitlines(keepends=False)
        total_lines = len(lines)

        # Prepare new content lines (split by \n, preserve empty lines)
        new_lines = new_content.split('\n') if new_content else ['']

        # Validate line range
        if start_line < 1:
            raise FileSystemError(f"start_line must be >= 1, got {start_line}")
        if end_line > total_lines:
            raise FileSystemError(
                f"end_line ({end_line}) exceeds file length ({total_lines} lines)"
            )

        # Replace the line range (convert to 0-based indexing)
        before = lines[:start_line - 1]
        after = lines[end_line:]
        result_lines = before + new_lines + after

        old_line_count = end_line - start_line + 1
        new_line_count = len(new_lines)

        # Join with Unix line endings
        new_file_content = '\n'.join(result_lines)

        # Ensure file ends with newline if it originally did
        if content and content[-1] == '\n':
            new_file_content += '\n'

        # VSCode integration: Show diff preview before applying changes
        from backend.feature import is_feature_enabled
        from backend.rpc.client import is_vscode_mode

        if is_vscode_mode() and is_feature_enabled("ide_integration.show_diff_before_edit"):
            try:
                from backend.tools.vscode_tools import vscode

                # Show diff in VSCode
                vscode.show_diff(
                    title=f"Edit {os.path.basename(full_path)} (lines {start_line}-{end_line})",
                    original_path=full_path,
                    modified_content=new_file_content
                )

                # Future: Wait for user confirmation if enabled
                # if is_feature_enabled("ide_integration.require_user_confirm"):
                #     # TODO: Implement confirmation mechanism via RPC
                #     pass

            except Exception as e:
                # If VSCode diff preview fails, continue with file write
                # This ensures edit_file still works even if VSCode integration fails
                pass

        # Write file with Unix line endings
        try:
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_file_content)

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
