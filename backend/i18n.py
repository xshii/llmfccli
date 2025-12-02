# -*- coding: utf-8 -*-
"""
Internationalization (i18n) Support Module

Provides multi-language support for tool descriptions and parameters
"""

import os
import locale
from pathlib import Path
from typing import Dict, Optional, Any
import yaml


class I18n:
    """Internationalization Manager"""

    # Supported languages
    SUPPORTED_LANGUAGES = {'en', 'zh'}

    # Default language
    DEFAULT_LANGUAGE = 'en'

    # Current language (global singleton)
    _current_language: Optional[str] = None

    @classmethod
    def initialize(cls, language: Optional[str] = None):
        """
        Initialize language settings

        Args:
            language: Specified language ('en' or 'zh'), None to read from config
        """
        if language:
            # Directly specify language
            if language not in cls.SUPPORTED_LANGUAGES:
                print(f"Warning: Unsupported language '{language}', using default language '{cls.DEFAULT_LANGUAGE}'")
                cls._current_language = cls.DEFAULT_LANGUAGE
            else:
                cls._current_language = language
        else:
            # Read from config file
            config_path = Path(__file__).parent.parent / 'config' / 'language.yaml'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                detection = config.get('detection', 'env')
                default = config.get('default', cls.DEFAULT_LANGUAGE)

                if detection == 'env':
                    # Read from environment variable
                    lang = os.getenv('CLAUDE_QWEN_LANG', default)
                elif detection == 'auto':
                    # Auto-detect system language
                    try:
                        system_lang = locale.getdefaultlocale()[0] or ''
                        if system_lang.startswith('zh'):
                            lang = 'zh'
                        else:
                            lang = 'en'
                    except Exception:
                        lang = default
                else:
                    # Use default language from config
                    lang = default

                cls._current_language = lang if lang in cls.SUPPORTED_LANGUAGES else default
            else:
                cls._current_language = cls.DEFAULT_LANGUAGE

    @classmethod
    def get_language(cls) -> str:
        """Get current language"""
        if cls._current_language is None:
            cls.initialize()
        return cls._current_language or cls.DEFAULT_LANGUAGE

    @classmethod
    def set_language(cls, language: str):
        """Set current language"""
        if language not in cls.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        cls._current_language = language

    @classmethod
    def translate(cls, translations: Dict[str, str]) -> str:
        """
        Translate text based on current language

        Args:
            translations: Translation dictionary, e.g., {'en': 'Hello', 'zh': '你好'}

        Returns:
            Text in current language, fallback to English or first available if not found
        """
        lang = cls.get_language()

        # Return current language first
        if lang in translations:
            return translations[lang]

        # Fallback to English
        if 'en' in translations:
            return translations['en']

        # Fallback to first available
        if translations:
            return next(iter(translations.values()))

        return ''


def t(translations: Dict[str, str]) -> str:
    """
    Translation shortcut function

    Args:
        translations: Translation dictionary, e.g., {'en': 'Hello', 'zh': '你好'}

    Returns:
        Text in current language

    Examples:
        >>> t({'en': 'Read file', 'zh': '读取文件'})
        'Read file'  # If current language is English
    """
    return I18n.translate(translations)


def get_current_language() -> str:
    """Get current language"""
    return I18n.get_language()


def set_language(language: str):
    """Set current language"""
    I18n.set_language(language)


def field_description(translations: Dict[str, str]) -> str:
    """
    Create internationalized description for Pydantic Field

    Args:
        translations: Translation dictionary, e.g., {'en': 'File path', 'zh': '文件路径'}

    Returns:
        Description in current language

    Examples:
        >>> from pydantic import Field
        >>> path: str = Field(description=field_description({
        ...     'en': 'File path',
        ...     'zh': '文件路径'
        ... }))
    """
    return I18n.translate(translations)
