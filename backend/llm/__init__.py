# -*- coding: utf-8 -*-
"""
LLM module for multi-backend LLM clients and prompt management

Supports:
- Ollama (local deployment)
- OpenAI-compatible APIs (internal/public LLMs)
"""

# Base class
from .base import BaseLLMClient

# Factory function (recommended way to create clients)
from .factory import (
    clear_cache,
    create_client,
    get_backend_for_task,
    list_available_backends,
    load_config,
)

# Client implementations
from .ollama import OllamaClient
from .openai_client import OpenAIClient

# Prompts
from .prompts import (
    get_code_style_prompt,
    get_compile_error_prompt,
    get_compression_prompt,
    get_error_recovery_prompt,
    get_integration_test_prompt,
    get_intent_prompt,
    get_system_prompt,
    get_todo_prompt,
    get_unit_test_prompt,
)
from .tool_adapter import PromptToolAdapter

__all__ = [
    # Base class
    'BaseLLMClient',
    # Clients
    'OllamaClient',
    'OpenAIClient',
    'PromptToolAdapter',
    # Factory
    'create_client',
    'load_config',
    'get_backend_for_task',
    'list_available_backends',
    'clear_cache',
    # Prompts
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
