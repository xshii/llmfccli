# -*- coding: utf-8 -*-
"""
Tool executor interface for decoupling AgentLoop from tool implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable


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

    def _tool_supports_confirmation(self, tool_name: str) -> bool:
        """
        检查工具是否支持 confirm 参数（通用方法，无硬编码）

        通过检查工具的 Pydantic model 来判断是否支持 confirm 参数

        Args:
            tool_name: 工具名称

        Returns:
            True if tool accepts 'confirm' parameter
        """
        try:
            # 直接从工具类读取 Pydantic model（无需完整实例化）
            if tool_name not in self.registry._tool_metadata:
                return False

            metadata = self.registry._tool_metadata[tool_name]

            # 导入工具类
            import importlib
            module = importlib.import_module(metadata.module_path)
            tool_class = getattr(module, metadata.class_name)

            # 通过临时实例获取 parameters_model
            temp_instance = self.registry._create_temp_instance_for_metadata(tool_class)
            params_model = temp_instance.parameters_model

            # 检查 Pydantic model 的字段
            if hasattr(params_model, 'model_fields'):
                # Pydantic v2
                has_confirm = 'confirm' in params_model.model_fields
            elif hasattr(params_model, '__fields__'):
                # Pydantic v1
                has_confirm = 'confirm' in params_model.__fields__
            else:
                has_confirm = False

            # 清理临时实例
            del temp_instance

            return has_confirm
        except Exception as e:
            # 静默失败
            return False

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool via registry with smart confirmation handling

        通用逻辑（无硬编码工具名）：
        1. 检查工具是否支持 confirm 参数（通过 schema）
        2. 检查用户是否设置了 "always allow"
        3. 如果两者都满足 → 注入 confirm=False
        """
        # 通用确认处理（适用于所有支持 confirm 的工具）
        if self.confirmation:
            # 检查工具是否支持 confirm 参数（通过 schema，不硬编码）
            if self._tool_supports_confirmation(tool_name):
                # 检查用户是否设置了 "always allow"
                if tool_name in self.confirmation.allowed_tool_calls:
                    # 用户信任这个工具，跳过工具级别的确认
                    arguments = dict(arguments)  # Copy to avoid mutation
                    arguments['confirm'] = False
                # 否则使用工具的默认值（通常是 confirm=True）

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
