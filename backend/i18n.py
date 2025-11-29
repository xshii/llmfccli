# -*- coding: utf-8 -*-
"""
国际化支持模块

提供工具描述和参数的多语言支持
"""

import os
import locale
from pathlib import Path
from typing import Dict, Optional, Any
import yaml


class I18n:
    """国际化管理器"""

    # 支持的语言
    SUPPORTED_LANGUAGES = {'en', 'zh'}

    # 默认语言
    DEFAULT_LANGUAGE = 'zh'

    # 当前语言（全局单例）
    _current_language: Optional[str] = None

    @classmethod
    def initialize(cls, language: Optional[str] = None):
        """
        初始化语言设置

        Args:
            language: 指定语言（'en' 或 'zh'），None 则从配置读取
        """
        if language:
            # 直接指定语言
            if language not in cls.SUPPORTED_LANGUAGES:
                print(f"警告: 不支持的语言 '{language}'，使用默认语言 '{cls.DEFAULT_LANGUAGE}'")
                cls._current_language = cls.DEFAULT_LANGUAGE
            else:
                cls._current_language = language
        else:
            # 从配置文件读取
            config_path = Path(__file__).parent.parent / 'config' / 'language.yaml'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                detection = config.get('detection', 'env')
                default = config.get('default', cls.DEFAULT_LANGUAGE)

                if detection == 'env':
                    # 从环境变量读取
                    lang = os.getenv('CLAUDE_QWEN_LANG', default)
                elif detection == 'auto':
                    # 自动检测系统语言
                    try:
                        system_lang = locale.getdefaultlocale()[0] or ''
                        if system_lang.startswith('zh'):
                            lang = 'zh'
                        else:
                            lang = 'en'
                    except Exception:
                        lang = default
                else:
                    # 使用配置中的默认语言
                    lang = default

                cls._current_language = lang if lang in cls.SUPPORTED_LANGUAGES else default
            else:
                cls._current_language = cls.DEFAULT_LANGUAGE

    @classmethod
    def get_language(cls) -> str:
        """获取当前语言"""
        if cls._current_language is None:
            cls.initialize()
        return cls._current_language or cls.DEFAULT_LANGUAGE

    @classmethod
    def set_language(cls, language: str):
        """设置当前语言"""
        if language not in cls.SUPPORTED_LANGUAGES:
            raise ValueError(f"不支持的语言: {language}")
        cls._current_language = language

    @classmethod
    def translate(cls, translations: Dict[str, str]) -> str:
        """
        根据当前语言翻译文本

        Args:
            translations: 翻译字典，例如 {'en': 'Hello', 'zh': '你好'}

        Returns:
            当前语言对应的文本，如果不存在则返回英文或第一个可用的
        """
        lang = cls.get_language()

        # 优先返回当前语言
        if lang in translations:
            return translations[lang]

        # 回退到英文
        if 'en' in translations:
            return translations['en']

        # 回退到第一个可用的
        if translations:
            return next(iter(translations.values()))

        return ''


def t(translations: Dict[str, str]) -> str:
    """
    翻译快捷函数

    Args:
        translations: 翻译字典，例如 {'en': 'Hello', 'zh': '你好'}

    Returns:
        当前语言对应的文本

    Examples:
        >>> t({'en': 'Read file', 'zh': '读取文件'})
        '读取文件'  # 如果当前语言是中文
    """
    return I18n.translate(translations)


def get_current_language() -> str:
    """获取当前语言"""
    return I18n.get_language()


def set_language(language: str):
    """设置当前语言"""
    I18n.set_language(language)


def field_description(translations: Dict[str, str]) -> str:
    """
    为 Pydantic Field 创建国际化描述

    Args:
        translations: 翻译字典，例如 {'en': 'File path', 'zh': '文件路径'}

    Returns:
        当前语言对应的描述

    Examples:
        >>> from pydantic import Field
        >>> path: str = Field(description=field_description({
        ...     'en': 'File path',
        ...     'zh': '文件路径'
        ... }))
    """
    return I18n.translate(translations)
