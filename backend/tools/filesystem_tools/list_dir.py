# -*- coding: utf-8 -*-
"""
ListDir Tool - 列出目录内容
"""

import os
import platform
import subprocess
from typing import Any, Dict

from pydantic import BaseModel, Field

from backend.constants import Limit, Timeout, ToolDefaults
from backend.tools.base import BaseTool, FileSystemError, ToolResult


class ListDirParams(BaseModel):
    """ListDir 工具参数"""
    path: str = Field(
        ".",
        description="Directory path (default '.')",
        json_schema_extra={"format": "filepath"}
    )
    max_depth: int = Field(
        ToolDefaults.LIST_DIR_DEPTH,
        description=f"Maximum traversal depth (default {ToolDefaults.LIST_DIR_DEPTH})"
    )


class ListDirTool(BaseTool):
    """列出目录内容工具"""

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': 'List directory contents recursively with line counts',
            'zh': '递归列出目录内容及行数'
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        depth = ToolDefaults.LIST_DIR_DEPTH
        return {
            'path': {
                'en': 'Directory path (default \'.\')',
                'zh': '目录路径（默认 \'.\'）',
            },
            'max_depth': {
                'en': f'Maximum traversal depth (default {depth})',
                'zh': f'最大遍历深度（默认 {depth}）',
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

    def execute(self, path: str = ".", max_depth: int = ToolDefaults.LIST_DIR_DEPTH) -> Dict[str, Any]:
        """执行目录列表"""
        # Resolve path and validate security
        try:
            dir_path = self.resolve_and_validate_path(path)
        except ValueError as e:
            raise FileSystemError(str(e))

        # Check directory exists
        if not os.path.exists(dir_path):
            raise FileSystemError(f"Directory not found: {path}")

        if not os.path.isdir(dir_path):
            raise FileSystemError(f"Not a directory: {path}")

        is_windows = platform.system() == 'Windows'

        if is_windows:
            output = self._list_dir_windows(dir_path, max_depth)
        else:
            output = self._list_dir_unix(dir_path, max_depth)

        return ToolResult.success(output)

    def _list_dir_unix(self, dir_path: str, max_depth: int) -> str:
        """Use find + wc -l on Unix/Linux/Mac"""
        # Use find to list files with depth limit, then wc -l for line count
        max_files = Limit.FILE_LIST_MAX
        cmd = f"find '{dir_path}' -maxdepth {max_depth} -not -path '*/.*' | head -{max_files}"

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=Timeout.MEDIUM
            )
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"

        lines = []
        for file_path in files:
            if not file_path or file_path == dir_path:
                continue

            rel_path = os.path.relpath(file_path, dir_path)

            if os.path.isdir(file_path):
                lines.append(f"{rel_path}/")
            else:
                line_count = self._count_lines_unix(file_path)
                if line_count < 0:
                    lines.append(f"{rel_path}  (binary)")
                else:
                    lines.append(f"{rel_path}  {line_count} lines")

        return '\n'.join(lines)

    def _count_lines_unix(self, file_path: str) -> int:
        """Use wc -l to count lines, returns -1 for binary"""
        # Check binary by extension first
        binary_exts = {'.pyc', '.pyo', '.so', '.o', '.a', '.dll', '.exe',
                       '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf',
                       '.zip', '.tar', '.gz', '.bz2', '.7z', '.whl'}
        if os.path.splitext(file_path)[1].lower() in binary_exts:
            return -1

        # Use file command to check if binary
        try:
            result = subprocess.run(
                ['file', '--mime', file_path],
                capture_output=True, text=True, timeout=Timeout.QUICK
            )
            if 'binary' in result.stdout.lower() or 'application/' in result.stdout:
                if 'text' not in result.stdout.lower():
                    return -1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Use wc -l to count lines
        try:
            result = subprocess.run(
                ['wc', '-l', file_path],
                capture_output=True, text=True, timeout=Timeout.QUICK
            )
            if result.returncode == 0:
                # wc -l output: "  123 filename"
                return int(result.stdout.strip().split()[0])
        except (subprocess.TimeoutExpired, ValueError, IndexError):
            pass

        return -1

    def _list_dir_windows(self, dir_path: str, max_depth: int) -> str:
        """Use dir /s /b on Windows"""
        try:
            result = subprocess.run(
                f'dir /s /b "{dir_path}"',
                shell=True, capture_output=True, text=True, timeout=Timeout.MEDIUM
            )
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"

        lines = []
        count = 0
        max_files = Limit.FILE_LIST_MAX
        for file_path in files:
            if not file_path or count >= max_files:
                break

            rel_path = os.path.relpath(file_path.strip(), dir_path)

            if os.path.isdir(file_path.strip()):
                lines.append(f"{rel_path}/")
            else:
                line_count = self._count_lines_windows(file_path.strip())
                if line_count < 0:
                    lines.append(f"{rel_path}  (binary)")
                else:
                    lines.append(f"{rel_path}  {line_count} lines")
            count += 1

        return '\n'.join(lines)

    def _count_lines_windows(self, file_path: str) -> int:
        """Count lines on Windows using find /c /v"""
        binary_exts = {'.pyc', '.pyo', '.so', '.o', '.a', '.dll', '.exe',
                       '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf',
                       '.zip', '.tar', '.gz', '.bz2', '.7z', '.whl'}
        if os.path.splitext(file_path)[1].lower() in binary_exts:
            return -1

        try:
            # find /c /v "" counts all lines
            result = subprocess.run(
                f'find /c /v "" "{file_path}"',
                shell=True, capture_output=True, text=True, timeout=Timeout.QUICK
            )
            if result.returncode == 0:
                # Output: "---------- FILENAME: 123"
                parts = result.stdout.strip().split(':')
                if len(parts) >= 2:
                    return int(parts[-1].strip())
        except (subprocess.TimeoutExpired, ValueError):
            pass

        return -1
