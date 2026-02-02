# -*- coding: utf-8 -*-
"""
管道模式 (Pipeline Pattern) - 消息处理
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List


class MessageProcessor(ABC):
    """消息处理器基类"""

    @abstractmethod
    def process(self, messages: List[Dict]) -> List[Dict]:
        """处理消息列表"""
        pass


class CleanSystemReminders(MessageProcessor):
    """清理历史消息中的 <system-reminder> 标签"""

    def __init__(self):
        self.pattern = re.compile(r'<system-reminder>.*?</system-reminder>\s*', re.DOTALL)

    def process(self, messages: List[Dict]) -> List[Dict]:
        if not messages:
            return messages

        cleaned = []
        for i, msg in enumerate(messages):
            is_last_user_msg = (
                msg.get('role') == 'user' and
                i == len(messages) - 1
            )

            if is_last_user_msg:
                # 保留最后一条用户消息的 system-reminder
                cleaned.append(msg)
            elif msg.get('role') == 'user' and self.pattern.search(msg.get('content', '')):
                # 清理历史用户消息中的 system-reminder
                new_content = self.pattern.sub('', msg.get('content', '')).strip()
                cleaned.append({**msg, 'content': new_content})
            else:
                cleaned.append(msg)

        return cleaned


class TruncateLongContent(MessageProcessor):
    """截断过长的消息内容"""

    def __init__(self, max_length: int = 50000):
        self.max_length = max_length

    def process(self, messages: List[Dict]) -> List[Dict]:
        result = []
        for msg in messages:
            content = msg.get('content', '')
            if len(content) > self.max_length:
                truncated = content[:self.max_length]
                truncated += f"\n\n[... truncated {len(content) - self.max_length} characters ...]"
                result.append({**msg, 'content': truncated})
            else:
                result.append(msg)
        return result


class MessagePipeline:
    """消息处理管道"""

    def __init__(self):
        self.processors: List[MessageProcessor] = []

    def add(self, processor: MessageProcessor) -> 'MessagePipeline':
        """添加处理器到管道"""
        self.processors.append(processor)
        return self

    def process(self, messages: List[Dict]) -> List[Dict]:
        """依次执行所有处理器"""
        result = messages
        for processor in self.processors:
            result = processor.process(result)
        return result

    @classmethod
    def default(cls) -> 'MessagePipeline':
        """创建默认管道"""
        return cls().add(CleanSystemReminders())
