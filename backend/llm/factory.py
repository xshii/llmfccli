# -*- coding: utf-8 -*-
"""
LLM Client Factory

Creates appropriate LLM client based on configuration.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

from .base import BaseLLMClient


# Cache for loaded configuration
_config_cache: Optional[Dict] = None
_client_cache: Dict[str, BaseLLMClient] = {}


def load_config(config_path: Optional[str] = None, force_reload: bool = False) -> Dict:
    """
    Load LLM configuration from file

    Args:
        config_path: Path to config file (default: config/llm.yaml)
        force_reload: Force reload config even if cached

    Returns:
        Configuration dict
    """
    global _config_cache

    if _config_cache is not None and not force_reload:
        return _config_cache

    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "llm.yaml"

        # Fallback to ollama.yaml if llm.yaml doesn't exist
        if not Path(config_path).exists():
            config_path = project_root / "config" / "ollama.yaml"

    config_path = Path(config_path)

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            _config_cache = yaml.safe_load(f)
    else:
        # Default configuration
        _config_cache = {
            'default_backend': 'ollama',
            'ollama': {
                'enabled': True,
                'base_url': 'http://localhost:11434',
                'models': {'main': 'qwen3'},
                'retry': {'max_attempts': 3, 'backoff_factor': 2, 'initial_delay': 1}
            }
        }

    return _config_cache


def get_backend_for_task(task: Optional[str] = None) -> str:
    """
    Determine which backend to use for a given task

    Args:
        task: Task type ('main_agent', 'compression', 'intent', or None for default)

    Returns:
        Backend name ('ollama' or 'openai')
    """
    config = load_config()

    # Check task-specific override
    if task:
        task_backends = config.get('task_backends', {})
        task_backend = task_backends.get(task)
        if task_backend:
            return task_backend

    # Check environment variable override
    env_backend = os.getenv('DEFAULT_LLM_BACKEND')
    if env_backend:
        return env_backend

    # Use default from config
    return config.get('default_backend', 'ollama')


def create_client(
    backend: Optional[str] = None,
    task: Optional[str] = None,
    config_path: Optional[str] = None,
    use_cache: bool = True
) -> BaseLLMClient:
    """
    Create an LLM client based on configuration

    Args:
        backend: Explicit backend to use ('ollama' or 'openai')
        task: Task type for automatic backend selection
        config_path: Path to config file
        use_cache: Whether to cache and reuse client instances

    Returns:
        Configured LLM client instance

    Example:
        # Use default backend
        client = create_client()

        # Use specific backend
        client = create_client(backend='openai')

        # Use backend for specific task
        client = create_client(task='compression')
    """
    global _client_cache

    config = load_config(config_path)

    # Determine backend
    if backend is None:
        backend = get_backend_for_task(task)

    # Check cache
    cache_key = f"{backend}_{task or 'default'}"
    if use_cache and cache_key in _client_cache:
        return _client_cache[cache_key]

    # Create client based on backend
    if backend == 'openai':
        client = _create_openai_client(config, task)
    else:
        # Default to Ollama
        client = _create_ollama_client(config, task)

    # Cache client
    if use_cache:
        _client_cache[cache_key] = client

    return client


def _create_ollama_client(config: Dict, task: Optional[str] = None) -> BaseLLMClient:
    """Create Ollama client with appropriate model for task"""
    from .ollama import OllamaClient

    ollama_config = config.get('ollama', {})

    # Select model based on task
    models = ollama_config.get('models', {})
    if task == 'compression':
        model = models.get('compress', models.get('main', 'qwen3'))
    elif task == 'intent':
        model = models.get('intent', models.get('main', 'qwen3'))
    else:
        model = models.get('main', 'qwen3')

    # Build client config
    client_config = {
        'base_url': ollama_config.get('base_url', 'http://localhost:11434'),
        'model': model,
        'timeout': ollama_config.get('timeout', 300),
        'stream': ollama_config.get('stream', True),
        'generation': ollama_config.get('generation', {}),
        'retry': ollama_config.get('retry', {
            'max_attempts': 3,
            'backoff_factor': 2,
            'initial_delay': 1
        })
    }

    return OllamaClient(config=client_config)


def _create_openai_client(config: Dict, task: Optional[str] = None) -> BaseLLMClient:
    """Create OpenAI client with appropriate model for task"""
    from .openai_client import OpenAIClient

    openai_config = config.get('openai', {})

    # Select model based on task
    models = openai_config.get('models', {})
    if task == 'compression':
        model = models.get('compress', models.get('main', 'gpt-3.5-turbo'))
    elif task == 'intent':
        model = models.get('intent', models.get('main', 'gpt-3.5-turbo'))
    else:
        model = models.get('main', 'gpt-4-turbo')

    # Build client config
    client_config = {
        'base_url': openai_config.get('base_url', 'https://api.openai.com/v1'),
        'api_key': openai_config.get('api_key'),
        'timeout': openai_config.get('timeout', 300),
        'stream': openai_config.get('stream', True),
        'models': {'main': model},
        'generation': openai_config.get('generation', {
            'temperature': 0.1,
            'top_p': 0.9,
            'max_tokens': 4096
        }),
        'retry': openai_config.get('retry', {
            'max_attempts': 3,
            'backoff_factor': 2,
            'initial_delay': 1
        })
    }

    return OpenAIClient(config=client_config)


def clear_cache():
    """Clear the client cache"""
    global _client_cache, _config_cache
    _client_cache = {}
    _config_cache = None


def list_available_backends() -> Dict[str, bool]:
    """
    List available backends and their status

    Returns:
        Dict mapping backend name to enabled status
    """
    config = load_config()

    return {
        'ollama': config.get('ollama', {}).get('enabled', True),
        'openai': config.get('openai', {}).get('enabled', False)
    }
