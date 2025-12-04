# -*- coding: utf-8 -*-
"""
Feature Flags Manager
功能开关管理模块

所有非 bug 修复的新特性都通过此模块控制是否启用
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml


class FeatureFlags:
    """功能开关管理器"""

    _instance: Optional["FeatureFlags"] = None
    _config: dict = {}

    def __new__(cls) -> "FeatureFlags":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """加载功能开关配置"""
        # 项目根目录/config/feature.yaml
        config_path = Path(__file__).parent.parent.parent / "config" / "feature.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

    def is_enabled(self, feature_path: str) -> bool:
        """
        检查功能是否启用

        Args:
            feature_path: 功能路径，用点分隔，如 "ide_integration.inject_active_file_context"

        Returns:
            bool: 功能是否启用，默认 False
        """
        parts = feature_path.split(".")
        value = self._config

        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return False
            value = value[part]

        if isinstance(value, dict):
            return value.get("enabled", False)
        return bool(value)

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()


# 便捷函数
def is_feature_enabled(feature_path: str) -> bool:
    """检查功能是否启用"""
    return FeatureFlags().is_enabled(feature_path)
