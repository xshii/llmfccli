# -*- coding: utf-8 -*-
"""
DiffPreviewManager - 统一的差异预览管理

提供文件编辑前的差异预览功能，支持 VSCode 集成。
"""

import os
import time
from typing import Optional


class DiffPreviewManager:
    """差异预览管理器

    用于在文件编辑前显示差异预览，支持 VSCode 集成。

    Usage:
        manager = DiffPreviewManager()
        manager.show_replace_preview(
            file_path="/path/to/file.py",
            old_str="old text",
            new_str="new text"
        )
    """

    def __init__(self):
        self._vscode = None
        self._vscode_mode = None
        self._feature_enabled = None

    def _is_preview_enabled(self) -> bool:
        """检查是否启用差异预览"""
        if self._vscode_mode is None:
            from backend.rpc.client import is_vscode_mode
            self._vscode_mode = is_vscode_mode()

        if not self._vscode_mode:
            return False

        if self._feature_enabled is None:
            from backend.utils.feature import is_feature_enabled
            self._feature_enabled = is_feature_enabled("ide_integration.show_diff_before_edit")

        return self._feature_enabled

    def _get_vscode(self):
        """获取 VSCode 工具实例"""
        if self._vscode is None:
            from backend.tools.vscode_tools import vscode
            self._vscode = vscode
        return self._vscode

    def show_replace_preview(
        self,
        file_path: str,
        old_str: str,
        new_str: str,
        replace_all: bool = False
    ) -> bool:
        """
        显示字符串替换的差异预览

        Args:
            file_path: 文件绝对路径
            old_str: 要替换的字符串
            new_str: 替换后的字符串
            replace_all: 是否替换所有出现

        Returns:
            bool: 是否成功显示预览
        """
        if not self._is_preview_enabled():
            return False

        try:
            # 读取文件
            if not os.path.isfile(file_path):
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查字符串是否存在
            if old_str not in content:
                return False

            # 生成新内容
            count = content.count(old_str)
            if replace_all:
                new_content = content.replace(old_str, new_str)
                title_op = f"Replace all ({count} occurrences)"
            else:
                if count != 1:
                    return False  # 不唯一，跳过预览
                new_content = content.replace(old_str, new_str, 1)
                title_op = "Replace"

            # 显示差异
            timestamp = int(time.time() * 1000)
            self._get_vscode().show_diff(
                title=f"Preview: {title_op} in {os.path.basename(file_path)} [{timestamp}]",
                original_path=file_path,
                modified_content=new_content
            )
            return True

        except Exception:
            return False

    def show_content_preview(
        self,
        file_path: str,
        new_content: str,
        title: Optional[str] = None
    ) -> bool:
        """
        显示任意内容变更的差异预览

        Args:
            file_path: 文件绝对路径（新建文件时可以不存在）
            new_content: 新的文件内容
            title: 可选的预览标题

        Returns:
            bool: 是否成功显示预览
        """
        if not self._is_preview_enabled():
            return False

        try:
            timestamp = int(time.time() * 1000)
            display_title = title or f"Preview: {os.path.basename(file_path)} [{timestamp}]"

            self._get_vscode().show_diff(
                title=display_title,
                original_path=file_path,
                modified_content=new_content
            )
            return True

        except Exception:
            return False


# 全局单例
_diff_preview_manager: Optional[DiffPreviewManager] = None


def get_diff_preview_manager() -> DiffPreviewManager:
    """获取差异预览管理器单例"""
    global _diff_preview_manager
    if _diff_preview_manager is None:
        _diff_preview_manager = DiffPreviewManager()
    return _diff_preview_manager
