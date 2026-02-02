# -*- coding: utf-8 -*-
"""
命令模式 (Command Pattern) - 工具调用
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ToolCommand:
    """工具调用命令"""
    tool_name: str
    arguments: Dict[str, Any]
    tool_call_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    result: Any = None
    executed: bool = False
    success: bool = False
    error: Optional[str] = None

    def execute(self, executor) -> Any:
        """执行命令"""
        try:
            self.result = executor.execute_tool(self.tool_name, self.arguments)
            self.executed = True
            self.success = self._is_success(self.result)
            return self.result
        except Exception as e:
            self.executed = True
            self.success = False
            self.error = str(e)
            self.result = {'success': False, 'error': str(e)}
            return self.result

    def _is_success(self, result: Any) -> bool:
        """判断执行是否成功"""
        if isinstance(result, dict):
            return result.get('success', True)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'tool_name': self.tool_name,
            'arguments': self.arguments,
            'tool_call_id': self.tool_call_id,
            'timestamp': self.timestamp.isoformat(),
            'executed': self.executed,
            'success': self.success,
            'error': self.error,
        }


class CommandHistory:
    """命令历史记录"""

    def __init__(self, max_size: int = 100):
        self.commands: List[ToolCommand] = []
        self.max_size = max_size

    def add(self, command: ToolCommand):
        """添加命令到历史"""
        self.commands.append(command)
        # 限制历史大小
        if len(self.commands) > self.max_size:
            self.commands = self.commands[-self.max_size:]

    def execute(self, command: ToolCommand, executor) -> Any:
        """执行命令并记录"""
        result = command.execute(executor)
        self.add(command)
        return result

    def get_last(self, n: int = 1) -> List[ToolCommand]:
        """获取最近 n 条命令"""
        return self.commands[-n:]

    def get_by_tool(self, tool_name: str) -> List[ToolCommand]:
        """获取指定工具的命令"""
        return [cmd for cmd in self.commands if cmd.tool_name == tool_name]

    def get_failed(self) -> List[ToolCommand]:
        """获取失败的命令"""
        return [cmd for cmd in self.commands if cmd.executed and not cmd.success]

    def get_successful(self) -> List[ToolCommand]:
        """获取成功的命令"""
        return [cmd for cmd in self.commands if cmd.executed and cmd.success]

    def clear(self):
        """清空历史"""
        self.commands.clear()

    def summary(self) -> Dict[str, Any]:
        """获取历史摘要"""
        executed = [cmd for cmd in self.commands if cmd.executed]
        return {
            'total': len(self.commands),
            'executed': len(executed),
            'successful': len([cmd for cmd in executed if cmd.success]),
            'failed': len([cmd for cmd in executed if not cmd.success]),
            'tools_used': list(set(cmd.tool_name for cmd in self.commands)),
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [cmd.to_dict() for cmd in self.commands]


class CommandFactory:
    """命令工厂"""

    @staticmethod
    def from_tool_call(tool_call: Dict[str, Any]) -> ToolCommand:
        """从工具调用创建命令"""
        import json

        tool_name = tool_call['function']['name']
        arguments = tool_call['function'].get('arguments', {})

        # 解析参数
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        tool_call_id = tool_call.get('id', f'call_{tool_name}')

        return ToolCommand(
            tool_name=tool_name,
            arguments=arguments,
            tool_call_id=tool_call_id
        )

    @staticmethod
    def from_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[ToolCommand]:
        """从工具调用列表创建命令列表"""
        return [CommandFactory.from_tool_call(tc) for tc in tool_calls]
