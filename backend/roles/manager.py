# -*- coding: utf-8 -*-
"""
角色管理器 - 支持角色切换和配置管理

提供以下功能：
1. 加载角色配置
2. 切换当前角色
3. 获取角色的模型配置
4. 过滤角色可用的工具
5. 创建和管理角色专用模型
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import yaml


@dataclass
class Role:
    """角色定义"""
    id: str                          # 角色 ID（配置文件中的 key）
    name: str                        # 角色名称（中文）
    name_en: str                     # 角色名称（英文）
    description: str                 # 角色描述
    icon: str                        # 角色图标（emoji）
    model: str                       # 使用的模型（角色专用模型名称）
    tool_categories: List[str]       # 启用的工具类别
    base_model: str = "qwen3:latest"  # 基础模型
    modelfile: str = ""               # Modelfile 路径
    included_tools: List[str] = field(default_factory=list)  # 额外包含的工具（跨类别复用）
    excluded_tools: List[str] = field(default_factory=list)  # 排除的工具


class RoleManager:
    """角色管理器 - 单例模式"""

    _instance: Optional["RoleManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化角色管理器

        Args:
            config_path: 角色配置文件路径（默认为 config/roles.yaml）
        """
        if RoleManager._initialized:
            return

        self._config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._roles: Dict[str, Role] = {}
        self._current_role_id: str = "programmer"  # 默认角色
        self._callbacks: List[callable] = []  # 角色切换回调
        self._project_root = str(Path(__file__).parent.parent.parent)

        # 加载配置
        self._load_config()

        RoleManager._initialized = True

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 相对于当前文件: backend/roles/manager.py
        # 目标: config/roles.yaml
        base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "config" / "roles.yaml")

    def _load_config(self):
        """加载角色配置文件"""
        if not os.path.exists(self._config_path):
            print(f"警告: 角色配置文件不存在: {self._config_path}")
            # 使用默认配置
            self._create_default_config()
            return

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

            # 解析角色
            self._parse_roles()

            # 设置默认角色
            default_role = self._config.get('default_role', 'programmer')
            if default_role in self._roles:
                self._current_role_id = default_role

        except Exception as e:
            print(f"警告: 加载角色配置失败: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        self._roles = {
            'programmer': Role(
                id='programmer',
                name='程序员',
                name_en='Programmer',
                description='C/C++ 编程助手',
                icon='💻',
                model='claude-qwen:latest',
                base_model='qwen3:latest',
                modelfile='config/modelfiles/programmer.modelfile',
                tool_categories=['filesystem', 'executor', 'git', 'agent'],
                excluded_tools=[]
            )
        }
        self._current_role_id = 'programmer'

    def _parse_roles(self):
        """解析角色配置"""
        roles_config = self._config.get('roles', {})

        for role_id, role_data in roles_config.items():
            try:
                role = Role(
                    id=role_id,
                    name=role_data.get('name', role_id),
                    name_en=role_data.get('name_en', role_id),
                    description=role_data.get('description', ''),
                    icon=role_data.get('icon', '🤖'),
                    model=role_data.get('model', 'qwen3:latest'),
                    base_model=role_data.get('base_model', 'qwen3:latest'),
                    modelfile=role_data.get('modelfile', ''),
                    tool_categories=role_data.get('tool_categories', []),
                    included_tools=role_data.get('included_tools', []),
                    excluded_tools=role_data.get('excluded_tools', [])
                )
                self._roles[role_id] = role
            except Exception as e:
                print(f"警告: 解析角色 {role_id} 失败: {e}")

    def reload_config(self):
        """重新加载配置"""
        self._roles.clear()
        self._load_config()

    @property
    def current_role(self) -> Role:
        """获取当前角色"""
        return self._roles.get(self._current_role_id, list(self._roles.values())[0])

    @property
    def current_role_id(self) -> str:
        """获取当前角色 ID"""
        return self._current_role_id

    def switch_role(self, role_id: str) -> bool:
        """
        切换角色

        Args:
            role_id: 目标角色 ID

        Returns:
            True 如果切换成功
        """
        if role_id not in self._roles:
            return False

        old_role_id = self._current_role_id
        self._current_role_id = role_id

        # 触发回调
        for callback in self._callbacks:
            try:
                callback(old_role_id, role_id)
            except Exception as e:
                print(f"警告: 角色切换回调失败: {e}")

        return True

    def on_role_switch(self, callback: callable):
        """
        注册角色切换回调

        Args:
            callback: 回调函数 (old_role_id, new_role_id) -> None
        """
        self._callbacks.append(callback)

    def list_roles(self) -> List[Role]:
        """列出所有可用角色"""
        return list(self._roles.values())

    def get_role(self, role_id: str) -> Optional[Role]:
        """获取指定角色"""
        return self._roles.get(role_id)

    def get_model(self, role_id: Optional[str] = None) -> str:
        """
        获取角色使用的模型

        Args:
            role_id: 角色 ID（默认使用当前角色）

        Returns:
            模型名称
        """
        role = self._roles.get(role_id or self._current_role_id)
        if role:
            return role.model
        return "qwen3:latest"

    def get_modelfile_path(self, role_id: Optional[str] = None) -> Optional[str]:
        """
        获取角色的 Modelfile 绝对路径

        Args:
            role_id: 角色 ID（默认使用当前角色）

        Returns:
            Modelfile 绝对路径，如果不存在返回 None
        """
        role = self._roles.get(role_id or self._current_role_id)
        if not role or not role.modelfile:
            return None

        # 构建绝对路径
        modelfile_path = os.path.join(self._project_root, role.modelfile)
        if os.path.exists(modelfile_path):
            return modelfile_path
        return None

    def check_role_model_exists(self, role_id: Optional[str] = None) -> bool:
        """
        检查角色模型是否已创建

        Args:
            role_id: 角色 ID（默认使用当前角色）

        Returns:
            True 如果模型存在
        """
        role = self._roles.get(role_id or self._current_role_id)
        if not role:
            return False

        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True, text=True, timeout=10
            )
            return role.model in result.stdout
        except Exception:
            return False

    def create_role_model(self, role_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        为角色创建 Ollama 模型

        Args:
            role_id: 角色 ID（默认使用当前角色）

        Returns:
            (success, message) 元组
        """
        role = self._roles.get(role_id or self._current_role_id)
        if not role:
            return False, f"角色不存在: {role_id}"

        modelfile_path = self.get_modelfile_path(role_id)
        if not modelfile_path:
            return False, f"Modelfile 不存在: {role.modelfile}"

        try:
            # 使用 ollama create 创建模型
            result = subprocess.run(
                ['ollama', 'create', role.model, '-f', modelfile_path],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                return True, f"模型 {role.model} 创建成功"
            else:
                return False, f"创建失败: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "创建超时（>5分钟）"
        except FileNotFoundError:
            return False, "ollama 命令未找到"
        except Exception as e:
            return False, str(e)

    def create_all_role_models(self) -> Dict[str, Tuple[bool, str]]:
        """
        为所有角色创建模型

        Returns:
            {role_id: (success, message)} 字典
        """
        results = {}
        for role_id in self._roles:
            if not self.check_role_model_exists(role_id):
                results[role_id] = self.create_role_model(role_id)
            else:
                results[role_id] = (True, "模型已存在")
        return results

    def filter_tools(self, tools: List[Dict[str, Any]], role_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据角色过滤工具列表

        过滤优先级（从高到低）：
        1. excluded_tools: 明确排除的工具（最高优先级）
        2. included_tools: 明确包含的工具（跨类别复用）
        3. tool_categories: 按类别包含

        Args:
            tools: 完整的工具 schema 列表
            role_id: 角色 ID（默认使用当前角色）

        Returns:
            过滤后的工具列表
        """
        role = self._roles.get(role_id or self._current_role_id)
        if not role:
            return tools

        # 获取工具类别映射
        category_prefixes = {
            'filesystem': ['view_file', 'edit_file', 'create_file', 'grep_search', 'list_dir'],
            'executor': ['bash_run', 'cmake_build', 'run_tests'],
            'git': ['git'],
            'agent': ['instant_compact', 'propose_options'],
            'knowledge': ['extract_keywords', 'generate_summary', 'classify_knowledge', 'save_knowledge']
        }

        def get_tool_category(tool_name: str) -> str:
            """根据工具名称推断类别"""
            for category, prefixes in category_prefixes.items():
                for prefix in prefixes:
                    if tool_name.startswith(prefix) or tool_name == prefix:
                        return category
            return 'other'

        filtered = []
        for tool in tools:
            tool_name = tool.get('function', {}).get('name', '')

            # 1. 最高优先级：检查是否被明确排除
            if tool_name in role.excluded_tools:
                continue

            # 2. 次高优先级：检查是否被明确包含（跨类别复用）
            if tool_name in role.included_tools:
                filtered.append(tool)
                continue

            # 3. 按类别检查
            tool_category = get_tool_category(tool_name)
            if tool_category in role.tool_categories or tool_category == 'other':
                filtered.append(tool)

        return filtered

    def get_knowledge_taxonomy(self) -> Dict[str, Any]:
        """获取知识分类体系配置"""
        return self._config.get('knowledge_taxonomy', {})

    def get_knowledge_output_config(self) -> Dict[str, Any]:
        """获取知识输出格式配置"""
        return self._config.get('knowledge_output', {})


# 全局单例访问
_role_manager: Optional[RoleManager] = None


def get_role_manager() -> RoleManager:
    """获取角色管理器单例"""
    global _role_manager
    if _role_manager is None:
        _role_manager = RoleManager()
    return _role_manager


def initialize_role_manager(config_path: Optional[str] = None) -> RoleManager:
    """
    初始化角色管理器

    Args:
        config_path: 配置文件路径

    Returns:
        角色管理器实例
    """
    global _role_manager
    # 重置单例
    RoleManager._instance = None
    RoleManager._initialized = False
    _role_manager = RoleManager(config_path)
    return _role_manager
