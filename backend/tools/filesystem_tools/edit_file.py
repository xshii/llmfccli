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

        # INSERT MODE: When end_line < start_line (e.g., [3, 2] means insert after line 2)
        if end_line < start_line:
            # For insert mode, end_line represents the position to insert after
            if end_line < 0:
                raise ValueError(f"Insert position (end_line) must be >= 0, got {end_line}")
            # start_line should be end_line + 1 for clarity, but we'll allow any start > end
            return v

        # REPLACE MODE: Normal validation
        if start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {start_line}")
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
                'Edits a file with two modes: REPLACE or INSERT. You must use view_file at least once before editing. '
                'Use Unix line endings (\\n) in new_content.\n\n'
                '**REPLACE MODE** (when end_line >= start_line):\n'
                '  line_range=[10, 15] replaces lines 10-15 with new_content\n'
                '  line_range=[2, 2] replaces line 2 with new_content\n'
                '  Use cases: Fix bugs, refactor code, modify function implementations\n'
                '  Example: Change "def subtract(a, b):" to "def sub(a, b):" using line_range=[5, 5]\n\n'
                '**INSERT MODE** (when end_line < start_line):\n'
                '  line_range=[3, 2] inserts new_content AFTER line 2 (between lines 2 and 3)\n'
                '  line_range=[1, 0] inserts new_content at the beginning of the file\n'
                '  The original lines are preserved, and new content is inserted\n'
                '  Use cases: Add new functions, add imports, add documentation\n'
                '  Example: Add "import json" after "import sys" at line 2 using line_range=[3, 2]\n\n'
                '**Common Scenarios:**\n'
                '  • Add import: After "import sys" (line 2), use line_range=[3, 2], new_content="import json"\n'
                '  • Add function: After function ending at line 10, use line_range=[11, 10], new_content="\\ndef new_func():\\n    pass"\n'
                '  • Fix single line: Change line 5, use line_range=[5, 5], new_content="fixed_line"\n'
                '  • Add file header: Use line_range=[1, 0], new_content="#!/usr/bin/env python3\\n# -*- coding: utf-8 -*-"\n\n'
                'GOOD: line_range=[10, 15] replaces lines 10-15 (accurate line numbers from view_file)\n'
                'GOOD: line_range=[3, 2] inserts after line 2 (preserves line 2)\n'
                'BAD: Using wrong line numbers without checking view_file first'
            ),
            'zh': (
                '编辑文件，支持两种模式：替换或插入。必须先使用 view_file 读取文件。'
                '在 new_content 中使用 Unix 行结束符（\\n）。\n\n'
                '**替换模式** (当 end_line >= start_line)：\n'
                '  line_range=[10, 15] 将 10-15 行替换为 new_content\n'
                '  line_range=[2, 2] 将第 2 行替换为 new_content\n'
                '  使用场景：修复 bug、重构代码、修改函数实现\n'
                '  例子：将第 5 行 "def subtract(a, b):" 改为 "def sub(a, b):" 使用 line_range=[5, 5]\n\n'
                '**插入模式** (当 end_line < start_line)：\n'
                '  line_range=[3, 2] 在第 2 行之后插入 new_content（在第 2 行和第 3 行之间）\n'
                '  line_range=[1, 0] 在文件开头插入 new_content\n'
                '  原有行会被保留，新内容被插入\n'
                '  使用场景：添加新函数、添加导入语句、添加文档\n'
                '  例子：在第 2 行 "import sys" 后添加 "import json" 使用 line_range=[3, 2]\n\n'
                '**常见场景：**\n'
                '  • 添加导入：在 "import sys"（第 2 行）后，使用 line_range=[3, 2], new_content="import json"\n'
                '  • 添加函数：在第 10 行函数后，使用 line_range=[11, 10], new_content="\\ndef new_func():\\n    pass"\n'
                '  • 修复单行：修改第 5 行，使用 line_range=[5, 5], new_content="修复后的行"\n'
                '  • 添加文件头：使用 line_range=[1, 0], new_content="#!/usr/bin/env python3\\n# -*- coding: utf-8 -*-"\n\n'
                '好例子：line_range=[10, 15] 替换 10-15 行（使用 view_file 中准确的行号）\n'
                '好例子：line_range=[3, 2] 在第 2 行后插入（保留第 2 行）\n'
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

        # Determine operation mode: insert or replace
        if end_line < start_line:
            # INSERT MODE: line_range=[3, 2] means insert after line 2 (between lines 2 and 3)
            insert_after_line = end_line

            # Validate insert position
            if insert_after_line < 0:
                raise FileSystemError(f"Insert position must be >= 0, got {insert_after_line}")
            if insert_after_line > total_lines:
                raise FileSystemError(
                    f"Insert position ({insert_after_line}) exceeds file length ({total_lines} lines)"
                )

            # Insert new lines after insert_after_line (0-based indexing)
            before = lines[:insert_after_line]
            after = lines[insert_after_line:]
            result_lines = before + new_lines + after

            operation_mode = "insert"
            display_range = f"after line {insert_after_line}" if insert_after_line > 0 else "at beginning"
            old_line_count = 0
            new_line_count = len(new_lines)

        else:
            # REPLACE MODE: line_range=[2, 3] means replace lines 2-3
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

            operation_mode = "replace"
            display_range = f"lines {start_line}-{end_line}"
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
                'operation_mode': operation_mode,
                'message': f"Successfully edited {os.path.basename(full_path)} ({display_range})"
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
