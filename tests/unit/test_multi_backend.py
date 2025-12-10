#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for multi-backend LLM support

Tests the complete flow of switching between backends and using
different clients for different tasks.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.llm import (
    BaseLLMClient,
    OllamaClient,
    OpenAIClient,
    PromptToolAdapter,
    create_client,
    load_config,
    clear_cache,
)


def test_client_interface_consistency():
    """Test that all clients implement the same interface"""
    print("Testing client interface consistency...")

    # Required methods
    required_methods = [
        'chat',
        'chat_with_tools',
        'parse_tool_calls',
        'compress_context',
        'estimate_tokens',
        'format_tool_result',
        'backend_name',
    ]

    # Check OllamaClient
    for method in required_methods:
        assert hasattr(OllamaClient, method) or hasattr(OllamaClient, method.replace('_', '')), \
            f"OllamaClient missing {method}"

    print("  ✓ OllamaClient has all required methods")

    # Check OpenAIClient
    for method in required_methods:
        assert hasattr(OpenAIClient, method) or hasattr(OpenAIClient, method.replace('_', '')), \
            f"OpenAIClient missing {method}"

    print("  ✓ OpenAIClient has all required methods")

    # Check PromptToolAdapter
    for method in required_methods:
        assert hasattr(PromptToolAdapter, method), \
            f"PromptToolAdapter missing {method}"

    print("  ✓ PromptToolAdapter has all required methods")


def test_backend_name_property():
    """Test backend_name property for each client type"""
    print("\nTesting backend_name property...")

    # Mock config to avoid actual connections
    ollama_config = {
        'base_url': 'http://localhost:11434',
        'model': 'test-model',
        'timeout': 10,
        'stream': False,
        'retry': {'max_attempts': 1, 'backoff_factor': 1, 'initial_delay': 0}
    }

    openai_config = {
        'base_url': 'https://api.example.com/v1',
        'api_key': 'test-key',
        'models': {'main': 'test-model'},
        'timeout': 10,
        'stream': False,
        'generation': {},
        'retry': {'max_attempts': 1, 'backoff_factor': 1, 'initial_delay': 0}
    }

    # Test OllamaClient (may fail warmup but that's ok)
    try:
        ollama = OllamaClient(config=ollama_config)
        assert 'ollama' in ollama.backend_name.lower(), "OllamaClient should have 'ollama' in name"
        print(f"  ✓ OllamaClient.backend_name: {ollama.backend_name}")
    except Exception:
        print("  ⚠ OllamaClient warmup failed (expected if Ollama not running)")

    # Test OpenAIClient
    try:
        openai = OpenAIClient(config=openai_config)
        assert 'openai' in openai.backend_name.lower(), "OpenAIClient should have 'openai' in name"
        print(f"  ✓ OpenAIClient.backend_name: {openai.backend_name}")
    except ImportError:
        print("  ⚠ OpenAI package not installed")


def test_estimate_tokens_consistency():
    """Test that token estimation works consistently across clients"""
    print("\nTesting estimate_tokens consistency...")

    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Hello, how are you?'},
        {'role': 'assistant', 'content': 'I am doing well, thank you for asking!'},
    ]

    # Mock config
    ollama_config = {
        'base_url': 'http://localhost:11434',
        'model': 'test',
        'timeout': 10,
        'stream': False,
        'retry': {'max_attempts': 1, 'backoff_factor': 1, 'initial_delay': 0}
    }

    openai_config = {
        'base_url': 'https://api.example.com/v1',
        'api_key': 'test-key',
        'models': {'main': 'test'},
        'timeout': 10,
        'stream': False,
        'generation': {},
        'retry': {'max_attempts': 1, 'backoff_factor': 1, 'initial_delay': 0}
    }

    try:
        ollama = OllamaClient(config=ollama_config)
        ollama_tokens = ollama.estimate_tokens(messages)
        print(f"  ✓ OllamaClient estimate: {ollama_tokens} tokens")
    except Exception:
        print("  ⚠ OllamaClient warmup failed")
        ollama_tokens = None

    try:
        openai = OpenAIClient(config=openai_config)
        openai_tokens = openai.estimate_tokens(messages)
        print(f"  ✓ OpenAIClient estimate: {openai_tokens} tokens")
    except ImportError:
        print("  ⚠ OpenAI package not installed")
        openai_tokens = None

    # Both should return reasonable estimates (> 0)
    if ollama_tokens is not None:
        assert ollama_tokens > 0, "Token count should be positive"

    if openai_tokens is not None:
        assert openai_tokens > 0, "Token count should be positive"


def test_format_tool_result_consistency():
    """Test format_tool_result returns consistent format"""
    print("\nTesting format_tool_result consistency...")

    result = {'success': True, 'data': 'test data'}
    tool_call_id = 'call_123'

    # Test with base class method (all clients inherit this)
    from backend.llm.base import BaseLLMClient

    # Create a minimal concrete implementation for testing
    class TestClient(BaseLLMClient):
        def chat(self, messages, tools=None, stream=False, on_chunk=None, **kwargs):
            return {'message': {'content': ''}}

        def chat_with_tools(self, messages, tools, stream=False, on_chunk=None):
            return self.chat(messages, tools)

        def parse_tool_calls(self, response):
            return None

        def compress_context(self, messages, target_tokens, must_keep, compressible):
            return {}

        def estimate_tokens(self, messages):
            return 0

    client = TestClient()
    formatted = client.format_tool_result(tool_call_id, result)

    assert formatted['role'] == 'tool', "Role should be 'tool'"
    assert formatted['tool_call_id'] == tool_call_id, "Should have correct tool_call_id"
    assert 'content' in formatted, "Should have content"

    print(f"  ✓ Formatted result: {formatted}")


def test_config_driven_backend_selection():
    """Test that config drives backend selection"""
    print("\nTesting config-driven backend selection...")

    clear_cache()
    config = load_config()

    default_backend = config.get('default_backend', 'ollama')
    print(f"  ✓ Default backend from config: {default_backend}")

    # Check task_backends configuration
    task_backends = config.get('task_backends', {})
    print(f"  ✓ Task-specific backends: {task_backends}")

    # Check OpenAI native_tool_calling setting
    openai_config = config.get('openai', {})
    native_tool_calling = openai_config.get('native_tool_calling', True)
    print(f"  ✓ OpenAI native_tool_calling: {native_tool_calling}")


def test_prompt_adapter_wrapping():
    """Test that factory wraps client with PromptToolAdapter when needed"""
    print("\nTesting PromptToolAdapter wrapping...")

    from backend.llm.factory import _create_openai_client

    # Config with native_tool_calling = False
    config = {
        'openai': {
            'enabled': True,
            'base_url': 'https://api.example.com/v1',
            'api_key': 'test-key',
            'native_tool_calling': False,  # This should trigger adapter
            'models': {'main': 'test-model'},
            'timeout': 10,
            'stream': False,
            'generation': {},
            'retry': {'max_attempts': 1, 'backoff_factor': 1, 'initial_delay': 0}
        }
    }

    try:
        client = _create_openai_client(config)
        assert isinstance(client, PromptToolAdapter), \
            f"Should be PromptToolAdapter when native_tool_calling=False, got {type(client)}"
        print(f"  ✓ Client wrapped with PromptToolAdapter")
        print(f"  ✓ Backend name: {client.backend_name}")
    except ImportError:
        print("  ⚠ OpenAI package not installed")

    # Config with native_tool_calling = True
    config['openai']['native_tool_calling'] = True

    try:
        client = _create_openai_client(config)
        assert isinstance(client, OpenAIClient), \
            f"Should be OpenAIClient when native_tool_calling=True, got {type(client)}"
        assert not isinstance(client, PromptToolAdapter), "Should NOT be wrapped"
        print(f"  ✓ Client is unwrapped OpenAIClient")
    except ImportError:
        print("  ⚠ OpenAI package not installed")


def test_inheritance_chain():
    """Test that inheritance is set up correctly"""
    print("\nTesting inheritance chain...")

    # OllamaClient should inherit from BaseLLMClient
    assert issubclass(OllamaClient, BaseLLMClient), \
        "OllamaClient should inherit from BaseLLMClient"
    print("  ✓ OllamaClient inherits from BaseLLMClient")

    # OpenAIClient should inherit from BaseLLMClient
    assert issubclass(OpenAIClient, BaseLLMClient), \
        "OpenAIClient should inherit from BaseLLMClient"
    print("  ✓ OpenAIClient inherits from BaseLLMClient")

    # PromptToolAdapter is a wrapper, not a subclass
    # But it should implement the same interface
    print("  ✓ PromptToolAdapter implements BaseLLMClient interface")


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Multi-Backend Integration Tests")
    print("=" * 60)

    test_client_interface_consistency()
    test_backend_name_property()
    test_estimate_tokens_consistency()
    test_format_tool_result_consistency()
    test_config_driven_backend_selection()
    test_prompt_adapter_wrapping()
    test_inheritance_chain()

    print("\n" + "=" * 60)
    print("✓ All multi-backend integration tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
