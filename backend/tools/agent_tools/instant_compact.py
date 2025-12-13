# -*- coding: utf-8 -*-
"""
InstantCompact Tool - 即时压缩指定工具调用的结果
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class InstantCompactParams(BaseModel):
    """InstantCompact 工具参数"""
    tool_call_id: str = Field(description="要压缩的工具调用ID")
    summary: str = Field(description="该工具结果的摘要，保留关键信息")


class InstantCompactTool(BaseTool):
    """即时压缩指定工具结果"""

    def __init__(self, project_root=None, agent=None, **dependencies):
        super().__init__(project_root, **dependencies)
        self.agent = agent

    @property
    def name(self) -> str:
        return "instant_compact"

    @property
    def description(self) -> str:
        return ("Compress a previous tool result to save context space. "
                "Use after view_file to summarize file content - avoids re-reading the same file later. "
                "Especially useful when edit_file is denied and you need to retry with different parameters.")

    @property
    def category(self) -> str:
        return "agent"

    @property
    def priority(self) -> int:
        return 10

    @property
    def parameters_model(self):
        return InstantCompactParams

    def execute(self, tool_call_id: str, summary: str) -> Dict[str, Any]:
        """压缩指定工具结果"""
        if not self.agent:
            return {'success': False, 'error': 'Agent not available'}

        try:
            # 遍历历史找到对应的工具消息
            for msg in self.agent.conversation_history:
                if msg.get('role') == 'tool' and msg.get('tool_call_id') == tool_call_id:
                    original_content = msg['content']
                    original_len = len(original_content)

                    # 替换为摘要
                    msg['content'] = f"[摘要] {summary}"
                    new_len = len(msg['content'])

                    # 估算 token 节省（粗略按 4 字符/token）
                    tokens_saved = (original_len - new_len) // 4

                    return {
                        'success': True,
                        'tool_call_id': tool_call_id,
                        'original_chars': original_len,
                        'compressed_chars': new_len,
                        'tokens_saved_approx': max(0, tokens_saved)
                    }

            return {'success': False, 'error': f'tool_call_id "{tool_call_id}" not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}
