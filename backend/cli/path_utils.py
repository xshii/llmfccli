# -*- coding: utf-8 -*-
"""
路径处理工具模块

提供路径压缩和格式化功能
"""

import os
from typing import Optional, List, Tuple
import glob as glob_module


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
        """智能压缩路径，根据字符长度选择性裁剪

        策略:
        1. 项目内路径优先使用相对路径
        2. 如果路径长度 <= max_length，直接返回
        3. 如果超过 max_length，智能压缩：
           - 保留文件名（最后一层）
           - 保留第一层目录
           - 中间层级用 ... 替代
           - 动态调整保留层级，确保不超过 max_length

        示例（max_length=50）:
            项目内:
                backend/agent/tools.py (19字符) -> backend/agent/tools.py (不压缩)
                backend/agent/tools/filesystem/view_file.py (44字符) -> backend/.../view_file.py (27字符)
                a/very/long/deeply/nested/path/to/some/file.py (46字符) -> a/.../file.py (13字符)

            项目外:
                /usr/lib/python3.11/site-packages/module.py (44字符) -> 不压缩
                /home/user/very/long/path/to/file.py (38字符) -> 不压缩
                /home/user/project/src/backend/api/v1/endpoints/users.py (55字符) -> /home/user/.../users.py (25字符)

        Args:
            path: 待压缩的路径
            max_length: 最大字符长度限制

        Returns:
            压缩后的路径
        """
        # 检测路径分隔符 (/ 或 \)
        sep = '\\' if '\\' in path else '/'

        # 规范化路径用于比较（相对路径基于项目根目录解析）
        if not os.path.isabs(path):
            path_abs = os.path.join(self.project_root, path)
        else:
            path_abs = path

        project_root_abs = os.path.abspath(self.project_root)

        # 确定显示路径（项目内用相对路径，项目外用绝对路径）
        display_path = path_abs
        is_project_internal = False

        try:
            # 尝试获取相对于项目根目录的路径
            if path_abs.startswith(project_root_abs + os.sep) or path_abs == project_root_abs:
                # 路径在项目内 - 使用相对路径
                display_path = os.path.relpath(path_abs, project_root_abs)
                is_project_internal = True
        except (ValueError, OSError):
            pass

        # 如果路径长度已经符合要求，直接返回
        if len(display_path) <= max_length:
            return display_path

        # 路径太长，需要压缩
        parts = display_path.split(os.sep)
        parts = [p for p in parts if p]  # 过滤空部分

        if len(parts) <= 1:
            # 只有一个部分，无法压缩，直接截断
            return display_path[:max_length - 3] + "..."

        # 智能压缩：保留第一层 + ... + 尽可能多的最后几层
        # 计算保留多少层
        filename = parts[-1]  # 文件名（必须保留）
        first_part = parts[0]   # 第一层目录（必须保留）

        # 基础压缩：first/.../filename
        ellipsis = "..."
        base_length = len(first_part) + len(sep) + len(ellipsis) + len(sep) + len(filename)

        if base_length <= max_length:
            # 尝试从倒数第二层开始，逐步增加保留层级
            last_parts = [filename]
            remaining_length = max_length - len(first_part) - len(sep) - len(ellipsis) - len(sep)

            for i in range(len(parts) - 2, 0, -1):  # 从倒数第二层向前遍历
                part = parts[i]
                needed_length = len(sep.join(last_parts)) + len(sep) + len(part)

                if needed_length <= remaining_length:
                    last_parts.insert(0, part)
                else:
                    break

            # 构建压缩路径
            if len(last_parts) == len(parts) - 1:
                # 可以保留所有层级，不需要省略号
                compressed = f"{first_part}{sep}{sep.join(last_parts)}"
            else:
                compressed = f"{first_part}{sep}{ellipsis}{sep}{sep.join(last_parts)}"
        else:
            # 基础压缩都超长，只能保留文件名
            if len(filename) > max_length:
                # 文件名本身太长，截断文件名
                compressed = filename[:max_length - 3] + "..."
            else:
                compressed = f"...{sep}{filename}"

        # 对于绝对路径，添加前缀
        if not is_project_internal and path_abs.startswith(os.sep):
            if not compressed.startswith(os.sep):
                compressed = os.sep + compressed

        return compressed

    def find_similar_file(self, path: str) -> Optional[str]:
        """
        当路径不存在时，查找最相似的文件

        策略:
        1. 提取文件名，搜索项目中同名文件
        2. 单个匹配：直接返回
        3. 多个匹配：按路径文件夹重合度排序，返回最高分

        Args:
            path: 不存在的路径

        Returns:
            最相似的文件路径（相对于项目根目录），或 None
        """
        # 提取文件名
        filename = os.path.basename(path)
        if not filename:
            return None

        # 在项目中搜索同名文件
        pattern = os.path.join(self.project_root, "**", filename)
        matches = glob_module.glob(pattern, recursive=True)

        if not matches:
            return None

        if len(matches) == 1:
            # 单个匹配，直接返回相对路径
            return os.path.relpath(matches[0], self.project_root)

        # 多个匹配，按路径相似度排序
        scored_matches = []
        path_parts = self._get_path_parts(path)

        for match in matches:
            rel_match = os.path.relpath(match, self.project_root)
            match_parts = self._get_path_parts(rel_match)
            score = self._calculate_path_similarity(path_parts, match_parts)
            scored_matches.append((score, rel_match))

        # 按分数降序排序
        scored_matches.sort(key=lambda x: x[0], reverse=True)

        # 返回最高分的路径
        return scored_matches[0][1]

    def find_similar_files(self, path: str) -> List[Tuple[float, str]]:
        """
        查找所有相似文件及其相似度分数

        Args:
            path: 不存在的路径

        Returns:
            按相似度降序排列的 (分数, 路径) 列表
        """
        filename = os.path.basename(path)
        if not filename:
            return []

        pattern = os.path.join(self.project_root, "**", filename)
        matches = glob_module.glob(pattern, recursive=True)

        if not matches:
            return []

        path_parts = self._get_path_parts(path)
        scored_matches = []

        for match in matches:
            rel_match = os.path.relpath(match, self.project_root)
            match_parts = self._get_path_parts(rel_match)
            score = self._calculate_path_similarity(path_parts, match_parts)
            scored_matches.append((score, rel_match))

        scored_matches.sort(key=lambda x: x[0], reverse=True)
        return scored_matches

    def _get_path_parts(self, path: str) -> List[str]:
        """提取路径中的文件夹名（不含文件名）"""
        # 规范化路径
        normalized = os.path.normpath(path)
        parts = normalized.split(os.sep)
        # 返回除文件名外的所有部分
        return [p for p in parts[:-1] if p and p != '.']

    def _calculate_path_similarity(self, parts1: List[str], parts2: List[str]) -> float:
        """
        计算两个路径的文件夹重合度

        Args:
            parts1: 第一个路径的文件夹列表
            parts2: 第二个路径的文件夹列表

        Returns:
            相似度分数 (0.0 - 1.0)
        """
        if not parts1 and not parts2:
            return 1.0
        if not parts1 or not parts2:
            return 0.0

        # 计算重合的文件夹数量
        set1 = set(parts1)
        set2 = set(parts2)
        intersection = set1 & set2
        union = set1 | set2

        # Jaccard 相似度
        base_score = len(intersection) / len(union) if union else 0.0

        # 额外加分：连续匹配的文件夹（从后向前）
        # 例如 src/utils/helper.cpp 和 lib/utils/helper.cpp 应该比 utils/src/helper.cpp 分数更高
        consecutive_bonus = 0.0
        min_len = min(len(parts1), len(parts2))
        for i in range(1, min_len + 1):
            if parts1[-i] == parts2[-i]:
                consecutive_bonus += 0.1 * i  # 越靠近文件名的匹配权重越高
            else:
                break

        return min(1.0, base_score + consecutive_bonus)
