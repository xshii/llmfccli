# -*- coding: utf-8 -*-
"""
ClassifyKnowledge Tool - 知识分类

用于知识治理场景，支持：
1. 自动分类知识内容
2. 多层级分类体系
3. 支持多标签分类
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from backend.roles import get_role_manager


class ClassifyKnowledgeParams(BaseModel):
    """ClassifyKnowledge 工具参数"""
    text: str = Field(
        description="要分类的文本内容"
    )
    title: Optional[str] = Field(
        None,
        description="文档标题（可选，有助于提高分类准确性）"
    )
    keywords: Optional[List[str]] = Field(
        None,
        description="已提取的关键词列表（可选）"
    )
    max_categories: int = Field(
        3,
        description="最大分类数量（支持多分类）",
        ge=1,
        le=5
    )
    include_confidence: bool = Field(
        True,
        description="是否包含分类置信度"
    )


class ClassifyKnowledgeTool(BaseTool):
    """知识内容分类"""

    @property
    def name(self) -> str:
        return "classify_knowledge"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Classify knowledge content into predefined categories.\n\n'
                'Features:\n'
                '- Multi-level category hierarchy\n'
                '- Support for multiple labels\n'
                '- Confidence scoring\n\n'
                'Example:\n'
                '  classify_knowledge(text="文章内容...", title="标题", max_categories=3)'
            ),
            'zh': (
                '将知识内容分类到预定义的类别体系中。\n\n'
                '功能特性：\n'
                '- 多层级分类体系\n'
                '- 支持多标签分类\n'
                '- 置信度评分\n\n'
                '示例：\n'
                '  classify_knowledge(text="文章内容...", title="标题", max_categories=3)'
            )
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'text': {
                'en': 'Text content to classify',
                'zh': '要分类的文本内容',
            },
            'title': {
                'en': 'Document title (optional)',
                'zh': '文档标题（可选）',
            },
            'keywords': {
                'en': 'Pre-extracted keywords (optional)',
                'zh': '已提取的关键词列表（可选）',
            },
            'max_categories': {
                'en': 'Maximum number of categories (default: 3)',
                'zh': '最大分类数量（默认：3）',
            },
            'include_confidence': {
                'en': 'Whether to include confidence scores',
                'zh': '是否包含分类置信度',
            },
        }

    @property
    def category(self) -> str:
        return "knowledge"

    @property
    def priority(self) -> int:
        return 70

    @property
    def parameters_model(self):
        return ClassifyKnowledgeParams

    def execute(self, text: str, title: Optional[str] = None,
                keywords: Optional[List[str]] = None, max_categories: int = 3,
                include_confidence: bool = True) -> Dict[str, Any]:
        """
        分类知识内容

        Args:
            text: 要分类的文本
            title: 文档标题
            keywords: 已提取的关键词
            max_categories: 最大分类数
            include_confidence: 是否包含置信度

        Returns:
            Dict 包含分类结果和建议
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': '文本内容为空'
            }

        # 获取分类体系配置
        role_manager = get_role_manager()
        taxonomy = role_manager.get_knowledge_taxonomy()
        categories = taxonomy.get('categories', self._get_default_taxonomy())

        # 构建分类体系描述
        taxonomy_desc = self._format_taxonomy(categories)

        # 构建分类提示
        classification_context = []

        if title:
            classification_context.append(f"文档标题：{title}")

        if keywords:
            classification_context.append(f"关键词：{', '.join(keywords[:10])}")

        classification_context.append(f"内容片段：{text[:500]}..." if len(text) > 500 else f"内容：{text}")

        # 返回分类任务描述
        return {
            'success': True,
            'action': 'classify_knowledge',
            'taxonomy': taxonomy_desc,
            'context': "\n".join(classification_context),
            'parameters': {
                'max_categories': max_categories,
                'include_confidence': include_confidence
            },
            'instruction': (
                f"请根据以下分类体系，为知识内容选择最合适的 {max_categories} 个分类：\n\n"
                f"**分类体系**：\n{taxonomy_desc}\n\n"
                f"**待分类内容**：\n{chr(10).join(classification_context)}\n\n"
                f"请返回分类结果，格式：\n"
                f"- 主分类: <一级分类> > <二级分类>\n"
                f"- 副分类: <一级分类> > <二级分类>\n"
                f"{'- 置信度: 0.0-1.0' if include_confidence else ''}"
            ),
            'available_categories': [cat.get('name', '') for cat in categories]
        }

    def _get_default_taxonomy(self) -> List[Dict]:
        """获取默认分类体系"""
        return [
            {
                'name': '编程语言',
                'subcategories': ['C/C++', 'Python', 'Rust', 'Go', 'JavaScript', '其他语言']
            },
            {
                'name': '软件工程',
                'subcategories': ['设计模式', '架构设计', '测试方法', '重构技术', '代码规范']
            },
            {
                'name': '工具与框架',
                'subcategories': ['构建工具', '版本控制', 'CI/CD', '容器化', 'IDE 与编辑器']
            },
            {
                'name': '系统与网络',
                'subcategories': ['操作系统', '网络协议', '分布式系统', '数据库', '安全']
            },
            {
                'name': 'AI 与机器学习',
                'subcategories': ['深度学习', '自然语言处理', '计算机视觉', '强化学习', 'MLOps']
            }
        ]

    def _format_taxonomy(self, categories: List[Dict]) -> str:
        """格式化分类体系"""
        lines = []
        for cat in categories:
            name = cat.get('name', '')
            subcats = cat.get('subcategories', [])
            lines.append(f"**{name}**")
            for subcat in subcats:
                lines.append(f"  - {subcat}")
        return "\n".join(lines)
