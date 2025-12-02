# -*- coding: utf-8 -*-
"""
EditFile Tool - Performs exact string replacements in files
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field

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
    old_str: str = Field(
        description="Text to replace (must be unique in file). Provide surrounding context to ensure uniqueness."
    )
    new_str: str = Field(
        description="Replacement text (must preserve exact indentation)"
    )
    confirm: bool = Field(
        True,
        description="Whether to confirm before editing (default true)"
    )


class EditFileTool(BaseTool):
    """Edit file using exact string replacement"""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Performs exact string replacements in files. You must use view_file at least once before editing. '
                'The old_str must be unique in the file or the edit will fail. Provide larger context to ensure uniqueness. '
                'Preserve exact indentation (tabs/spaces) when editing.\n\n'
                'GOOD: old_str includes surrounding lines for uniqueness\n'
                'GOOD: Indentation matches exactly (spaces/tabs)\n'
                'BAD: old_str="return 0;" appears 10 times in file'
            ),
            'zh': (
                '执行精确字符串替换。必须先使用 view_file 读取文件。old_str 必须在文件中唯一，否则编辑失败。'
                '提供更大上下文确保唯一性。编辑时保持精确缩进（tabs/spaces）。\n\n'
                '好例子：old_str 包含周围行以确保唯一性\n'
                '好例子：缩进完全匹配（空格/制表符）\n'
                '坏例子：old_str="return 0;" 在文件中出现 10 次'
            )
        }


    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'old_str': {
                'en': 'Text to replace (must be unique in file). Include surrounding context to ensure uniqueness.',
                'zh': '要替换的文本（必须在文件中唯一）。包含周围上下文以确保唯一性。',
            },
            'new_str': {
                'en': 'Replacement text (preserve exact indentation - tabs/spaces)',
                'zh': '替换后的文本（保持精确缩进 - tabs/spaces）',
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
    def parameters_model(self):
        return EditFileParams

    def execute(self, path: str, old_str: str, new_str: str, confirm: bool = True) -> Dict[str, Any]:
        """
        Execute file editing with exact string replacement

        Args:
            path: File path (relative to project root or absolute)
            old_str: Text to replace (must be unique in file)
            new_str: Replacement text (preserve exact indentation)
            confirm: Whether to confirm before editing (default: True)

        Returns:
            Dict containing success status and edit details

        Raises:
            FileSystemError: If file not found, old_str not unique, or write fails
        """
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
            raise FileSystemError(
                f"Text not found in file: {old_str[:50]}...\n"
                f"Make sure to copy the exact text including indentation."
            )

        # Check uniqueness - must appear exactly once
        count = content.count(old_str)
        if count > 1:
            raise FileSystemError(
                f"Text appears {count} times in file (must be unique): {old_str[:50]}...\n"
                f"Provide more surrounding context to make it unique."
            )

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
