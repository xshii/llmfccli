# -*- coding: utf-8 -*-
"""
Tool executor interface for decoupling AgentLoop from tool implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ToolExecutor(ABC):
    """Abstract interface for tool execution"""

    @abstractmethod
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all available tool schemas in OpenAI function calling format

        Returns:
            List of tool schema dicts
        """
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name with given arguments

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool_name is not registered
        """
        pass

    @abstractmethod
    def get_tool_names(self) -> List[str]:
        """
        Get list of all registered tool names

        Returns:
            List of tool names
        """
        pass

    def is_file_operation(self, tool_name: str) -> bool:
        """
        Check if a tool is a file operation (for tracking active files)

        Args:
            tool_name: Tool name to check

        Returns:
            True if tool operates on files
        """
        # Default implementation - can be overridden
        return tool_name in ['view_file', 'edit_file', 'create_file']


class RegistryToolExecutor(ToolExecutor):
    """Tool executor backed by ToolRegistry"""

    def __init__(self, project_root: str):
        """
        Initialize tool executor with project root

        Args:
            project_root: Project root directory path
        """
        from .tools import initialize_tools, registry

        self.project_root = project_root
        self.registry = registry

        # Initialize tools
        initialize_tools(project_root)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all registered tool schemas"""
        return self.registry.get_schemas()

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool via registry"""
        return self.registry.execute(tool_name, arguments)

    def get_tool_names(self) -> List[str]:
        """Get all registered tool names"""
        return list(self.registry.implementations.keys())

    def reinitialize(self, project_root: str):
        """
        Reinitialize tools with new project root

        Args:
            project_root: New project root directory
        """
        from .tools import initialize_tools

        self.project_root = project_root
        initialize_tools(project_root)


class MockToolExecutor(ToolExecutor):
    """Mock tool executor for testing"""

    def __init__(self):
        """Initialize mock executor"""
        self.tools: Dict[str, Dict] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.mock_results: Dict[str, Any] = {}

    def register_mock_tool(self, name: str, schema: Dict[str, Any],
                          result: Any = None):
        """
        Register a mock tool

        Args:
            name: Tool name
            schema: Tool schema dict
            result: Mock result to return (optional)
        """
        self.tools[name] = schema
        if result is not None:
            self.mock_results[name] = result

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all mock tool schemas"""
        return list(self.tools.values())

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute mock tool and record call"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Record call
        self.call_history.append({
            'tool': tool_name,
            'arguments': arguments
        })

        # Return mock result or default
        return self.mock_results.get(tool_name, {'status': 'ok'})

    def get_tool_names(self) -> List[str]:
        """Get all mock tool names"""
        return list(self.tools.keys())

    def clear_history(self):
        """Clear call history"""
        self.call_history = []
