# -*- coding: utf-8 -*-
"""
Agent tools module - dynamic tool discovery, execution, and confirmation
"""

# Tool registry (dynamic discovery)
from .registry import ToolRegistry

# Tool execution
from .executor import ToolExecutor, RegistryToolExecutor, MockToolExecutor

# Tool confirmation
from .confirmation import ConfirmAction, ConfirmResult, ToolConfirmation

# Backward compatible API from schemas.py
from .schemas import (
    registry,
    get_tool_schemas,
    execute_tool,
    initialize_tools,
)

__all__ = [
    # Core registry
    'ToolRegistry',
    # Executor
    'ToolExecutor',
    'RegistryToolExecutor',
    'MockToolExecutor',
    # Confirmation
    'ConfirmAction',
    'ConfirmResult',
    'ToolConfirmation',
    # Backward compatible API
    'registry',
    'get_tool_schemas',
    'execute_tool',
    'initialize_tools',
]
