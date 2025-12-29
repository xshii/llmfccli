# -*- coding: utf-8 -*-
"""
ListDir Tool - 列出目录内容
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool, ToolResult


class FileSystemError(Exception):
    """Filesystem operation error"""
    pass


class ListDirParams(BaseModel):
    """ListDir 工具参数"""
    path: str = Field(
        ".",
        description="Directory path (default '.')",
        json_schema_extra={"format": "filepath"}
    )
    max_depth: int = Field(
        3,
        description="Maximum traversal depth (default 3)"
    )


class ListDirTool(BaseTool):
    """列出目录内容工具"""

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': 'List directory contents recursively',
            'zh': '递归列出目录内容'
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'Directory path (default \'.\')',
                'zh': '目录路径（默认 \'.\'）',
            },
            'max_depth': {
                'en': 'Maximum traversal depth (default 3)',
                'zh': '最大遍历深度（默认 3）',
            },
        }
    @property
    def category(self) -> str:
        return "filesystem"

    @property
    def priority(self) -> int:
        return 65

    @property
    def parameters_model(self):
        return ListDirParams

    def execute(self, path: str = ".", max_depth: int = 3) -> Dict[str, Any]:
        """执行目录列表"""
        # Resolve path
        if not os.path.isabs(path) and self.project_root:
            dir_path = os.path.join(self.project_root, path)
        else:
            dir_path = path

        dir_path = os.path.abspath(dir_path)

        # Security check
        if self.project_root:
            project_root = os.path.abspath(self.project_root)
            if not dir_path.startswith(project_root):
                raise FileSystemError(f"Path {path} is outside project root")

        # Check directory exists
        if not os.path.exists(dir_path):
            raise FileSystemError(f"Directory not found: {path}")

        if not os.path.isdir(dir_path):
            raise FileSystemError(f"Not a directory: {path}")

        # List directory recursively
        def list_recursive(current_path, current_depth):
            if current_depth > max_depth:
                return []

            items = []
            try:
                for entry in sorted(os.listdir(current_path)):
                    if entry.startswith('.'):
                        continue

                    full_path = os.path.join(current_path, entry)
                    rel_path = os.path.relpath(full_path, dir_path)

                    if os.path.isdir(full_path):
                        items.append(f"{rel_path}/")
                        items.extend(list_recursive(full_path, current_depth + 1))
                    else:
                        items.append(rel_path)
            except PermissionError:
                pass

            return items

        tree = list_recursive(dir_path, 0)

        # Format as text
        items = tree[:500]
        output = '\n'.join(items)
        if len(tree) > 500:
            output += f"\n... ({len(tree) - 500} more items)"

        return ToolResult.success(output)
