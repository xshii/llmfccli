# -*- coding: utf-8 -*-
"""
CreateFile Tool - 创建文件
"""

import os
from typing import Any, Dict

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
    """创建文件工具"""

    @property
    def name(self) -> str:
        return "create_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': 'Create new file with content',
            'zh': '创建新文件并写入内容'
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path',
                'zh': '文件路径',
            },
            'content': {
                'en': 'File content',
                'zh': '文件内容',
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

    def get_diff_preview(self, path: str, content: str) -> None:
        """在 VSCode 中显示新建文件的差异预览（空 -> content）"""
        full_path = self.resolve_path(path)

        from backend.tools.diff_preview import get_diff_preview_manager
        get_diff_preview_manager().show_content_preview(
            file_path=full_path,
            new_content=content,
            title=f"Preview: Create {os.path.basename(full_path)}",
        )

    def execute(self, path: str, content: str) -> Dict[str, Any]:
        """执行文件创建"""
        # Resolve path and validate security
        try:
            path = self.resolve_and_validate_path(path)
        except ValueError as e:
            raise FileSystemError(str(e))

        # Check if file already exists
        if os.path.exists(path):
            raise FileSystemError(f"File already exists: {path}")

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
            raise FileSystemError(f"Failed to create file {path}: {e}")

        return ToolResult.success(f"Created {path} ({len(content)} bytes)")
