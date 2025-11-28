# -*- coding: utf-8 -*-
"""
命令注册器 - 自动发现和懒加载命令
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from rich.console import Console

from .commands.base import Command


class CommandMetadata:
    """命令元数据"""

    def __init__(self, name: str, description: str, usage: str, category: str,
                 module_path: str, class_name: str):
        self.name = name
        self.description = description
        self.usage = usage
        self.category = category
        self.module_path = module_path
        self.class_name = class_name


class CommandRegistry:
    """命令注册器 - 自动发现和懒加载所有命令"""

    def __init__(self, console: Console, **dependencies):
        """初始化命令注册器

        Args:
            console: Rich Console 实例
            **dependencies: 命令可能需要的依赖（agent, remote_commands 等）
        """
        self.console = console
        self.dependencies = dependencies

        # 命令实例缓存（懒加载）
        self._command_instances: Dict[str, Command] = {}

        # 命令元数据（立即加载）
        self._command_metadata: Dict[str, CommandMetadata] = {}

        # 自动发现所有命令
        self._discover_commands()

    def _discover_commands(self):
        """扫描 commands/ 目录，自动发现所有命令类"""
        # 获取 commands 目录路径
        commands_dir = Path(__file__).parent / 'commands'

        if not commands_dir.exists():
            self.console.print(f"[yellow]警告: 命令目录不存在: {commands_dir}[/yellow]")
            return

        # 扫描所有 .py 文件（排除 __init__.py 和 base.py）
        for py_file in commands_dir.glob('*.py'):
            if py_file.name in ('__init__.py', 'base.py'):
                continue

            module_name = py_file.stem
            try:
                # 动态导入模块（只导入模块，不实例化类）
                module_path = f'backend.cli.commands.{module_name}'
                module = importlib.import_module(module_path)

                # 查找所有 Command 子类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 跳过 Command 基类本身
                    if obj is Command:
                        continue

                    # 检查是否是 Command 的子类
                    if issubclass(obj, Command) and obj.__module__ == module_path:
                        # 读取命令元数据（通过临时实例获取，但不保存实例）
                        try:
                            temp_instance = self._create_temp_instance_for_metadata(obj)
                            metadata = CommandMetadata(
                                name=temp_instance.name,
                                description=temp_instance.description,
                                usage=getattr(temp_instance, 'usage', ''),
                                category=getattr(temp_instance, 'category', 'other'),
                                module_path=module_path,
                                class_name=name
                            )
                            self._command_metadata[metadata.name] = metadata

                            # 临时实例用完即丢弃（真正的实例在首次使用时创建）
                            del temp_instance

                        except Exception as e:
                            self.console.print(
                                f"[yellow]警告: 无法读取命令元数据 {name}: {e}[/yellow]"
                            )

            except Exception as e:
                self.console.print(
                    f"[yellow]警告: 无法加载命令模块 {module_name}: {e}[/yellow]"
                )

    def _create_temp_instance_for_metadata(self, command_class: Type[Command]) -> Command:
        """创建临时实例用于读取元数据（使用 mock 依赖）"""
        sig = inspect.signature(command_class.__init__)

        # 准备构造参数（提供 mock 值）
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 提供基本参数
            if param_name == 'console':
                kwargs['console'] = self.console
            elif param_name == 'command_registry':
                kwargs['command_registry'] = None  # 元数据读取时不需要
            elif param.default is not inspect.Parameter.empty:
                # 有默认值的参数可以跳过
                continue
            else:
                # 其他参数提供 None（仅用于元数据读取）
                kwargs[param_name] = None

        return command_class(**kwargs)

    def _create_command_instance(self, command_class: Type[Command]) -> Command:
        """根据命令类创建实例，自动注入依赖"""
        # 获取构造函数签名
        sig = inspect.signature(command_class.__init__)

        # 准备构造参数
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 尝试从依赖中匹配参数
            if param_name == 'console':
                kwargs['console'] = self.console
            elif param_name == 'command_registry':
                # 特殊处理：HelpCommand 需要访问 registry 本身
                kwargs['command_registry'] = self
            elif param_name in self.dependencies:
                kwargs[param_name] = self.dependencies[param_name]
            elif param.default is not inspect.Parameter.empty:
                # 有默认值的参数可以跳过
                continue
            else:
                # 必需参数但没有提供，记录警告
                self.console.print(
                    f"[yellow]警告: 命令 {command_class.__name__} 缺少必需参数 {param_name}[/yellow]"
                )

        return command_class(**kwargs)

    def get(self, name: str) -> Optional[Command]:
        """获取命令实例（懒加载）

        Args:
            name: 命令名称

        Returns:
            命令实例，如果不存在返回 None
        """
        # 如果已经实例化，直接返回
        if name in self._command_instances:
            return self._command_instances[name]

        # 检查元数据中是否有此命令
        if name not in self._command_metadata:
            return None

        # 懒加载：首次使用时才实例化
        metadata = self._command_metadata[name]
        try:
            # 导入模块
            module = importlib.import_module(metadata.module_path)

            # 获取类
            command_class = getattr(module, metadata.class_name)

            # 创建实例
            instance = self._create_command_instance(command_class)

            # 缓存实例
            self._command_instances[name] = instance

            return instance

        except Exception as e:
            self.console.print(f"[red]错误: 无法加载命令 {name}: {e}[/red]")
            return None

    def has(self, name: str) -> bool:
        """检查命令是否存在"""
        return name in self._command_metadata

    def get_all_metadata(self) -> Dict[str, CommandMetadata]:
        """获取所有命令的元数据（用于生成帮助等）"""
        return self._command_metadata.copy()

    def get_commands_by_category(self) -> Dict[str, List[CommandMetadata]]:
        """按类别分组获取命令元数据"""
        categories: Dict[str, List[CommandMetadata]] = {}

        for metadata in self._command_metadata.values():
            category = metadata.category
            if category not in categories:
                categories[category] = []
            categories[category].append(metadata)

        return categories

    def list_commands(self) -> List[str]:
        """列出所有可用命令名称"""
        return list(self._command_metadata.keys())
