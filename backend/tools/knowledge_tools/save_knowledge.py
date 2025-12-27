# -*- coding: utf-8 -*-
"""
SaveKnowledge Tool - 保存知识条目

用于知识治理场景，支持：
1. 保存知识条目到 JSON/YAML 文件
2. 结构化存储摘要、关键词、分类
3. 支持知识关联关系
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class KnowledgeRelation(BaseModel):
    """知识关联关系"""
    type: str = Field(description="关联类型（related_to/depends_on/extends/implements/contradicts）")
    target_id: str = Field(description="目标知识条目 ID")
    description: Optional[str] = Field(None, description="关联描述")


class SaveKnowledgeParams(BaseModel):
    """SaveKnowledge 工具参数"""
    title: str = Field(
        description="知识条目标题"
    )
    summary: str = Field(
        description="知识摘要（100-300 字）"
    )
    keywords: List[str] = Field(
        description="关键词列表（5-10 个）"
    )
    categories: List[str] = Field(
        description="分类标签列表（如：['编程语言', 'Python']）"
    )
    source_file: Optional[str] = Field(
        None,
        description="源文件路径（可选）"
    )
    source_url: Optional[str] = Field(
        None,
        description="源 URL（可选）"
    )
    relations: Optional[List[Dict[str, str]]] = Field(
        None,
        description="关联关系列表（可选）"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="额外元数据（可选）"
    )
    output_file: Optional[str] = Field(
        None,
        description="输出文件路径（默认自动生成）"
    )


class SaveKnowledgeTool(BaseTool):
    """保存知识条目到文件"""

    @property
    def name(self) -> str:
        return "save_knowledge"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Save a structured knowledge entry to file for RAG indexing.\n\n'
                'Features:\n'
                '- Structured storage: title, summary, keywords, categories\n'
                '- Support for knowledge relations\n'
                '- Auto-generated ID and timestamps\n\n'
                'Example:\n'
                '  save_knowledge(\n'
                '    title="Python 设计模式",\n'
                '    summary="介绍 Python 中常用的设计模式...",\n'
                '    keywords=["Python", "设计模式", "单例模式"],\n'
                '    categories=["编程语言", "Python"]\n'
                '  )'
            ),
            'zh': (
                '将结构化知识条目保存到文件，用于 RAG 索引。\n\n'
                '功能特性：\n'
                '- 结构化存储：标题、摘要、关键词、分类\n'
                '- 支持知识关联关系\n'
                '- 自动生成 ID 和时间戳\n\n'
                '示例：\n'
                '  save_knowledge(\n'
                '    title="Python 设计模式",\n'
                '    summary="介绍 Python 中常用的设计模式...",\n'
                '    keywords=["Python", "设计模式", "单例模式"],\n'
                '    categories=["编程语言", "Python"]\n'
                '  )'
            )
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'title': {
                'en': 'Knowledge entry title',
                'zh': '知识条目标题',
            },
            'summary': {
                'en': 'Knowledge summary (100-300 characters)',
                'zh': '知识摘要（100-300 字）',
            },
            'keywords': {
                'en': 'List of keywords (5-10)',
                'zh': '关键词列表（5-10 个）',
            },
            'categories': {
                'en': 'Category labels',
                'zh': '分类标签列表',
            },
            'source_file': {
                'en': 'Source file path (optional)',
                'zh': '源文件路径（可选）',
            },
            'source_url': {
                'en': 'Source URL (optional)',
                'zh': '源 URL（可选）',
            },
            'relations': {
                'en': 'List of knowledge relations (optional)',
                'zh': '关联关系列表（可选）',
            },
            'metadata': {
                'en': 'Additional metadata (optional)',
                'zh': '额外元数据（可选）',
            },
            'output_file': {
                'en': 'Output file path (auto-generated if not specified)',
                'zh': '输出文件路径（默认自动生成）',
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
        return SaveKnowledgeParams

    def execute(self, title: str, summary: str, keywords: List[str],
                categories: List[str], source_file: Optional[str] = None,
                source_url: Optional[str] = None,
                relations: Optional[List[Dict[str, str]]] = None,
                metadata: Optional[Dict[str, Any]] = None,
                output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        保存知识条目

        Args:
            title: 标题
            summary: 摘要
            keywords: 关键词列表
            categories: 分类列表
            source_file: 源文件路径
            source_url: 源 URL
            relations: 关联关系
            metadata: 额外元数据
            output_file: 输出文件路径

        Returns:
            Dict 包含保存结果
        """
        # 验证必要参数
        if not title or not title.strip():
            return {'success': False, 'error': '标题不能为空'}

        if not summary or not summary.strip():
            return {'success': False, 'error': '摘要不能为空'}

        if not keywords or len(keywords) < 1:
            return {'success': False, 'error': '至少需要 1 个关键词'}

        if not categories or len(categories) < 1:
            return {'success': False, 'error': '至少需要 1 个分类'}

        try:
            # 生成知识条目 ID
            entry_id = self._generate_id(title)

            # 构建知识条目
            knowledge_entry = {
                'id': entry_id,
                'title': title.strip(),
                'summary': summary.strip(),
                'keywords': keywords,
                'categories': categories,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
            }

            # 添加可选字段
            if source_file:
                knowledge_entry['source_file'] = source_file

            if source_url:
                knowledge_entry['source_url'] = source_url

            if relations:
                knowledge_entry['relations'] = relations

            if metadata:
                knowledge_entry['metadata'] = metadata

            # 确定输出路径
            if not output_file:
                output_file = self._get_default_output_path(entry_id)

            # 确保目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_entry, f, ensure_ascii=False, indent=2)

            return {
                'success': True,
                'entry_id': entry_id,
                'output_file': output_file,
                'knowledge_entry': knowledge_entry,
                'message': f'知识条目已保存到 {output_file}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_id(self, title: str) -> str:
        """生成知识条目 ID"""
        import hashlib
        import re

        # 清理标题
        clean_title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title)

        # 生成时间戳部分
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # 生成标题 hash（取前 8 位）
        title_hash = hashlib.md5(clean_title.encode('utf-8')).hexdigest()[:8]

        return f"kb_{timestamp}_{title_hash}"

    def _get_default_output_path(self, entry_id: str) -> str:
        """获取默认输出路径"""
        # 默认保存到项目根目录下的 knowledge_base 目录
        if self.project_root:
            base_dir = os.path.join(self.project_root, 'knowledge_base')
        else:
            base_dir = os.path.join(os.getcwd(), 'knowledge_base')

        # 按日期分组
        date_dir = datetime.now().strftime('%Y%m')

        return os.path.join(base_dir, date_dir, f"{entry_id}.json")
