# -*- coding: utf-8 -*-
"""
工具注册器 - 自动发现和懒加载
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Type

from backend.tools.base import BaseTool


class ToolMetadata:
    """工具元数据"""

    def __init__(self, name: str, description: str, category: str,
                 module_path: str, class_name: str):
        self.name = name
        self.description = description
        self.category = category
        self.module_path = module_path
        self.class_name = class_name


class ToolRegistry:
    """工具注册器 - 自动发现和懒加载所有工具"""

    def __init__(self, project_root: Optional[str] = None, **dependencies):
        """
        初始化工具注册器

        Args:
            project_root: 项目根目录
            **dependencies: 工具可能需要的依赖（agent 等）
        """
        self.project_root = project_root
        self.dependencies = dependencies

        # 工具实例缓存（懒加载）
        self._tool_instances: Dict[str, BaseTool] = {}

        # 工具元数据（立即加载）
        self._tool_metadata: Dict[str, ToolMetadata] = {}

        # 自动发现所有工具
        self._discover_tools()

    def _discover_tools(self):
        """扫描 backend/tools/ 目录，自动发现所有工具类"""
        # 获取 backend/tools 目录路径
        # 当前文件: backend/agent/tools/registry.py
        # 目标目录: backend/tools/
        tools_dir = Path(__file__).parent.parent.parent / 'tools'

        if not tools_dir.exists():
            print(f"警告: 工具目录不存在: {tools_dir}")
            return

        # 扫描所有子目录（filesystem, executor, git, agent）
        for category_dir in tools_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # 跳过特殊目录
            if category_dir.name.startswith('_') or category_dir.name == '__pycache__':
                continue

            # 扫描该类别下的所有 .py 文件
            for py_file in category_dir.glob('*.py'):
                if py_file.name in ('__init__.py', 'base.py'):
                    continue

                module_name = py_file.stem
                try:
                    # 动态导入模块
                    module_path = f'backend.tools.{category_dir.name}.{module_name}'
                    module = importlib.import_module(module_path)

                    # 查找所有 BaseTool 子类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # 跳过 BaseTool 基类本身
                        if obj is BaseTool:
                            continue

                        # 检查是否是 BaseTool 的子类
                        if issubclass(obj, BaseTool) and obj.__module__ == module_path:
                            # 读取工具元数据（通过临时实例获取）
                            try:
                                temp_instance = self._create_temp_instance_for_metadata(obj)
                                metadata = ToolMetadata(
                                    name=temp_instance.name,
                                    description=temp_instance.description,
                                    category=getattr(temp_instance, 'category', 'other'),
                                    module_path=module_path,
                                    class_name=name
                                )
                                self._tool_metadata[metadata.name] = metadata

                                # 临时实例用完即丢弃
                                del temp_instance

                            except Exception as e:
                                print(f"警告: 无法读取工具元数据 {name}: {e}")

                except Exception as e:
                    print(f"警告: 无法加载工具模块 {module_name}: {e}")

    def _create_temp_instance_for_metadata(self, tool_class: Type[BaseTool]) -> BaseTool:
        """创建临时实例用于读取元数据（使用 mock 依赖）"""
        sig = inspect.signature(tool_class.__init__)

        # 准备构造参数（提供 mock 值）
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 跳过 *args 和 **kwargs 类型参数
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # 提供基本参数
            if param_name == 'project_root':
                kwargs['project_root'] = None  # 元数据读取时不需要
            elif param.default is not inspect.Parameter.empty:
                # 有默认值的参数可以跳过
                continue
            else:
                # 其他参数提供 None（仅用于元数据读取）
                kwargs[param_name] = None

        return tool_class(**kwargs)

    def _create_tool_instance(self, tool_class: Type[BaseTool]) -> BaseTool:
        """根据工具类创建实例，自动注入依赖"""
        # 获取构造函数签名
        sig = inspect.signature(tool_class.__init__)

        # 准备构造参数
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 跳过 *args 和 **kwargs 类型参数
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # 尝试从依赖中匹配参数
            if param_name == 'project_root':
                kwargs['project_root'] = self.project_root
            elif param_name in self.dependencies:
                kwargs[param_name] = self.dependencies[param_name]
            elif param.default is not inspect.Parameter.empty:
                # 有默认值的参数可以跳过
                continue
            else:
                # 必需参数但没有提供，记录警告
                print(f"警告: 工具 {tool_class.__name__} 缺少必需参数 {param_name}")

        return tool_class(**kwargs)

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具实例（懒加载）

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在返回 None
        """
        # 如果已经实例化，直接返回
        if name in self._tool_instances:
            return self._tool_instances[name]

        # 检查元数据中是否有此工具
        if name not in self._tool_metadata:
            return None

        # 懒加载：首次使用时才实例化
        metadata = self._tool_metadata[name]
        try:
            # 导入模块
            module = importlib.import_module(metadata.module_path)

            # 获取类
            tool_class = getattr(module, metadata.class_name)

            # 创建实例
            instance = self._create_tool_instance(tool_class)

            # 缓存实例
            self._tool_instances[name] = instance

            return instance

        except Exception as e:
            print(f"错误: 无法加载工具 {name}: {e}")
            return None

    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tool_metadata

    def get_all_metadata(self) -> Dict[str, ToolMetadata]:
        """获取所有工具的元数据"""
        return self._tool_metadata.copy()

    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具的完整元数据（包括 schema）

        使用临时实例读取 schema（无需完整依赖）

        Args:
            tool_name: 工具名称

        Returns:
            包含 name, description, category, schema 的字典
            如果工具不存在返回 None
        """
        if tool_name not in self._tool_metadata:
            return None

        metadata = self._tool_metadata[tool_name]

        try:
            # 导入模块
            module = importlib.import_module(metadata.module_path)
            tool_class = getattr(module, metadata.class_name)

            # 创建临时实例用于读取 schema（使用 mock 依赖）
            temp_instance = self._create_temp_instance_for_metadata(tool_class)

            # 获取 OpenAI schema
            schema = temp_instance.get_openai_schema()

            # 清理临时实例
            del temp_instance

            return {
                'name': metadata.name,
                'description': metadata.description,
                'category': metadata.category,
                'schema': schema
            }
        except Exception as e:
            # 静默失败，返回 None
            return None

    def get_tools_by_category(self) -> Dict[str, List[ToolMetadata]]:
        """按类别分组获取工具元数据"""
        categories: Dict[str, List[ToolMetadata]] = {}

        for metadata in self._tool_metadata.values():
            category = metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(metadata)

        return categories

    def list_tools(self) -> List[str]:
        """列出所有可用工具名称"""
        return list(self._tool_metadata.keys())

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 OpenAI function calling schemas"""
        schemas = []

        # 为每个工具生成 schema（需要临时实例）
        for tool_name in self._tool_metadata.keys():
            tool = self.get(tool_name)
            if tool:
                try:
                    schema = tool.get_openai_schema()
                    schemas.append(schema)
                except Exception as e:
                    print(f"警告: 无法生成工具 {tool_name} 的 schema: {e}")

        return schemas

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get(tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'Unknown tool: {tool_name}'
            }

        return tool.validate_and_execute(arguments)
