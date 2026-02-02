# -*- coding: utf-8 -*-
"""
Pre-check modules

各检查模块:
- result: PreCheckResult 结果容器
- ssh_check: SSH 隧道检查
- ollama_check: Ollama 连接和模型检查
- process_check: 本地进程检查
- project_check: 项目结构检查
"""

from .result import PreCheckResult
from .ssh_check import check_ssh_tunnel
from .ollama_check import check_ollama_connection, check_ollama_model, test_ollama_hello, get_ollama_config
from .process_check import check_and_kill_local_ollama
from .project_check import check_project_structure

__all__ = [
    'PreCheckResult',
    'check_ssh_tunnel',
    'check_ollama_connection',
    'check_ollama_model',
    'test_ollama_hello',
    'get_ollama_config',
    'check_and_kill_local_ollama',
    'check_project_structure',
]
