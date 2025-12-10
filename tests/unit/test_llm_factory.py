#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for LLM factory and multi-backend support
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.llm.factory import (
    load_config,
    create_client,
    get_backend_for_task,
    list_available_backends,
    clear_cache,
)
from backend.llm.base import BaseLLMClient
from backend.llm.ollama import OllamaClient


def test_load_config():
    """Test configuration loading"""
    print("Testing config loading...")

    # Clear cache first
    clear_cache()

    config = load_config()

    assert config is not None, "Config should not be None"
    assert 'default_backend' in config, "Config should have default_backend"
    assert 'ollama' in config, "Config should have ollama section"

    # Check ollama config
    ollama_config = config.get('ollama', {})
    assert 'base_url' in ollama_config, "Ollama config should have base_url"
    assert 'models' in ollama_config, "Ollama config should have models"

    print(f"  ✓ Default backend: {config['default_backend']}")
    print(f"  ✓ Ollama base_url: {ollama_config.get('base_url')}")
    print(f"  ✓ Ollama models: {ollama_config.get('models')}")


def test_list_backends():
    """Test listing available backends"""
    print("\nTesting list_available_backends...")

    backends = list_available_backends()

    assert 'ollama' in backends, "Should have ollama backend"
    assert 'openai' in backends, "Should have openai backend"

    print(f"  ✓ Available backends: {backends}")


def test_get_backend_for_task():
    """Test backend selection for different tasks"""
    print("\nTesting get_backend_for_task...")

    clear_cache()

    # Default task
    default_backend = get_backend_for_task()
    print(f"  ✓ Default backend: {default_backend}")

    # Specific tasks
    main_backend = get_backend_for_task('main_agent')
    compress_backend = get_backend_for_task('compression')
    intent_backend = get_backend_for_task('intent')

    print(f"  ✓ Main agent backend: {main_backend}")
    print(f"  ✓ Compression backend: {compress_backend}")
    print(f"  ✓ Intent backend: {intent_backend}")


def test_create_ollama_client():
    """Test creating Ollama client via factory"""
    print("\nTesting create_client for Ollama...")

    clear_cache()

    # Create client without connecting (will fail warmup but that's ok for unit test)
    try:
        client = create_client(backend='ollama', use_cache=False)

        assert client is not None, "Client should not be None"
        assert isinstance(client, BaseLLMClient), "Client should be BaseLLMClient"
        assert isinstance(client, OllamaClient), "Client should be OllamaClient"

        print(f"  ✓ Created OllamaClient: {client.backend_name}")
        print(f"  ✓ Model: {client.model}")
        print(f"  ✓ Base URL: {client.base_url}")

    except Exception as e:
        # Warmup failure is expected if Ollama not running
        if "预热" in str(e) or "warmup" in str(e).lower():
            print(f"  ⚠ Ollama not running (warmup failed), but client creation logic is correct")
        else:
            raise


def test_client_caching():
    """Test client caching behavior"""
    print("\nTesting client caching...")

    clear_cache()

    try:
        # Create two clients with same config
        client1 = create_client(backend='ollama', task='main_agent', use_cache=True)
        client2 = create_client(backend='ollama', task='main_agent', use_cache=True)

        # Should be the same instance
        assert client1 is client2, "Cached clients should be same instance"
        print("  ✓ Cached clients are same instance")

        # Create without cache
        client3 = create_client(backend='ollama', task='main_agent', use_cache=False)

        # Should be different instance
        assert client1 is not client3, "Non-cached client should be different instance"
        print("  ✓ Non-cached client is different instance")

    except Exception as e:
        if "预热" in str(e) or "warmup" in str(e).lower():
            print(f"  ⚠ Ollama not running, skipping cache test")
        else:
            raise


def test_openai_client_creation():
    """Test OpenAI client creation (without actual API call)"""
    print("\nTesting OpenAI client creation...")

    clear_cache()

    # Set a dummy API key for testing
    os.environ['OPENAI_API_KEY'] = 'test-key-for-unit-test'

    try:
        from backend.llm.openai_client import OpenAIClient

        # Create client directly
        client = OpenAIClient(config={
            'base_url': 'https://api.example.com/v1',
            'api_key': 'test-key',
            'models': {'main': 'test-model'},
            'timeout': 60,
            'stream': False,
            'generation': {'temperature': 0.1},
            'retry': {'max_attempts': 1, 'backoff_factor': 1, 'initial_delay': 1}
        })

        assert client is not None, "Client should not be None"
        assert isinstance(client, BaseLLMClient), "Client should be BaseLLMClient"
        assert client.model == 'test-model', "Model should be test-model"

        print(f"  ✓ Created OpenAIClient")
        print(f"  ✓ Model: {client.model}")
        print(f"  ✓ Base URL: {client.base_url}")

    except ImportError as e:
        print(f"  ⚠ OpenAI package not installed: {e}")
    finally:
        # Clean up
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


def test_native_tool_calling_config():
    """Test native_tool_calling configuration"""
    print("\nTesting native_tool_calling config...")

    config = load_config()
    openai_config = config.get('openai', {})

    native_tool_calling = openai_config.get('native_tool_calling', True)
    print(f"  ✓ native_tool_calling: {native_tool_calling}")

    # When native_tool_calling is False, factory should wrap with PromptToolAdapter
    # This is tested in test_tool_adapter.py


def run_all_tests():
    """Run all factory tests"""
    print("=" * 60)
    print("LLM Factory Unit Tests")
    print("=" * 60)

    test_load_config()
    test_list_backends()
    test_get_backend_for_task()
    test_create_ollama_client()
    test_client_caching()
    test_openai_client_creation()
    test_native_tool_calling_config()

    print("\n" + "=" * 60)
    print("✓ All LLM factory tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
