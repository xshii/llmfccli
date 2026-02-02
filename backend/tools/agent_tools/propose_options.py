# -*- coding: utf-8 -*-
"""
ProposeOptions Tool - 向用户提出方案选择
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class OptionItem(BaseModel):
    """单个选项"""
    id: str = Field(description="Option ID (A/B/C/D/E)")
    description: str = Field(description="Option description")


class ProposeOptionsParams(BaseModel):
    """ProposeOptions 工具参数"""
    question: str = Field(description="Question to ask the user")
    options: List[OptionItem] = Field(description="List of 2-5 options with id and description")


class ProposeOptionsTool(BaseTool):
    """向用户提出方案选择，获取用户决策"""

    def __init__(self, project_root=None, agent=None, **dependencies):
        super().__init__(project_root, **dependencies)
        self.agent = agent

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
    def priority(self) -> int:
        return 20

    @property
    def skip_confirmation(self) -> bool:
        # 交互工具，本身就需要用户输入，无需额外确认
        return True

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
                    "List of 2-5 options. Each option has 'id' (A/B/C/D/E) and 'description'. "
                    "Example: [{\"id\": \"A\", \"description\": \"Read file content\"}, "
                    "{\"id\": \"B\", \"description\": \"Modify code\"}]"
                ),
                'zh': (
                    "2-5个选项，每个选项包含 'id' (A/B/C/D/E) 和 'description'。"
                    "示例: [{\"id\": \"A\", \"description\": \"读取文件内容\"}, "
                    "{\"id\": \"B\", \"description\": \"修改代码\"}]"
                )
            }
        }

    def execute(self, question: str, options: List[Dict[str, str]]) -> Dict[str, Any]:
        """执行方案选择 - 直接通过 input() 获取用户输入

        Args:
            question: 问题文本
            options: 选项列表，每个选项是 {"id": "A", "description": "描述"}
        """
        if not options or len(options) < 2:
            return {
                'success': False,
                'error': 'At least 2 options required'
            }

        if len(options) > 5:
            options = options[:5]  # 限制最多 5 个选项

        # 构建选项 ID 到描述的映射
        option_map = {}
        for opt in options:
            opt_id = opt.get('id', '').upper()
            opt_desc = opt.get('description', '')
            if opt_id and opt_desc:
                option_map[opt_id] = opt_desc

        # 添加 "No" 选项 - 让用户告诉 AI 想怎么做
        option_map['N'] = 'No, 让我告诉你我想怎么做'

        valid_ids = list(option_map.keys())

        try:
            # 显示问题和选项
            print(f"\n{'='*50}")
            print(f"📋 {question}")
            print(f"{'='*50}")
            for opt_id, opt_desc in option_map.items():
                print(f"  {opt_id}: {opt_desc}")
            print()

            # 获取用户输入
            while True:
                choice = input(f"请选择 ({'/'.join(valid_ids)}): ").strip().upper()

                if choice == 'N':
                    # 用户选择 No - 告诉 AI 想怎么做
                    user_input = input("请告诉我你想怎么做: ").strip()
                    if user_input:
                        return {
                            'success': True,
                            'selected': 'N',
                            'is_reject': True,
                            'user_feedback': user_input,
                            'options': options
                        }
                    else:
                        print("请输入你的想法")
                        continue

                elif choice in valid_ids:
                    # 用户选择了预设选项
                    return {
                        'success': True,
                        'selected': choice,
                        'selected_description': option_map.get(choice, ''),
                        'is_reject': False,
                        'user_feedback': None,
                        'options': options
                    }
                else:
                    print(f"无效选择，请输入 {'/'.join(valid_ids)}")

        except KeyboardInterrupt:
            return {
                'success': False,
                'error': 'User cancelled'
            }
        except EOFError:
            # 非交互模式（如测试），返回第一个选项
            first_opt = options[0] if options else {}
            return {
                'success': True,
                'selected': first_opt.get('id', 'A').upper(),
                'selected_description': first_opt.get('description', ''),
                'is_reject': False,
                'user_feedback': None,
                'options': options,
                'warning': 'Non-interactive mode, auto-selected first option'
            }
