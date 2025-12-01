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
                "Present options to user for decision making. "
                "ONLY USE when user intent is GENUINELY UNCLEAR. "
                "Use cases: "
                "(1) User asks 'what can you do' or provides NO specific task; "
                "(2) Task has multiple EQUALLY valid approaches requiring user choice; "
                "(3) User provides ambiguous request like 'help me with this file' without details. "
                "DO NOT USE if user has specified a clear task (e.g., 'add timeout', 'fix bugs', 'generate tests'). "
                "If you've read a file and user task is clear, CONTINUE execution - don't ask. "
                "Always includes 'Other' option for custom input. Returns selected option ID."
            ),
            'zh': (
                "向用户提出选项以获取决策。"
                "仅在用户意图真正不明确时使用。"
                "使用场景: "
                "(1) 用户询问'你能做什么'或完全未提供具体任务; "
                "(2) 任务有多种同样有效的方案，需要用户选择; "
                "(3) 用户提供模糊请求如'帮我处理这个文件'但没有细节。"
                "如果用户已指定明确任务（如'添加超时'、'修复bug'、'生成测试'），不要使用此工具。"
                "如果已读取文件且用户任务明确，继续执行 - 不要询问。"
                "自动包含'其他'选项供自定义输入。返回所选选项 ID。"
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
                'en': "Question to ask the user, e.g. 'What would you like me to do with this file?'",
                'zh': "向用户提出的问题，如'您希望我对这个文件做什么？'"
            },
            'options': {
                'en': (
                    "List of options in format ['A: Title - Description', 'B: Title - Description']. "
                    "2-5 options. Example: "
                    "['A: View - Read and explain the file', "
                    "'B: Edit - Modify specific parts', "
                    "'C: Fix - Find and fix bugs', "
                    "'D: Explain - Explain how it works']"
                ),
                'zh': (
                    "选项列表，格式 ['A: 标题 - 描述', 'B: 标题 - 描述']，2-5个选项。"
                    "示例: ['A: 查看 - 阅读并解释文件内容', "
                    "'B: 编辑 - 修改特定部分', "
                    "'C: 修复 - 查找并修复bug', "
                    "'D: 解释 - 解释其工作原理']"
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
