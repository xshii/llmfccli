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

    def __init__(self, project_root: str, confirmation_manager: Optional[Any] = None, agent: Optional[Any] = None):
        """
        Initialize tool executor with project root

        Args:
            project_root: Project root directory path
            confirmation_manager: ToolConfirmation instance (optional)
            agent: Agent instance (for agent-specific tools)
        """
        from .tool_registry import ToolRegistry

        self.project_root = project_root
        self.confirmation = confirmation_manager

        # Initialize new ToolRegistry with auto-discovery
        self.registry = ToolRegistry(project_root=project_root, agent=agent)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all registered tool schemas"""
        return self.registry.get_openai_schemas()

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool via registry with smart confirmation handling

        For edit_file:
        - If user set "always allow" → confirm=False (skip tool-level confirmation)
        - Otherwise → confirm=True (show diff preview)
        """
        # Smart handling for edit_file
        if tool_name == 'edit_file' and self.confirmation:
            # Check if user has set "always allow" for edit_file
            # (tool signature is just the tool name for file operations)
            if tool_name in self.confirmation.allowed_tool_calls:
                # User trusts this tool, skip tool-level confirmation
                arguments = dict(arguments)  # Copy to avoid mutation
                arguments['confirm'] = False
            # If not in allowed_tool_calls, use default (confirm=True)
            # This shows diff preview for user review

        return self.registry.execute(tool_name, arguments)

    def get_tool_names(self) -> List[str]:
        """Get all registered tool names"""
        return self.registry.list_tools()

    def reinitialize(self, project_root: str):
        """
        Reinitialize tools with new project root

        Args:
            project_root: New project root directory
        """
        from .tool_registry import ToolRegistry

        self.project_root = project_root
        # Recreate registry with new project root
        agent = self.registry.dependencies.get('agent')
        self.registry = ToolRegistry(project_root=project_root, agent=agent)


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
