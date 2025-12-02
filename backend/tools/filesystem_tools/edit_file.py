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
        description="Line range [start_line, end_line] (1-indexed)",
        min_items=2,
        max_items=2
    )
    new_content: str = Field(
        description="New content (use \\n for line breaks)"
    )
    operation: int = Field(
        description="Operation type: 0=replace lines, 1=insert before line, 2=insert after line"
    )

    @validator('operation')
    def validate_operation(cls, v):
        if v not in (0, 1, 2):
            raise ValueError(f"operation must be 0 (replace), 1 (insert_before), or 2 (insert_after), got {v}")
        return v

    @validator('line_range')
    def validate_line_range(cls, v, values):
        if len(v) != 2:
            raise ValueError("line_range must contain exactly 2 elements: [start_line, end_line]")
        start_line, end_line = v

        if start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {start_line}")

        operation = values.get('operation', 0)

        # For replace mode, validate end_line
        if operation == 0:
            if end_line < start_line:
                raise ValueError(f"Replace operation: end_line ({end_line}) must be >= start_line ({start_line})")
        # For insert modes, only start_line is used (end_line is ignored)
        # No validation needed for end_line in insert modes

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
                'Edit file with explicit operation type. Line numbers start from 1.\n\n'
                'Examples:\n'
                '  operation=0, line_range=[5, 5], new_content="fixed"  # Replace line 5\n'
                '  operation=0, line_range=[2, 4], new_content="new\\ncode"  # Replace lines 2-4\n'
                '  operation=1, line_range=[3, 3], new_content="import json"  # Insert before line 3\n'
                '  operation=2, line_range=[2, 2], new_content="import json"  # Insert after line 2'
            ),
            'zh': (
                '使用明确操作类型编辑文件。行号从 1 开始。\n\n'
                '示例：\n'
                '  operation=0, line_range=[5, 5], new_content="修复"  # 替换第 5 行\n'
                '  operation=0, line_range=[2, 4], new_content="新\\n代码"  # 替换第 2-4 行\n'
                '  operation=1, line_range=[3, 3], new_content="import json"  # 在第 3 行前插入\n'
                '  operation=2, line_range=[2, 2], new_content="import json"  # 在第 2 行后插入'
            )
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'line_range': {
                'en': '[start_line, end_line] (1-indexed). For insert operations (1/2), only start_line is used',
                'zh': '[起始行, 结束行]（从1开始）。插入操作（1/2）只使用起始行',
            },
            'new_content': {
                'en': 'New content (use \\n for line breaks)',
                'zh': '新内容（使用 \\n 换行）',
            },
            'operation': {
                'en': 'Operation type (required): 0=replace (uses both start and end), 1=insert before (uses start only), 2=insert after (uses start only)',
                'zh': '操作类型（必填）：0=替换（使用起始和结束行），1=在前插入（只使用起始行），2=在后插入（只使用起始行）',
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

    def get_diff_preview(self, path: str, line_range: List[int], new_content: str, operation: int) -> None:
        """
        Generate and show diff preview in VSCode (without applying changes)

        This method is called by Agent during confirmation stage to show the diff
        before user confirms the operation.

        Args:
            path: File path
            line_range: Line range [start_line, end_line] (for insert ops, only start_line is used)
            new_content: New content
            operation: Operation type (0=replace, 1=insert_before, 2=insert_after)
        """
        start_line, end_line = line_range

        # Resolve path
        if not os.path.isabs(path) and self.project_root:
            full_path = os.path.join(self.project_root, path)
        else:
            full_path = path
        full_path = os.path.abspath(full_path)

        # Check if file exists
        if not os.path.isfile(full_path):
            return  # File doesn't exist, skip preview

        try:
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Calculate new content based on operation
            lines = content.splitlines(keepends=False)
            new_lines = new_content.split('\n') if new_content else ['']

            if operation == 0:  # replace
                before = lines[:start_line - 1]
                after = lines[end_line:]
                result_lines = before + new_lines + after
                title_op = "Replace"
            elif operation == 1:  # insert_before (only uses start_line)
                before = lines[:start_line - 1]
                after = lines[start_line - 1:]
                result_lines = before + new_lines + after
                title_op = "Insert before"
            elif operation == 2:  # insert_after (only uses start_line)
                before = lines[:start_line]
                after = lines[start_line:]
                result_lines = before + new_lines + after
                title_op = "Insert after"
            else:
                return  # Invalid operation

            new_file_content = '\n'.join(result_lines)

            if content and content[-1] == '\n':
                new_file_content += '\n'

            # Show diff in VSCode
            from backend.feature import is_feature_enabled
            from backend.rpc.client import is_vscode_mode

            if is_vscode_mode() and is_feature_enabled("ide_integration.show_diff_before_edit"):
                from backend.tools.vscode_tools import vscode
                import time
                timestamp = int(time.time() * 1000)  # Milliseconds timestamp
                vscode.show_diff(
                    title=f"Preview: {title_op} line {start_line} in {os.path.basename(full_path)} [{timestamp}]",
                    original_path=full_path,
                    modified_content=new_file_content
                )
        except Exception:
            # Preview failed, continue silently
            pass

    def execute(self, path: str, line_range: List[int], new_content: str, operation: int) -> Dict[str, Any]:
        """
        Execute file editing with specified operation

        Args:
            path: File path (relative to project root or absolute)
            line_range: Line range as [start_line, end_line] (1-based). For insert operations, only start_line is used
            new_content: New content
            operation: Operation type (0=replace, 1=insert_before, 2=insert_after)

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

        # Validate line range based on operation
        if start_line < 1:
            raise FileSystemError(f"start_line must be >= 1, got {start_line}")

        if operation == 0:  # replace operation
            if end_line < start_line:
                raise FileSystemError(f"Replace operation: end_line ({end_line}) must be >= start_line ({start_line})")
            if end_line > total_lines:
                raise FileSystemError(f"end_line ({end_line}) exceeds file length ({total_lines} lines)")
            # Replace lines
            before = lines[:start_line - 1]
            after = lines[end_line:]
            result_lines = before + new_lines + after
            op_msg = f"replaced lines {start_line}-{end_line}"

        elif operation == 1:  # insert_before (only uses start_line)
            if start_line > total_lines:
                raise FileSystemError(f"start_line ({start_line}) exceeds file length ({total_lines} lines)")
            # Insert before line
            before = lines[:start_line - 1]
            after = lines[start_line - 1:]
            result_lines = before + new_lines + after
            op_msg = f"inserted before line {start_line}"

        elif operation == 2:  # insert_after (only uses start_line)
            if start_line > total_lines:
                raise FileSystemError(f"start_line ({start_line}) exceeds file length ({total_lines} lines)")
            # Insert after line
            before = lines[:start_line]
            after = lines[start_line:]
            result_lines = before + new_lines + after
            op_msg = f"inserted after line {start_line}"

        else:
            raise FileSystemError(f"Invalid operation: {operation} (must be 0, 1, or 2)")

        # Join with Unix line endings
        new_file_content = '\n'.join(result_lines)

        # Ensure file ends with newline if it originally did
        if content and content[-1] == '\n':
            new_file_content += '\n'

        # Write file with Unix line endings
        try:
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_file_content)

            return {
                'success': True,
                'message': f"Successfully {op_msg} in {os.path.basename(full_path)}"
            }
        except Exception as e:
            raise FileSystemError(f"Failed to write file {path}: {e}")


# Export function interface for backward compatibility
def edit_file(path: str, line_range: List[int], new_content: str, mode: int, project_root: str = None) -> Dict[str, Any]:
    """
    Edit file with specified mode

    Args:
        path: File path (relative to project root or absolute)
        line_range: Line range as [start_line, end_line] (1-based)
        new_content: New content
        project_root: Project root directory
        mode: Edit mode (0=replace, 1=insert_before, 2=insert_after)

    Returns:
        Dict containing success status and edit details
    """
    tool = EditFileTool(project_root=project_root)
    return tool.execute(path=path, line_range=line_range, new_content=new_content, mode=mode)
