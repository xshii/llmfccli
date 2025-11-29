# -*- coding: utf-8 -*-
"""
工具基类 - 支持 Pydantic schema 自动生成
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel

from backend.i18n import t


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
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具

        Args:
            **kwargs: 参数（与 parameters_model 定义的字段对应）

        Returns:
            Dict 包含执行结果
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
            return self.execute(**validated_args)

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': self.name,
                'arguments': arguments
            }

    def get_confirmation_signature(self, _arguments: Dict[str, Any]) -> str:
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

    def is_dangerous_operation(self, _arguments: Dict[str, Any]) -> bool:
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
