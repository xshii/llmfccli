# -*- coding: utf-8 -*-
"""
Tool registration and schema generation for function calling
"""

from typing import Dict, Any, List, Callable, Optional
import json


class ToolRegistry:
    """Registry for managing tools and their schemas"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.implementations: Dict[str, Callable] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any],
                 implementation: Callable):
        """
        Register a tool with its schema and implementation
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            implementation: Python function to execute
        """
        self.tools[name] = {
            'type': 'function',
            'function': {
                'name': name,
                'description': description,
                'parameters': parameters
            }
        }
        self.implementations[name] = implementation
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in OpenAI format"""
        return list(self.tools.values())
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.implementations:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        func = self.implementations[tool_name]
        try:
            return func(**arguments)
        except Exception as e:
            return {
                'error': str(e),
                'tool': tool_name,
                'arguments': arguments
            }


# Global registry instance
registry = ToolRegistry()


def register_filesystem_tools(project_root: str):
    """Register filesystem tools"""
    from ..tools.filesystem import view_file, edit_file, create_file, grep_search, list_dir
    
    # view_file
    registry.register(
        name='view_file',
        description='Read file contents with optional line range',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'File path relative to project root or absolute'
                },
                'line_range': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'minItems': 2,
                    'maxItems': 2,
                    'description': 'Optional [start_line, end_line] (1-indexed, use -1 for end)'
                }
            },
            'required': ['path']
        },
        implementation=lambda path, line_range=None: view_file(
            path, tuple(line_range) if line_range else None, project_root
        )
    )
    
    # edit_file
    registry.register(
        name='edit_file',
        description='Edit file using str_replace (old_str must be unique)',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'File path'
                },
                'old_str': {
                    'type': 'string',
                    'description': 'String to replace (must appear exactly once)'
                },
                'new_str': {
                    'type': 'string',
                    'description': 'Replacement string'
                }
            },
            'required': ['path', 'old_str', 'new_str']
        },
        implementation=lambda path, old_str, new_str: edit_file(
            path, old_str, new_str, project_root
        )
    )
    
    # create_file
    registry.register(
        name='create_file',
        description='Create new file with content',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'File path'
                },
                'content': {
                    'type': 'string',
                    'description': 'File content'
                }
            },
            'required': ['path', 'content']
        },
        implementation=lambda path, content: create_file(
            path, content, project_root
        )
    )
    
    # grep_search
    registry.register(
        name='grep_search',
        description='Search for pattern in files (regex supported)',
        parameters={
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'Search pattern (regex)'
                },
                'scope': {
                    'type': 'string',
                    'description': 'Search scope directory (default: ".")'
                },
                'file_pattern': {
                    'type': 'string',
                    'description': 'Optional file pattern filter (e.g., "*.cpp")'
                }
            },
            'required': ['pattern']
        },
        implementation=lambda pattern, scope=".", file_pattern=None: grep_search(
            pattern, scope, project_root, file_pattern=file_pattern
        )
    )
    
    # list_dir
    registry.register(
        name='list_dir',
        description='List directory contents recursively',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Directory path (default: ".")'
                },
                'max_depth': {
                    'type': 'integer',
                    'description': 'Maximum depth to traverse (default: 3)'
                }
            },
            'required': []
        },
        implementation=lambda path=".", max_depth=3: list_dir(
            path, project_root, max_depth
        )
    )


def register_executor_tools(project_root: str):
    """Register executor tools (bash, cmake, etc.)"""
    # TODO: Implement when executor.py is ready
    pass


def register_analyzer_tools(project_root: str):
    """Register analyzer tools (tree-sitter, etc.)"""
    # TODO: Implement when analyzer.py is ready
    pass


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Get all registered tool schemas"""
    return registry.get_schemas()


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool by name"""
    return registry.execute(tool_name, arguments)


def initialize_tools(project_root: str):
    """Initialize all available tools"""
    register_filesystem_tools(project_root)
    # register_executor_tools(project_root)
    # register_analyzer_tools(project_root)
