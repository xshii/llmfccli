# -*- coding: utf-8 -*-
"""
Ollama connection and model checks
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import yaml

from .result import PreCheckResult
from backend.llm.config import get_ssh_host


def get_ollama_config() -> Tuple[str, str]:
    """
    Get model name and base_url from llm.yaml config

    Returns:
        Tuple of (model_name, base_url)

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If required config is missing
    """
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "llm.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    ollama_config = config.get('ollama', {})
    model = ollama_config.get('model')
    base_url = ollama_config.get('base_url')

    if not model:
        raise ValueError("配置缺少 ollama.model")
    if not base_url:
        raise ValueError("配置缺少 ollama.base_url")

    return model, base_url


def check_ollama_connection(base_url: str = "http://localhost:11434") -> PreCheckResult:
    """
    Check Ollama service connection

    Args:
        base_url: Ollama base URL

    Returns:
        PreCheckResult
    """
    try:
        result = subprocess.run(
            ['curl', '-s', '--connect-timeout', '3', f'{base_url}/api/tags'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                models = data.get('models', [])
                model_names = [m.get('name', 'unknown') for m in models]

                return PreCheckResult(
                    "Ollama Connection",
                    True,
                    f"Connected to Ollama ({len(models)} models available)",
                    {"url": base_url, "models": model_names}
                )
            except json.JSONDecodeError:
                return PreCheckResult(
                    "Ollama Connection",
                    False,
                    f"Connected but invalid response: {result.stdout[:100]}",
                    {"url": base_url}
                )
        else:
            ssh_host = get_ssh_host()
            if ssh_host:
                msg = f"无法连接 Ollama: {base_url}（检查 SSH 隧道 {ssh_host} 是否已启动）"
            else:
                msg = f"无法连接 Ollama: {base_url}（服务可能未启动）"
            return PreCheckResult(
                "Ollama Connection",
                False,
                msg,
                {"url": base_url, "stderr": result.stderr}
            )
    except subprocess.TimeoutExpired:
        return PreCheckResult(
            "Ollama Connection",
            False,
            f"Connection timeout to {base_url}",
            {"url": base_url}
        )
    except Exception as e:
        return PreCheckResult(
            "Ollama Connection",
            False,
            f"Connection check failed: {e}",
            {"url": base_url}
        )


def check_ollama_model(model_name: Optional[str] = None,
                       base_url: Optional[str] = None) -> PreCheckResult:
    """
    Check if specific Ollama model is available

    Args:
        model_name: Model name to check (default: from config)
        base_url: Ollama base URL (default: from config)

    Returns:
        PreCheckResult
    """
    try:
        if model_name is None or base_url is None:
            cfg_model, cfg_url = get_ollama_config()
            model_name = model_name or cfg_model
            base_url = base_url or cfg_url
    except (FileNotFoundError, ValueError) as e:
        return PreCheckResult("Ollama Model", False, str(e), {})

    try:
        result = subprocess.run(
            ['curl', '-s', '--connect-timeout', '3', f'{base_url}/api/tags'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            models = data.get('models', [])
            model_names = [m.get('name', '') for m in models]

            # Check if model exists (exact match or prefix match)
            model_exists = any(
                name == model_name or name.startswith(model_name.split(':')[0])
                for name in model_names
            )

            if model_exists:
                return PreCheckResult(
                    "Ollama Model",
                    True,
                    f"Model '{model_name}' is available",
                    {"model": model_name, "all_models": model_names}
                )
            else:
                return PreCheckResult(
                    "Ollama Model",
                    False,
                    f"Model '{model_name}' not found. Available: {', '.join(model_names)}",
                    {"model": model_name, "all_models": model_names}
                )
        else:
            return PreCheckResult(
                "Ollama Model",
                False,
                "Cannot retrieve model list from Ollama",
                {"model": model_name}
            )
    except Exception as e:
        return PreCheckResult(
            "Ollama Model",
            False,
            f"Model check failed: {e}",
            {"model": model_name}
        )


def test_ollama_hello(model_name: Optional[str] = None,
                      base_url: Optional[str] = None) -> PreCheckResult:
    """
    Test Ollama with a simple 'hi' request

    Args:
        model_name: Model to test (default: from config)
        base_url: Ollama base URL (default: from config)

    Returns:
        PreCheckResult
    """
    try:
        if model_name is None or base_url is None:
            cfg_model, cfg_url = get_ollama_config()
            model_name = model_name or cfg_model
            base_url = base_url or cfg_url
    except (FileNotFoundError, ValueError) as e:
        return PreCheckResult("Ollama Hello Test", False, str(e), {})

    try:
        request_data = {
            "model": model_name,
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(request_data, f)
            temp_file = f.name

        result = subprocess.run(
            ['curl', '-s', '--noproxy', 'localhost', '--connect-timeout', '5',
             f'{base_url}/api/chat', '-d', f'@{temp_file}'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up
        try:
            os.unlink(temp_file)
        except:
            pass

        if result.returncode == 0 and result.stdout:
            try:
                response = json.loads(result.stdout)
                content = response.get('message', {}).get('content', '')

                if content:
                    return PreCheckResult(
                        "Ollama Hello Test",
                        True,
                        f"Model responded: '{content[:50]}{'...' if len(content) > 50 else ''}'",
                        {"model": model_name, "response_length": len(content)}
                    )
                else:
                    return PreCheckResult(
                        "Ollama Hello Test",
                        False,
                        "Model returned empty response",
                        {"model": model_name, "response": response}
                    )
            except json.JSONDecodeError as e:
                return PreCheckResult(
                    "Ollama Hello Test",
                    False,
                    f"Invalid JSON response: {e}",
                    {"model": model_name}
                )
        else:
            return PreCheckResult(
                "Ollama Hello Test",
                False,
                f"Request failed: {result.stderr or 'empty response'}",
                {"model": model_name}
            )
    except subprocess.TimeoutExpired:
        return PreCheckResult(
            "Ollama Hello Test",
            False,
            "Request timeout (>30s)",
            {"model": model_name}
        )
    except Exception as e:
        return PreCheckResult(
            "Ollama Hello Test",
            False,
            f"Test failed: {e}",
            {"model": model_name}
        )
