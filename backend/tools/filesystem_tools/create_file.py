# -*- coding: utf-8 -*-
"""
CreateFile Tool - 创建文件
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


class CreateFileParams(BaseModel):
    """CreateFile 工具参数"""
    path: str = Field(description="文件路径")
    content: str = Field(description="文件内容")


class CreateFileTool(BaseTool):
    """创建文件工具"""

    @property
    def name(self) -> str:
        return "create_file"

    @property
    def description(self) -> str:
        return "Create new file with content"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def parameters_model(self):
        return CreateFileParams

    def execute(self, path: str, content: str) -> Dict[str, Any]:
        """执行文件创建"""
        # Resolve path
        if not os.path.isabs(path) and self.project_root:
            path = os.path.join(self.project_root, path)

        path = os.path.abspath(path)

        # Security check
        if self.project_root:
            project_root = os.path.abspath(self.project_root)
            if not path.startswith(project_root):
                raise FileSystemError(f"Path {path} is outside project root")

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
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise FileSystemError(f"Failed to create file {path}: {e}")

        return {
            'success': True,
            'path': path,
            'size': len(content)
        }
