# -*- coding: utf-8 -*-
"""
ExtractKeywords Tool - 从文本中提取关键词

用于知识治理场景，支持：
1. 自动提取文本关键词
2. 计算关键词权重
3. 按重要性排序
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class ExtractKeywordsParams(BaseModel):
    """ExtractKeywords 工具参数"""
    text: str = Field(
        description="要提取关键词的文本内容"
    )
    max_keywords: int = Field(
        10,
        description="最大关键词数量（默认 10）",
        ge=1,
        le=50
    )
    include_weight: bool = Field(
        True,
        description="是否包含关键词权重"
    )
    language: str = Field(
        "auto",
        description="文本语言（auto/zh/en）"
    )


class ExtractKeywordsTool(BaseTool):
    """从文本中提取关键词"""

    @property
    def name(self) -> str:
        return "extract_keywords"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                'Extract keywords from text content for knowledge base indexing.\n\n'
                'Features:\n'
                '- Automatic keyword extraction with weight scoring\n'
                '- Support for Chinese and English text\n'
                '- Configurable maximum keywords count\n\n'
                'Example:\n'
                '  extract_keywords(text="文章内容...", max_keywords=10)'
            ),
            'zh': (
                '从文本内容中提取关键词，用于知识库索引。\n\n'
                '功能特性：\n'
                '- 自动提取关键词并计算权重\n'
                '- 支持中英文文本\n'
                '- 可配置最大关键词数量\n\n'
                '示例：\n'
                '  extract_keywords(text="文章内容...", max_keywords=10)'
            )
        }

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'text': {
                'en': 'Text content to extract keywords from',
                'zh': '要提取关键词的文本内容',
            },
            'max_keywords': {
                'en': 'Maximum number of keywords (default: 10)',
                'zh': '最大关键词数量（默认：10）',
            },
            'include_weight': {
                'en': 'Whether to include keyword weights',
                'zh': '是否包含关键词权重',
            },
            'language': {
                'en': 'Text language (auto/zh/en)',
                'zh': '文本语言（auto/zh/en）',
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
        return ExtractKeywordsParams

    def execute(self, text: str, max_keywords: int = 10,
                include_weight: bool = True, language: str = "auto") -> Dict[str, Any]:
        """
        提取关键词

        使用 TF-IDF 和词频统计的简化实现

        Args:
            text: 要分析的文本
            max_keywords: 最大关键词数量
            include_weight: 是否包含权重
            language: 语言设置

        Returns:
            Dict 包含关键词列表
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': '文本内容为空',
                'keywords': []
            }

        try:
            # 检测语言
            detected_language = self._detect_language(text) if language == "auto" else language

            # 提取关键词
            if detected_language == "zh":
                keywords = self._extract_chinese_keywords(text, max_keywords)
            else:
                keywords = self._extract_english_keywords(text, max_keywords)

            # 格式化输出
            if include_weight:
                result_keywords = [
                    {"keyword": kw, "weight": round(weight, 3)}
                    for kw, weight in keywords
                ]
            else:
                result_keywords = [kw for kw, _ in keywords]

            return {
                'success': True,
                'keywords': result_keywords,
                'language': detected_language,
                'total_extracted': len(result_keywords)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'keywords': []
            }

    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        # 统计中文字符比例
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text.replace(" ", ""))

        if total_chars == 0:
            return "en"

        chinese_ratio = chinese_chars / total_chars
        return "zh" if chinese_ratio > 0.3 else "en"

    def _extract_chinese_keywords(self, text: str, max_keywords: int) -> List[tuple]:
        """提取中文关键词（简化实现）"""
        import re

        # 简单分词（基于常见模式）
        # 移除标点和特殊字符
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', text)

        # 提取 2-4 字的词语（简化的中文分词）
        words = []

        # 尝试导入 jieba（如果可用）
        try:
            import jieba
            words = list(jieba.cut(text))
        except ImportError:
            # 回退到简单的 n-gram 方法
            for n in [4, 3, 2]:
                for i in range(len(text) - n + 1):
                    word = text[i:i+n]
                    if all('\u4e00' <= c <= '\u9fff' for c in word):
                        words.append(word)

        # 统计词频
        word_freq = {}
        for word in words:
            if len(word) >= 2:  # 忽略单字
                word_freq[word] = word_freq.get(word, 0) + 1

        # 排除停用词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人',
                     '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                     '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '但'}
        word_freq = {k: v for k, v in word_freq.items() if k not in stopwords}

        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # 计算权重（归一化）
        if sorted_words:
            max_freq = sorted_words[0][1]
            keywords = [(word, freq / max_freq) for word, freq in sorted_words[:max_keywords]]
        else:
            keywords = []

        return keywords

    def _extract_english_keywords(self, text: str, max_keywords: int) -> List[tuple]:
        """提取英文关键词"""
        import re

        # 转小写并分词
        text = text.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)  # 至少 3 个字母

        # 停用词
        stopwords = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
            'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
            'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
            'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no',
            'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
            'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also'
        }

        # 统计词频
        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # 计算权重
        if sorted_words:
            max_freq = sorted_words[0][1]
            keywords = [(word, freq / max_freq) for word, freq in sorted_words[:max_keywords]]
        else:
            keywords = []

        return keywords
