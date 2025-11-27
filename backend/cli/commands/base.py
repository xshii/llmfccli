# -*- coding: utf-8 -*-
"""
命令基类

定义所有斜杠命令的基类接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from rich.console import Console


class Command(ABC):
    """命令基类"""

    def __init__(self, console: Console):
        """
        初始化命令

        Args:
            console: Rich Console 实例
        """
        self.console = console

    @abstractmethod
    def execute(self, args: List[str]) -> bool:
        """
        执行命令

        Args:
            args: 命令参数列表

        Returns:
            True 继续运行，False 退出程序
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """命令名称（不含 /）"""
        pass

    @property
    def aliases(self) -> List[str]:
        """命令别名列表"""
        return []

    @property
    def description(self) -> str:
        """命令描述"""
        return ""

    def show_help(self):
        """显示命令帮助"""
        self.console.print(f"[yellow]用法: /{self.name}[/yellow]")
        if self.description:
            self.console.print(self.description)
