# -*- coding: utf-8 -*-
"""
LLM module for Ollama client and prompt management
"""

from .client import OllamaClient
from .prompts import (
    get_system_prompt,
    get_intent_prompt,
    get_todo_prompt,
    get_compile_error_prompt,
    get_compression_prompt,
    get_unit_test_prompt,
    get_integration_test_prompt,
    get_code_style_prompt,
    get_error_recovery_prompt,
)

__all__ = [
    'OllamaClient',
    'get_system_prompt',
    'get_intent_prompt',
    'get_todo_prompt',
    'get_compile_error_prompt',
    'get_compression_prompt',
    'get_unit_test_prompt',
    'get_integration_test_prompt',
    'get_code_style_prompt',
    'get_error_recovery_prompt',
]
