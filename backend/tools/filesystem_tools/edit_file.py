# -*- coding: utf-8 -*-
"""
EditFile Tool - Exact string replacement following Claude Code design
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
            'en': (
                'Performs exact string replacements in files.\n\n'
                'Usage:\n'
                '- Recommended: Use view_file first to get the exact string content, but you CAN call edit_file directly if you know the exact old_str.\n'
                '- If editing a previously viewed file, use the same path from that view_file call.\n'
                '- When editing text from view_file output, preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. '
                'The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. '
                'Never include any part of the line number prefix in old_str or new_str.\n'
                '- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.\n'
                '- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.\n'
                '- The edit will FAIL if old_str is not unique in the file. Either provide a larger string with more surrounding context to make it unique '
                'or use replace_all=True to change every instance of old_str.\n'
                '- Use replace_all for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.'
            ),
            'zh': (
                '对文件执行精确的字符串替换。\n\n'
                '使用说明：\n'
                '- 建议：先用 view_file 获取准确的字符串内容，但如果你确定准确的 old_str，可以直接调用 edit_file。\n'
                '- 如果编辑之前查看过的文件，使用与 view_file 调用相同的路径。\n'
                '- 编辑 view_file 输出的文本时，请保持行号前缀之后的精确缩进（制表符/空格）。'
                '行号前缀格式为：空格 + 行号 + 制表符。制表符之后才是实际的文件内容。'
                '绝不要在 old_str 或 new_str 中包含行号前缀的任何部分。\n'
                '- 始终优先编辑代码库中的现有文件。除非明确要求，否则不要创建新文件。\n'
                '- 仅在用户明确要求时使用表情符号。除非被要求，否则避免向文件中添加表情符号。\n'
                '- 如果 old_str 在文件中不唯一，编辑将失败。要么提供更大的字符串和更多上下文使其唯一，'
                '要么使用 replace_all=True 来更改 old_str 的所有实例。\n'
                '- 使用 replace_all 可以在整个文件中替换和重命名字符串。此参数在重命名变量等场景下很有用。'
            )
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
        if not os.path.isabs(path) and self.project_root:
            full_path = os.path.join(self.project_root, path)
        else:
            full_path = path
        full_path = os.path.abspath(full_path)

        # Check if file exists
        if not os.path.isfile(full_path):
            # Try to find similar file
            from backend.cli.path_utils import PathUtils
            path_utils = PathUtils(self.project_root or os.getcwd())
            similar = path_utils.find_similar_file(path)
            if similar:
                full_path = os.path.join(self.project_root or os.getcwd(), similar)
                full_path = os.path.abspath(full_path)
            else:
                return  # File doesn't exist, skip preview

        try:
            # Read file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if old_str exists
            if old_str not in content:
                return  # String not found, skip preview

            # Generate new content
            if replace_all:
                new_file_content = content.replace(old_str, new_str)
                title_op = f"Replace all ({content.count(old_str)} occurrences)"
            else:
                count = content.count(old_str)
                if count != 1:
                    return  # Not unique, skip preview
                new_file_content = content.replace(old_str, new_str, 1)
                title_op = "Replace"

            # Show diff in VSCode
            from backend.utils.feature import is_feature_enabled
            from backend.rpc.client import is_vscode_mode

            if is_vscode_mode() and is_feature_enabled("ide_integration.show_diff_before_edit"):
                from backend.tools.vscode_tools import vscode
                import time
                timestamp = int(time.time() * 1000)
                vscode.show_diff(
                    title=f"Preview: {title_op} in {os.path.basename(full_path)} [{timestamp}]",
                    original_path=full_path,
                    modified_content=new_file_content
                )
        except Exception:
            # Preview failed, continue silently
            pass

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
            # Try to find similar file
            from backend.cli.path_utils import PathUtils
            path_utils = PathUtils(self.project_root or os.getcwd())
            similar = path_utils.find_similar_file(path)
            if similar:
                # Use the similar file
                full_path = os.path.join(self.project_root or os.getcwd(), similar)
                full_path = os.path.abspath(full_path)
            else:
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

        return {
            'success': True,
            'message': f"Successfully {op_msg} in {os.path.basename(full_path)}"
        }
