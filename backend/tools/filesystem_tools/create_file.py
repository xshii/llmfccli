# -*- coding: utf-8 -*-
"""
CreateFile Tool - 创建新文件或覆写已有文件
"""

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from backend.tools.base import BaseTool, FileSystemError, ToolResult


class CreateFileParams(BaseModel):
    """CreateFile 工具参数"""
    path: str = Field(
        description="File path"
    )
    content: str = Field(
        description="File content"
    )


class CreateFileTool(BaseTool):
    """创建新文件或覆写已有文件"""

    @property
    def name(self) -> str:
        return "create_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Create a new file or overwrite an existing file with full content. '
                'Use this for new files or when you need to rewrite an entire file. '
                'For partial edits (replacing specific lines), prefer edit_file instead.'
            ),
            'zh': (
                '创建新文件或用完整内容覆写已有文件。'
                '用于新建文件或需要重写整个文件的场景。'
                '如果只需修改特定几行，优先使用 edit_file。'
            ),
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'content': {
                'en': 'Complete file content to write',
                'zh': '要写入的完整文件内容',
            },
        }

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def priority(self) -> int:
        return 40

    @property
    def parameters_model(self):
        return CreateFileParams

    def get_diff_preview(
        self,
        path: str,
        content: str,
        interactive: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Show diff preview for creating or overwriting a file"""
        full_path = self.resolve_path(path)
        is_new = not os.path.isfile(full_path)

        from backend.tools.diff_preview import get_diff_preview_manager
        title = f"Preview: Create {os.path.basename(full_path)}" if is_new else None
        return get_diff_preview_manager().show_content_preview(
            file_path=full_path,
            new_content=content,
            title=title,
            interactive=interactive,
        )

    def execute(self, path: str, content: str) -> Dict[str, Any]:
        """执行文件创建或覆写"""
        # Resolve path and validate security
        try:
            path = self.resolve_and_validate_path(path)
        except ValueError as e:
            raise FileSystemError(str(e))

        is_overwrite = os.path.exists(path)

        # Create parent directories
        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except Exception as e:
                raise FileSystemError(f"Failed to create directory {parent_dir}: {e}")

        # Write file
        try:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
        except Exception as e:
            raise FileSystemError(f"Failed to write file {path}: {e}")

        if is_overwrite:
            return ToolResult.success(f"Overwrote {path} ({len(content)} bytes)")
        return ToolResult.success(f"Created {path} ({len(content)} bytes)")
