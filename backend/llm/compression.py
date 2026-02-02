# -*- coding: utf-8 -*-
"""
上下文压缩模块
"""

import json
from typing import Any, Callable, Dict, List

from .prompts import get_compression_prompt


def estimate_tokens_chinese(messages: List[Dict[str, str]]) -> int:
    """
    估算 token 数量（中文优化，约 3 字符/token）

    Args:
        messages: 消息列表

    Returns:
        估算的 token 数量
    """
    total_chars = sum(len(msg.get('content', '')) for msg in messages)
    estimated_tokens = total_chars // 3
    estimated_tokens += len(messages) * 10  # 消息开销
    return estimated_tokens


def estimate_tokens_english(messages: List[Dict[str, str]]) -> int:
    """
    估算 token 数量（英文优化，约 4 字符/token）

    Args:
        messages: 消息列表

    Returns:
        估算的 token 数量
    """
    total_chars = sum(len(msg.get('content', '')) for msg in messages)
    estimated_tokens = total_chars // 4
    estimated_tokens += len(messages) * 4  # 消息开销
    return estimated_tokens


def parse_compression_response(content: str) -> Dict[str, Any]:
    """
    解析压缩响应

    Args:
        content: LLM 响应内容

    Returns:
        解析后的压缩结果

    Raises:
        RuntimeError: 解析失败
    """
    try:
        # 提取 JSON 代码块
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse compression result: {e}\nContent: {content}")


def compress_context(
    messages: List[Dict[str, str]],
    target_tokens: int,
    must_keep: str,
    compressible: str,
    chat_func: Callable[[List[Dict[str, str]]], Dict[str, Any]],
    estimate_tokens: Callable[[List[Dict[str, str]]], int] = estimate_tokens_chinese
) -> Dict[str, Any]:
    """
    使用 LLM 压缩对话历史

    Args:
        messages: 完整对话历史
        target_tokens: 压缩后目标 token 数
        must_keep: 必须保留的内容描述
        compressible: 可压缩的内容描述
        chat_func: LLM 聊天函数
        estimate_tokens: token 估算函数

    Returns:
        压缩结果字典
    """
    current_tokens = estimate_tokens(messages)

    compression_prompt = get_compression_prompt(
        current_tokens=current_tokens,
        target_tokens=target_tokens,
        must_keep=must_keep,
        compressible=compressible
    )

    compress_messages = [
        {'role': 'system', 'content': 'You are a context compression assistant.'},
        {'role': 'user', 'content': compression_prompt}
    ]

    response = chat_func(compress_messages)
    content = response['message']['content']

    return parse_compression_response(content)
