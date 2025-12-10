# -*- coding: utf-8 -*-
"""
Backward compatibility layer for LLM clients

This module maintains backward compatibility with existing code that imports
from backend.llm.client. New code should use the factory function:

    from backend.llm import create_client
    client = create_client()  # Uses default backend from config

Or import specific clients:

    from backend.llm import OllamaClient, OpenAIClient
"""

# Re-export OllamaClient for backward compatibility
from .ollama import OllamaClient

# Re-export utility function
from .ollama import OllamaClient as _OllamaClient


def create_tool_definition(name: str, description: str,
                          parameters: dict) -> dict:
    """
    Create tool definition in OpenAI function calling format

    Args:
        name: Tool name
        description: Tool description
        parameters: JSON schema for parameters

    Returns:
        Tool definition dict
    """
    return {
        'type': 'function',
        'function': {
            'name': name,
            'description': description,
            'parameters': parameters
        }
    }


# Example tool definitions (kept for reference)
EXAMPLE_TOOLS = [
    create_tool_definition(
        name='view_file',
        description='Read file contents with optional line range',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'File path relative to project root'
                },
                'line_range': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': 'Optional [start, end] line numbers'
                }
            },
            'required': ['path']
        }
    ),
    create_tool_definition(
        name='grep_search',
        description='Search for pattern in files',
        parameters={
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'Search pattern (regex supported)'
                },
                'scope': {
                    'type': 'string',
                    'description': 'Search scope directory'
                }
            },
            'required': ['pattern']
        }
    )
]

__all__ = ['OllamaClient', 'create_tool_definition', 'EXAMPLE_TOOLS']
