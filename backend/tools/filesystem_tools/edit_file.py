# -*- coding: utf-8 -*-
"""
EditFile Tool - Exact string replacement following Claude Code design
"""

import os
from typing import Any, Dict

from pydantic import BaseModel, Field

from backend.tools.base import BaseTool, FileSystemError, ToolResult


class EditFileParams(BaseModel):
    """EditFile tool parameters"""
    path: str = Field(
        description="File path (relative to project root or absolute path)",
        json_schema_extra={"format": "filepath"}
    )
    old_str: str = Field(
        description="The exact string to replace (must appear exactly once in the file, unless replace_all is True)"
    )
    new_str: str = Field(
        description="The replacement string"
    )
    replace_all: bool = Field(
        default=False,
        description="If True, replace all occurrences of old_str. If False (default), old_str must be unique"
    )


class EditFileTool(BaseTool):
    """Edit file using exact string replacement (Claude Code style)"""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': 'Replace exact string in file. old_str must be unique (or use replace_all=True).',
            'zh': '精确替换文件中的字符串。old_str 必须唯一（或使用 replace_all=True）。'
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'path': {
                'en': 'File path (relative to project root or absolute path)',
                'zh': '文件路径（相对于项目根目录或绝对路径）',
            },
            'old_str': {
                'en': 'The exact string to replace (must be unique unless replace_all=True). Include surrounding context to ensure uniqueness',
                'zh': '要替换的精确字符串（除非 replace_all=True，否则必须唯一）。包含周围上下文以确保唯一性',
            },
            'new_str': {
                'en': 'The replacement string',
                'zh': '替换后的字符串',
            },
            'replace_all': {
                'en': 'If True, replace all occurrences. If False (default), old_str must appear exactly once',
                'zh': '如果为 True，替换所有出现的位置。如果为 False（默认），old_str 必须恰好出现一次',
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

    def get_diff_preview(self, path: str, old_str: str, new_str: str, replace_all: bool = False) -> None:
        """
        Generate and show diff preview in VSCode (without applying changes)

        Args:
            path: File path
            old_str: String to replace
            new_str: Replacement string
            replace_all: Replace all occurrences
        """
        # Resolve path
        full_path = self.resolve_path(path)

        # Check if file exists (with fuzzy matching fallback)
        if not os.path.isfile(full_path):
            try:
                full_path = self.find_file_with_fallback(path)
            except FileNotFoundError:
                return  # File doesn't exist, skip preview

        # Use DiffPreviewManager to show preview
        from backend.tools.diff_preview import get_diff_preview_manager
        get_diff_preview_manager().show_replace_preview(
            file_path=full_path,
            old_str=old_str,
            new_str=new_str,
            replace_all=replace_all
        )

    def execute(self, path: str, old_str: str, new_str: str, replace_all: bool = False) -> Dict[str, Any]:
        """
        Execute exact string replacement

        Args:
            path: File path (relative to project root or absolute)
            old_str: String to replace (must be unique unless replace_all=True)
            new_str: Replacement string
            replace_all: If True, replace all occurrences. If False, old_str must be unique

        Returns:
            Dict containing success status and message

        Raises:
            FileSystemError: If file not found, string not found, or not unique
        """
        # Resolve path and validate security
        try:
            full_path = self.resolve_and_validate_path(path)
        except ValueError as e:
            raise FileSystemError(str(e))

        # Check file exists (with fuzzy matching fallback)
        if not os.path.exists(full_path):
            try:
                full_path = self.find_file_with_fallback(path)
            except FileNotFoundError:
                raise FileSystemError(f"File not found: {path}")

        # Read file
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise FileSystemError(f"Failed to read file {path}: {e}")

        # Check old_str exists
        if old_str not in content:
            raise FileSystemError(f"String not found in file: {old_str[:50]}...")

        # Check uniqueness (unless replace_all)
        if not replace_all:
            count = content.count(old_str)
            if count > 1:
                raise FileSystemError(
                    f"String appears {count} times in file (must be unique). "
                    f"Either provide more surrounding context to make it unique, "
                    f"or use replace_all=True to replace all occurrences."
                )

        # Perform replacement
        if replace_all:
            count = content.count(old_str)
            new_content = content.replace(old_str, new_str)
            op_msg = f"replaced all {count} occurrences"
        else:
            new_content = content.replace(old_str, new_str, 1)
            op_msg = "replaced 1 occurrence"

        # Write file
        try:
            with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_content)
        except Exception as e:
            raise FileSystemError(f"Failed to write file {path}: {e}")

        return ToolResult.success(f"Successfully {op_msg} in {os.path.basename(full_path)}")
