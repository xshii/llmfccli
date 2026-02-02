# -*- coding: utf-8 -*-
"""
Tool executor interface for decoupling AgentLoop from tool implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


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
        from .registry import ToolRegistry

        self.project_root = project_root
        self.confirmation = confirmation_manager

        # Initialize new ToolRegistry with auto-discovery
        self.registry = ToolRegistry(project_root=project_root, agent=agent)

        # Set registry on confirmation manager for tool instance lookup
        if self.confirmation:
            self.confirmation.set_tool_registry(self.registry)

        # Streaming output callbacks
        self._stdout_callback: Optional[Callable[[str], None]] = None
        self._stderr_callback: Optional[Callable[[str], None]] = None

    def set_streaming_callbacks(
        self,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None
    ):
        """
        设置流式输出回调

        Args:
            on_stdout: stdout 行回调
            on_stderr: stderr 行回调
        """
        self._stdout_callback = on_stdout
        self._stderr_callback = on_stderr

        # 为 bash_run 工具设置回调
        bash_tool = self.registry.get('bash_run')
        if bash_tool and hasattr(bash_tool, 'set_output_callbacks'):
            bash_tool.set_output_callbacks(on_stdout, on_stderr)

    def get_tool_schemas(self, filter_by_role: bool = True) -> List[Dict[str, Any]]:
        """
        Get all registered tool schemas, optionally filtered by current role

        Args:
            filter_by_role: Whether to filter tools by current role (default: True)

        Returns:
            List of tool schemas
        """
        schemas = self.registry.get_openai_schemas()

        if filter_by_role:
            try:
                from backend.roles import get_role_manager
                role_manager = get_role_manager()
                schemas = role_manager.filter_tools(schemas)
            except Exception:
                # 角色管理器不可用时，返回所有工具
                pass

        return schemas

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool via registry"""
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
        from .registry import ToolRegistry

        self.project_root = project_root
        # Recreate registry with new project root
        agent = self.registry.dependencies.get('agent')
        self.registry = ToolRegistry(project_root=project_root, agent=agent)

        # Update registry on confirmation manager
        if self.confirmation:
            self.confirmation.set_tool_registry(self.registry)


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
