# -*- coding: utf-8 -*-
"""
Agent tools module - dynamic tool discovery, execution, and confirmation
"""

# Tool registry (dynamic discovery)
# Tool confirmation
from .confirmation import ConfirmAction, ConfirmResult, ToolConfirmation

# Tool execution
from .executor import MockToolExecutor, RegistryToolExecutor, ToolExecutor
from .registry import ToolRegistry

# Backward compatible API from schemas.py
from .schemas import (
    execute_tool,
    get_tool_schemas,
    initialize_tools,
    registry,
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
