# -*- coding: utf-8 -*-
"""
统一配置加载模块
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def get_config_dir() -> Path:
    """获取配置目录"""
    return get_project_root() / "config"


def load_yaml_config(config_path: Optional[Path] = None, filename: str = "llm.yaml") -> Dict[str, Any]:
    """
    加载 YAML 配置文件

    Args:
        config_path: 配置文件路径，如果为 None 则使用默认路径
        filename: 配置文件名

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    if config_path is None:
        config_path = get_config_dir() / filename

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_llm_config(
    config_path: Optional[str] = None,
    config: Optional[Dict] = None,
    section: str = "ollama"
) -> Dict[str, Any]:
    """
    加载 LLM 配置

    Args:
        config_path: 配置文件路径
        config: 直接提供的配置字典（优先级最高）
        section: 配置段名称 ('ollama' 或 'openai')

    Returns:
        配置字典
    """
    if config is not None:
        return config

    full_config = load_yaml_config(
        Path(config_path) if config_path else None
    )
    return full_config.get(section, {})


def resolve_env_var(value: Optional[str]) -> str:
    """
    解析环境变量引用

    支持格式:
    - ${VAR_NAME} - 从环境变量获取
    - 普通字符串 - 直接返回

    Args:
        value: 配置值

    Returns:
        解析后的值
    """
    if not value:
        return ''

    # 检查 ${VAR_NAME} 格式
    match = re.match(r'\$\{(\w+)\}', value)
    if match:
        env_var = match.group(1)
        return os.getenv(env_var, '')

    return value


def get_ssh_host() -> Optional[str]:
    """
    获取 SSH 隧道主机名

    Returns:
        SSH 主机名，未配置则返回 None
    """
    try:
        config = load_yaml_config()
        ssh_config = config.get('ssh', {})
        if ssh_config.get('enabled'):
            return ssh_config.get('host')
    except Exception:
        pass
    return None


def get_default_retry_config() -> Dict[str, Any]:
    """获取默认重试配置"""
    return {
        'max_attempts': 3,
        'backoff_factor': 2,
        'initial_delay': 1
    }


def get_default_generation_params() -> Dict[str, Any]:
    """获取默认生成参数"""
    return {
        'temperature': 0.1,
        'top_p': 0.9,
    }


class LLMConfig:
    """LLM 配置包装类"""

    def __init__(self, config: Dict[str, Any], section: str = "ollama"):
        """
        初始化配置

        Args:
            config: 配置字典
            section: 配置段名称
        """
        self.raw_config = config
        self.section = section

        # 基础配置
        self.base_url = config.get('base_url')
        self.model = config.get('model') or config.get('models', {}).get('main')
        self.timeout = config.get('timeout', 300)
        self.stream_enabled = config.get('stream', False)

        # 生成参数
        self.generation_params = config.get('generation', get_default_generation_params())

        # 重试配置
        self.retry_config = config.get('retry', get_default_retry_config())

    def validate(self, require_api_key: bool = False):
        """
        验证必需配置

        Args:
            require_api_key: 是否需要 API key

        Raises:
            ValueError: 缺少必需配置
        """
        if not self.base_url:
            raise ValueError("配置缺少 base_url")
        if not self.model:
            raise ValueError("配置缺少 model")
        if require_api_key and not self.raw_config.get('api_key'):
            raise ValueError("配置缺少 api_key")
