# -*- coding: utf-8 -*-
"""
ProposeOptions Tool - 向用户提出方案选择
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class ProposeOptionsParams(BaseModel):
    """ProposeOptions 工具参数"""
    question: str = Field(description="Question to ask the user")
    options: List[str] = Field(description="List of options, 2-5 items")


class ProposeOptionsTool(BaseTool):
    """向用户提出方案选择，获取用户决策"""

    def __init__(self, project_root=None, agent=None, **dependencies):
        super().__init__(project_root, **dependencies)
        self.agent = agent
        self._options_callback: Optional[Callable] = None

    def set_options_callback(self, callback: Callable[[str, List[str]], str]):
        """
        设置选项回调函数

        Args:
            callback: 函数签名 (question, options) -> selected
                      options 最后一个是 "X: 其他 - 输入自定义方案"
                      返回用户选择的选项（如 "A" 或用户输入的自定义文本）
        """
        self._options_callback = callback

    @property
    def name(self) -> str:
        return "propose_options"

    @property
    def description_i18n(self) -> Dict[str, str]:
        return {
            'en': (
                "Ask user for decision when intent is GENUINELY UNCLEAR. "
                "Use ONLY if: (1) No specific task provided; "
                "(2) Multiple equally valid approaches need user choice; "
                "(3) Ambiguous request without details. "
                "DO NOT use if task is clear (e.g., 'add timeout', 'fix bug'). "
                "Returns selected option ID (A/B/C/D or X for custom)."
            ),
            'zh': (
                "在意图真正不明确时询问用户决策。"
                "仅当: (1)无具体任务; (2)多种同等方案需选择; (3)模糊请求无细节时使用。"
                "任务明确时禁用（如'添加超时'、'修复bug'）。"
                "返回选项ID（A/B/C/D 或 X 表示自定义）。"
            )
        }

    @property
    def category(self) -> str:
        return "agent"

    @property
    def parameters_model(self):
        return ProposeOptionsParams

    def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
        return {
            'question': {
                'en': "The question to ask (clear and concise)",
                'zh': "向用户提出的问题（清晰简洁）"
            },
            'options': {
                'en': (
                    "List of 2-5 options in format: ['A: Action - Brief description', ...]. "
                    "Example: ['A: View - Read file content', 'B: Edit - Modify code', 'C: Fix - Find bugs']"
                ),
                'zh': (
                    "2-5个选项，格式: ['A: 动作 - 简述', ...]。"
                    "示例: ['A: 查看 - 读取内容', 'B: 编辑 - 修改代码', 'C: 修复 - 查找bug']"
                )
            }
        }

    def execute(self, question: str, options: List[str]) -> Dict[str, Any]:
        """执行方案选择"""
        if not options or len(options) < 2:
            return {
                'success': False,
                'error': 'At least 2 options required'
            }

        if len(options) > 5:
            options = options[:5]  # 限制最多 5 个选项

        # 添加"其他"选项
        other_option = "X: 其他 - 输入自定义方案"
        full_options = options + [other_option]

        if not self._options_callback:
            # 无回调时返回第一个选项（用于测试）
            return {
                'success': True,
                'selected': options[0].split(':')[0].strip(),
                'is_custom': False,
                'custom_text': None,
                'warning': 'No callback set, auto-selected first option'
            }

        try:
            # 调用回调获取用户选择
            result = self._options_callback(question, full_options)

            # 解析结果
            if result.upper() == 'X' or result.startswith('X:'):
                # 用户选择了"其他"，result 应该包含自定义文本
                # 回调应该返回 "X: 用户输入的内容"
                custom_text = result[2:].strip() if ':' in result else result
                return {
                    'success': True,
                    'selected': 'X',
                    'is_custom': True,
                    'custom_text': custom_text
                }
            else:
                # 用户选择了预设选项
                selected_id = result.split(':')[0].strip().upper()
                return {
                    'success': True,
                    'selected': selected_id,
                    'is_custom': False,
                    'custom_text': None
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
