# -*- coding: utf-8 -*-
"""
工具基类 - 支持 Pydantic schema 自动生成
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


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
    @abstractmethod
    def description(self) -> str:
        """工具描述（用于 LLM 理解工具用途）"""
        pass

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
