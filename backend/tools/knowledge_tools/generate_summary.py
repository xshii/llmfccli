# -*- coding: utf-8 -*-
"""
GenerateSummary Tool - 生成文本摘要

用于知识治理场景，支持：
1. 自动生成文本摘要
2. 可配置摘要长度
3. 支持多种摘要格式
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class GenerateSummaryParams(BaseModel):
    """GenerateSummary 工具参数"""
    text: str = Field(
        description="要生成摘要的文本内容"
    )
    max_length: int = Field(
        300,
        description="摘要最大字数（默认 300）",
        ge=50,
        le=1000
    )
    min_length: int = Field(
        100,
        description="摘要最小字数（默认 100）",
        ge=20,
        le=500
    )
    format: str = Field(
        "paragraph",
        description="摘要格式（paragraph: 段落 / bullet_points: 要点）"
    )
    focus: Optional[str] = Field(
        None,
        description="摘要关注点（可选，如：技术细节、核心观点、使用方法）"
    )


class GenerateSummaryTool(BaseTool):
    """生成文本摘要"""

    @property
    def name(self) -> str:
        return "generate_summary"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Generate a concise summary from text content.\n\n'
                'Features:\n'
                '- Configurable summary length (min/max)\n'
                '- Multiple output formats (paragraph/bullet points)\n'
                '- Optional focus area specification\n\n'
                'Example:\n'
                '  generate_summary(text="文章内容...", max_length=300, format="bullet_points")'
            ),
            'zh': (
                '从文本内容生成精炼摘要。\n\n'
                '功能特性：\n'
                '- 可配置摘要长度（最小/最大）\n'
                '- 支持多种输出格式（段落/要点）\n'
                '- 可选的关注点设置\n\n'
                '示例：\n'
                '  generate_summary(text="文章内容...", max_length=300, format="bullet_points")'
            )
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'text': {
                'en': 'Text content to summarize',
                'zh': '要生成摘要的文本内容',
            },
            'max_length': {
                'en': 'Maximum summary length in characters (default: 300)',
                'zh': '摘要最大字数（默认：300）',
            },
            'min_length': {
                'en': 'Minimum summary length in characters (default: 100)',
                'zh': '摘要最小字数（默认：100）',
            },
            'format': {
                'en': 'Summary format (paragraph/bullet_points)',
                'zh': '摘要格式（paragraph: 段落 / bullet_points: 要点）',
            },
            'focus': {
                'en': 'Optional focus area for the summary',
                'zh': '摘要关注点（可选）',
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
        return GenerateSummaryParams

    def execute(self, text: str, max_length: int = 300, min_length: int = 100,
                format: str = "paragraph", focus: Optional[str] = None) -> Dict[str, Any]:
        """
        生成摘要

        注意：此工具返回摘要生成的提示和参数，
        实际的摘要生成由 LLM 完成

        Args:
            text: 要摘要的文本
            max_length: 最大长度
            min_length: 最小长度
            format: 输出格式
            focus: 关注点

        Returns:
            Dict 包含摘要生成指令
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': '文本内容为空'
            }

        # 计算文本统计信息
        text_length = len(text)
        word_count = len(text.split()) if ' ' in text else text_length // 2  # 估算词数

        # 验证参数
        if min_length > max_length:
            min_length, max_length = max_length, min_length

        # 构建摘要提示
        prompt_parts = []

        if format == "bullet_points":
            prompt_parts.append("请以要点形式总结以下文本的核心内容：")
            prompt_parts.append(f"- 生成 3-5 个要点")
            prompt_parts.append(f"- 每个要点 {min_length // 3}-{max_length // 3} 字")
        else:
            prompt_parts.append("请生成以下文本的摘要：")
            prompt_parts.append(f"- 摘要长度：{min_length}-{max_length} 字")

        if focus:
            prompt_parts.append(f"- 重点关注：{focus}")

        prompt_parts.append("- 保持客观准确，不添加主观评价")
        prompt_parts.append("- 提取核心观点和关键信息")

        summary_prompt = "\n".join(prompt_parts)

        # 返回摘要任务描述（实际摘要由 LLM 生成）
        return {
            'success': True,
            'action': 'generate_summary',
            'task_description': summary_prompt,
            'source_text': text[:500] + "..." if len(text) > 500 else text,
            'parameters': {
                'max_length': max_length,
                'min_length': min_length,
                'format': format,
                'focus': focus
            },
            'source_stats': {
                'text_length': text_length,
                'estimated_words': word_count
            },
            'instruction': (
                f"请根据上述要求生成摘要。\n"
                f"原文长度：{text_length} 字\n"
                f"目标摘要：{min_length}-{max_length} 字"
            )
        }
