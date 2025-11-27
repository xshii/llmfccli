# -*- coding: utf-8 -*-
"""
路径处理工具模块

提供路径压缩和格式化功能
"""

import os
from typing import Optional


class PathUtils:
    """路径处理工具类"""

    def __init__(self, project_root: str):
        """
        初始化路径工具

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root

    def compress_path(self, path: str, max_length: int = 50) -> str:
        """智能压缩路径基于项目根目录

        策略:
        - 项目内路径: 显示相对路径，超过3层时压缩
        - 项目外路径: 显示绝对路径，超过4层时压缩

        示例:
            项目内 (/home/user/llmfccli):
                /home/user/llmfccli/backend/agent/tools.py -> backend/.../tools.py
                /home/user/llmfccli/tests/unit/test.py -> tests/unit/test.py (不压缩)

            项目外:
                /home/user/other/very/long/path/file.py -> /home/user/.../path/file.py
                /usr/lib/python3/site-packages/module.py -> /usr/lib/.../site-packages/module.py

        Args:
            path: 待压缩的路径
            max_length: 最大长度（当前未使用，保留用于未来扩展）

        Returns:
            压缩后的路径
        """
        # 检测路径分隔符 (/ 或 \)
        sep = '\\' if '\\' in path else '/'

        # 规范化路径用于比较
        path_abs = os.path.abspath(path) if not os.path.isabs(path) else path
        project_root_abs = os.path.abspath(self.project_root)

        # 检查路径是否在项目内
        try:
            # 尝试获取相对于项目根目录的路径
            if path_abs.startswith(project_root_abs + os.sep) or path_abs == project_root_abs:
                # 路径在项目内 - 使用相对路径
                rel_path = os.path.relpath(path_abs, project_root_abs)
                parts = rel_path.split(os.sep)

                # 项目相对路径，超过3层时压缩
                if len(parts) <= 3:
                    return rel_path

                # 压缩: 保留第一层 + 最后2层
                # 示例: backend/agent/tools/filesystem.py -> backend/.../filesystem.py
                compressed = f"{parts[0]}{sep}...{sep}{sep.join(parts[-2:])}"
                return compressed
        except (ValueError, OSError):
            pass

        # 路径在项目外 - 使用绝对路径并压缩
        parts = path_abs.split(os.sep)
        parts = [p for p in parts if p]  # 过滤空部分

        # 绝对路径，超过4层时压缩
        if len(parts) <= 4:
            return path_abs

        # 压缩: 保留前2层 + 最后2层
        prefix = os.sep if path_abs.startswith(os.sep) else ""
        compressed = f"{prefix}{os.sep.join(parts[:2])}{sep}...{sep}{os.sep.join(parts[-2:])}"

        return compressed
