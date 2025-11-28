# -*- coding: utf-8 -*-
"""
EditFile Tool - 编辑文件
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


class EditFileParams(BaseModel):
    """EditFile 工具参数"""
    path: str = Field(description="文件路径")
    old_str: str = Field(description="要替换的字符串（必须唯一出现）")
    new_str: str = Field(description="替换后的字符串")
    confirm: bool = Field(True, description="是否需要用户确认（默认 true）")


class EditFileTool(BaseTool):
    """编辑文件工具"""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Edit file using str_replace (old_str must be unique)"

    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def parameters_model(self):
        return EditFileParams

    def execute(self, path: str, old_str: str, new_str: str, confirm: bool = True) -> Dict[str, Any]:
        """执行文件编辑"""
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

        # Read file
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {path}: {e}")

        # Check if old_str exists
        if old_str not in content:
            raise FileSystemError(f"String not found in file: {old_str[:50]}...")

        # Check uniqueness
        count = content.count(old_str)
        if count > 1:
            raise FileSystemError(f"String appears {count} times (must be unique): {old_str[:50]}...")

        # Generate new content
        new_content = content.replace(old_str, new_str)

        # Write file (直接写入，确认逻辑由 AgentLoop 处理)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return {
                'success': True,
                'path': full_path,
                'mode': 'direct',
                'old_str': old_str[:100] + ('...' if len(old_str) > 100 else ''),
                'new_str': new_str[:100] + ('...' if len(new_str) > 100 else ''),
                'changes': len(new_str) - len(old_str),
                'message': f"Successfully edited {os.path.basename(full_path)}"
            }
        except Exception as e:
            raise FileSystemError(f"Failed to write file {path}: {e}")
