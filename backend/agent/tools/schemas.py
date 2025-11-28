# -*- coding: utf-8 -*-
"""
Tool registration and schema generation for function calling

Uses dynamic tool discovery from backend/tools/xxx_tools/ directories.
All tools inheriting from BaseTool are automatically discovered and registered.
"""

from typing import Dict, Any, List, Optional
from .registry import ToolRegistry as DynamicToolRegistry


class ToolRegistry:
    """
    Registry for managing tools and their schemas.

    Wraps the dynamic registry for backward compatibility while
    providing auto-discovery of BaseTool classes.
    """

    def __init__(self, project_root: Optional[str] = None, **dependencies):
        """
        Initialize the tool registry with dynamic discovery.

        Args:
            project_root: Project root directory for tool execution
            **dependencies: Additional dependencies (e.g., agent instance)
        """
        self.project_root = project_root
        self.dependencies = dependencies
        self._dynamic_registry: Optional[DynamicToolRegistry] = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazily initialize the dynamic registry"""
        if not self._initialized and self.project_root:
            self._dynamic_registry = DynamicToolRegistry(
                project_root=self.project_root,
                **self.dependencies
            )
            self._initialized = True

    def initialize(self, project_root: str, **dependencies):
        """
        Initialize or reinitialize the registry with a project root.

        Args:
            project_root: Project root directory
            **dependencies: Additional dependencies
        """
        self.project_root = project_root
        self.dependencies.update(dependencies)
        self._dynamic_registry = DynamicToolRegistry(
            project_root=project_root,
            **self.dependencies
        )
        self._initialized = True

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in OpenAI format"""
        self._ensure_initialized()
        if self._dynamic_registry:
            return self._dynamic_registry.get_openai_schemas()
        return []

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        self._ensure_initialized()
        if not self._dynamic_registry:
            return {
                'success': False,
                'error': 'Registry not initialized'
            }
        return self._dynamic_registry.execute(tool_name, arguments)

    def has(self, tool_name: str) -> bool:
        """Check if a tool exists"""
        self._ensure_initialized()
        if self._dynamic_registry:
            return self._dynamic_registry.has(tool_name)
        return False

    def list_tools(self) -> List[str]:
        """List all available tool names"""
        self._ensure_initialized()
        if self._dynamic_registry:
            return self._dynamic_registry.list_tools()
        return []


# Global registry instance (lazy initialization)
registry = ToolRegistry()


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Get all registered tool schemas"""
    return registry.get_schemas()


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool by name"""
    return registry.execute(tool_name, arguments)


def initialize_tools(project_root: str, agent=None):
    """
    Initialize all available tools via dynamic discovery.

    Args:
        project_root: Project root directory
        agent: Optional agent instance for tools that need it
    """
    dependencies = {}
    if agent:
        dependencies['agent'] = agent

    registry.initialize(project_root, **dependencies)


# Backward compatibility aliases (deprecated, use initialize_tools instead)
def register_filesystem_tools(project_root: str):
    """Deprecated: Tools are now auto-discovered. Use initialize_tools()."""
    pass


def register_executor_tools(project_root: str):
    """Deprecated: Tools are now auto-discovered. Use initialize_tools()."""
    pass


def register_git_tools(project_root: str):
    """Deprecated: Tools are now auto-discovered. Use initialize_tools()."""
    pass


def register_analyzer_tools(project_root: str):
    """Deprecated: Tools are now auto-discovered. Use initialize_tools()."""
    pass


def register_agent_tools(agent):
    """Deprecated: Pass agent to initialize_tools() instead."""
    pass
