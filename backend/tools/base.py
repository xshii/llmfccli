# -*- coding: utf-8 -*-
"""
工具基类 - 支持 Pydantic schema 自动生成
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel

from backend.utils.i18n import t


class FileSystemError(Exception):
    """文件系统操作错误

    统一的文件系统异常类，用于所有文件系统工具。
    """
    pass


@dataclass
class ToolResult:
    """统一的工具返回结果格式

    设计原则：
    - ok: 业务层面是否成功
    - output: 成功时是结果，失败时是错误原因
    """
    ok: bool = True
    output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为 dict（包含 success 别名用于向后兼容）"""
        return {'success': self.ok, 'output': self.output}

    @classmethod
    def success(cls, output: str = "") -> "ToolResult":
        """快捷创建成功结果"""
        return cls(ok=True, output=output)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        """快捷创建失败结果"""
        return cls(ok=False, output=error)

    # 别名，保持兼容
    ok_ = success

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ToolResult":
        """从旧格式 dict 转换（兼容层）"""
        # 判断成功/失败
        ok = d.get('success', d.get('ok', True))
        exit_code = d.get('exit_code', d.get('return_code', d.get('returncode', 0)))
        if exit_code != 0:
            ok = False

        # 提取输出
        if ok:
            output = d.get('output', d.get('stdout', d.get('content', '')))
        else:
            output = d.get('error', d.get('stderr', d.get('output', '')))

        return cls(ok=ok, output=output)


class BaseTool(ABC):
    """工具基类 - 声明式定义工具"""

    def __init__(self, project_root: Optional[str] = None, **dependencies):
        """
        初始化工具

        Args:
            project_root: 项目根目录
            **dependencies: 其他依赖（agent 等）
        """
        self.project_root = project_root
        self.dependencies = dependencies

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称（必须唯一）"""
        pass

    @property
    def description(self) -> str:
        """
        工具描述（用于 LLM 理解工具用途）

        默认使用 description_i18n 进行翻译。
        子类应该重写 description_i18n 属性提供多语言支持。
        """
        desc_dict = self.description_i18n
        if isinstance(desc_dict, dict):
            return t(desc_dict)
        # 向后兼容：如果子类直接重写了 description 返回字符串
        return desc_dict or ''

    @property
    def description_i18n(self) -> Dict[str, str]:
        """
        多语言工具描述

        子类应该重写此方法返回多语言描述字典，例如：
        {
            'en': 'Read file contents',
            'zh': '读取文件内容'
        }
        """
        return {}

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        """
        获取参数的多语言描述

        子类可以重写此方法返回参数的多语言描述，例如：
        {
            'path': {'en': 'File path', 'zh': '文件路径'},
            'old_str': {'en': 'String to replace', 'zh': '要替换的字符串'}
        }

        Returns:
            Dict[参数名, Dict[语言, 描述]]
        """
        return {}

    @property
    def category(self) -> str:
        """工具类别

        可选值: 'filesystem', 'executor', 'git', 'agent', 'other'
        """
        return "other"

    @property
    def priority(self) -> int:
        """工具优先级 (用于工具列表排序)

        优先级范围: 1-100
        - 高优先级 (80-100): 最常用工具，放在列表前面 (前30%)
        - 中优先级 (50-79): 常用工具，放在列表最后倒序 (中30%)
        - 低优先级 (1-49): 较少使用工具，放在列表中间随机 (后40%)

        默认: 50 (中优先级)
        """
        return 50

    @property
    def skip_confirmation(self) -> bool:
        """是否跳过用户确认直接执行

        默认: False（需要确认）
        无副作用的工具（如查看、交互、任务管理）可设为 True。
        """
        return False

    @property
    def parameters_model(self) -> Type[BaseModel]:
        """参数模型（Pydantic）- 自动生成 JSON Schema

        子类应该返回一个 Pydantic BaseModel 类，例如：

        class MyToolParams(BaseModel):
            path: str = Field(description="文件路径")
            count: int = Field(1, description="数量")

        @property
        def parameters_model(self):
            return MyToolParams
        """
        # 默认无参数
        return BaseModel

    @abstractmethod
    def execute(self, **kwargs) -> Union[ToolResult, Dict[str, Any]]:
        """
        执行工具

        Args:
            **kwargs: 参数（与 parameters_model 定义的字段对应）

        Returns:
            ToolResult 或 Dict（向后兼容）
        """
        pass

    def get_openai_schema(self) -> Dict[str, Any]:
        """自动生成 OpenAI function calling schema"""
        # 从 Pydantic model 生成 JSON schema
        if self.parameters_model == BaseModel:
            # 无参数的工具
            parameters_schema = {
                'type': 'object',
                'properties': {},
                'required': []
            }
        else:
            # 使用 Pydantic 的 model_json_schema
            schema = self.parameters_model.model_json_schema()

            # 转换为 OpenAI 格式
            parameters_schema = {
                'type': 'object',
                'properties': schema.get('properties', {}),
                'required': schema.get('required', [])
            }

            # 移除 Pydantic 特有的字段（如 $defs）
            if 'title' in parameters_schema:
                del parameters_schema['title']

            # 应用多语言参数描述
            params_i18n = self.get_parameters_i18n()
            if params_i18n:
                for param_name, translations in params_i18n.items():
                    if param_name in parameters_schema['properties']:
                        # 使用当前语言的描述替换
                        localized_desc = t(translations)
                        if localized_desc:
                            parameters_schema['properties'][param_name]['description'] = localized_desc

        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': parameters_schema
            }
        }

    def validate_and_execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数并执行工具"""
        try:
            # 使用 Pydantic 验证参数
            if self.parameters_model != BaseModel:
                validated = self.parameters_model(**arguments)
                # 转换为 dict 传递给 execute
                validated_args = validated.model_dump()
            else:
                validated_args = arguments

            # 执行工具
            result = self.execute(**validated_args)

            # 统一转换为 dict
            if isinstance(result, ToolResult):
                return result.to_dict()
            return result

        except Exception as e:
            return ToolResult.fail(str(e)).to_dict()

    def confirmation_signature(self, _arguments: Dict[str, Any]) -> str:
        """
        获取用于确认分组的签名

        默认返回工具名称，允许同一工具的所有调用共享确认状态。
        子类可以重写此方法实现细粒度控制，例如：
        - bash_run 可以返回 "bash_run:ls" 按基础命令分组
        - git 可以返回 "git:push" 按操作类型分组

        Args:
            arguments: 工具参数

        Returns:
            签名字符串
        """
        return self.name

    def is_dangerous(self, _arguments: Dict[str, Any]) -> bool:
        """
        检查操作是否危险，需要额外确认

        危险操作即使在已允许的工具列表中也需要确认。
        子类可以重写此方法定义危险条件，例如：
        - git reset --hard
        - git push --force
        - rm -rf

        Args:
            arguments: 工具参数

        Returns:
            True 如果操作危险需要确认
        """
        return False

    # ========== 路径处理方法 ==========

    def resolve_path(self, path: str) -> str:
        """
        解析路径为绝对路径

        将相对路径转换为基于 project_root 的绝对路径。

        Args:
            path: 相对或绝对路径

        Returns:
            绝对路径
        """
        import os
        if not os.path.isabs(path) and self.project_root:
            path = os.path.join(self.project_root, path)
        return os.path.abspath(path)

    def _validate_path_security(self, path: str) -> None:
        """
        验证路径安全性（防止路径遍历攻击）

        内部方法，通过 resolve_and_validate_path() 调用。

        Args:
            path: 绝对路径

        Raises:
            ValueError: 如果路径在项目根目录外
        """
        import os
        if self.project_root:
            project_root = os.path.abspath(self.project_root)
            if not path.startswith(project_root):
                raise ValueError(f"Path {path} is outside project root {project_root}")

    def resolve_and_validate_path(self, path: str) -> str:
        """
        解析路径并验证安全性

        组合 resolve_path 和 _validate_path_security。

        Args:
            path: 相对或绝对路径

        Returns:
            验证后的绝对路径

        Raises:
            ValueError: 如果路径在项目根目录外
        """
        resolved = self.resolve_path(path)
        self._validate_path_security(resolved)
        return resolved

    def find_file_with_fallback(self, path: str) -> str:
        """
        查找文件，不存在时尝试模糊匹配

        Args:
            path: 文件路径（已解析的绝对路径或相对路径）

        Returns:
            存在的文件绝对路径

        Raises:
            FileNotFoundError: 如果文件不存在且无法找到相似文件
        """
        import os

        # 确保是绝对路径
        abs_path = self.resolve_path(path)

        if os.path.exists(abs_path):
            return abs_path

        # 尝试模糊匹配
        from backend.cli.path_utils import PathUtils
        path_utils = PathUtils(self.project_root or os.getcwd())
        similar = path_utils.find_similar_file(path)

        if similar:
            found_path = os.path.join(self.project_root or os.getcwd(), similar)
            return os.path.abspath(found_path)

        raise FileNotFoundError(f"File not found: {path}")
