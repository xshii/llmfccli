# -*- coding: utf-8 -*-
"""
System Reminder Manager
系统提示管理模块

自动读取 config/system_reminder.yaml 并生成注入到 LLM 上下文的提示信息
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml


class SystemReminder:
    """系统提示管理器"""

    _instance: Optional["SystemReminder"] = None
    _config: dict = {}

    def __new__(cls) -> "SystemReminder":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """加载系统提示配置"""
        config_path = Path(__file__).parent.parent / "config" / "system_reminder.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

    def get_config(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key_path: 配置路径，用点分隔，如 "git.main_branch"
            default: 默认值

        Returns:
            配置值
        """
        parts = key_path.split(".")
        value = self._config

        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]

        return value

    def get_git_hints(self) -> List[str]:
        """
        获取 Git 相关提示

        Returns:
            提示列表
        """
        hints = []

        # Git 主分支提示
        if self.get_config("git.show_main_branch_hint", False):
            main_branch = self.get_config("git.main_branch", "main")
            hint_template = self.get_config(
                "git.main_branch_hint",
                "Main branch (you will usually use this for PRs): {branch}"
            )
            hints.append(hint_template.format(branch=main_branch))

        return hints

    def get_project_hints(self) -> List[str]:
        """
        获取项目相关提示

        Returns:
            提示列表
        """
        hints = []

        # 项目类型提示
        if self.get_config("project.show_project_type", False):
            project_type = self.get_config("project.type", "unknown")
            hint_template = self.get_config(
                "project.project_type_hint",
                "Project type: {type}"
            )
            hints.append(hint_template.format(type=project_type))

        return hints

    def get_tool_hints(self) -> List[str]:
        """
        获取工具相关提示

        Returns:
            提示列表
        """
        hints = []

        # Git MR 工具提示
        if self.get_config("tools.git_mr.enabled", False):
            hint = self.get_config("tools.git_mr.hint", "")
            if hint:
                hints.append(hint)

        return hints

    def get_custom_hints(self) -> List[str]:
        """
        获取自定义提示

        Returns:
            提示列表
        """
        if not self.get_config("custom_hints.enabled", False):
            return []

        custom_hints = self.get_config("custom_hints.hints", [])
        return [str(hint) for hint in custom_hints if hint]

    def generate_system_reminder(self) -> str:
        """
        生成完整的 system reminder 文本

        Returns:
            system reminder 文本，如果没有任何提示则返回空字符串
        """
        all_hints = []

        # 收集所有提示
        all_hints.extend(self.get_git_hints())
        all_hints.extend(self.get_project_hints())
        all_hints.extend(self.get_tool_hints())
        all_hints.extend(self.get_custom_hints())

        # 如果没有任何提示，返回空字符串
        if not all_hints:
            return ""

        # 生成 system reminder 文本
        return "\n".join(all_hints)

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()


# 便捷函数
def get_system_reminder() -> str:
    """
    获取 system reminder 文本

    Returns:
        system reminder 文本
    """
    return SystemReminder().generate_system_reminder()


def get_main_branch() -> str:
    """
    获取主分支名称

    Returns:
        主分支名称
    """
    return SystemReminder().get_config("git.main_branch", "main")


def get_project_type() -> str:
    """
    获取项目类型

    Returns:
        项目类型
    """
    return SystemReminder().get_config("project.type", "unknown")
