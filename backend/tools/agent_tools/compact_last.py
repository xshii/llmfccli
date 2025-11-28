# -*- coding: utf-8 -*-
"""
CompactLast Tool - 压缩最近的对话历史
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class CompactLastParams(BaseModel):
    """CompactLast 工具参数"""
    count: int = Field(description="要替换的最近消息数量", ge=1)
    replacement: str = Field(description="替换消息的摘要文本")


class CompactLastTool(BaseTool):
    """压缩最近对话历史工具"""

    def __init__(self, project_root=None, agent=None, **dependencies):
        super().__init__(project_root, **dependencies)
        self.agent = agent

    @property
    def name(self) -> str:
        return "compact_last"

    @property
    def description(self) -> str:
        return ("Compact recent conversation messages by replacing them with your summary. "
                "Use when token usage is high and recent messages contain redundant details.")

    @property
    def category(self) -> str:
        return "agent"

    @property
    def parameters_model(self):
        return CompactLastParams

    def execute(self, count: int, replacement: str) -> Dict[str, Any]:
        """执行历史压缩"""
        if not self.agent:
            return {'success': False, 'error': 'Agent not available'}

        try:
            history_len = len(self.agent.conversation_history)
            if count <= 0:
                return {'success': False, 'error': f'Invalid count: {count}'}

            if count > history_len:
                return {'success': False, 'error': f'Count {count} exceeds history length {history_len}'}

            # Get token counter
            token_counter = self.agent.token_counter
            max_tokens = token_counter.max_tokens
            tokens_before = token_counter.usage.get('total', 0)

            # Remove last 'count' messages and replace with summary
            self.agent.conversation_history = self.agent.conversation_history[:-count]
            self.agent.conversation_history.append({
                'role': 'assistant',
                'content': replacement
            })

            # Recalculate tokens
            self.agent.token_counter.count_messages(self.agent.conversation_history)
            tokens_after = token_counter.usage.get('total', 0)
            tokens_saved = tokens_before - tokens_after

            return {
                'success': True,
                'messages_removed': count,
                'messages_current': len(self.agent.conversation_history),
                'tokens_before': tokens_before,
                'tokens_after': tokens_after,
                'tokens_saved': tokens_saved,
                'current_usage_pct': (tokens_after / max_tokens * 100) if max_tokens > 0 else 0
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
