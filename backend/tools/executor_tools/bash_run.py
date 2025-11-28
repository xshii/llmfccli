# -*- coding: utf-8 -*-
"""
BashRun Tool - 执行 bash 命令
"""

import subprocess
import time
from typing import Dict, Any
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool


class BashRunParams(BaseModel):
    """BashRun 工具参数"""
    command: str = Field(description="要执行的 bash 命令")
    timeout: int = Field(60, description="超时时间（秒，默认 60）")


class BashRunTool(BaseTool):
    """执行 bash 命令工具"""

    @property
    def name(self) -> str:
        return "bash_run"

    @property
    def description(self) -> str:
        return "Execute bash command with security checks and timeout"

    @property
    def category(self) -> str:
        return "executor"

    @property
    def parameters_model(self):
        return BashRunParams

    def execute(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """执行 bash 命令"""
        start_time = time.time()

        try:
            result = subprocess.run(
                ['bash', '-c', command],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration = time.time() - start_time

            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'duration': duration,
                'success': result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'return_code': -1,
                'duration': time.time() - start_time,
                'success': False,
                'error': 'timeout',
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'duration': time.time() - start_time,
                'success': False,
                'error': str(e),
            }

    def get_confirmation_signature(self, arguments: Dict[str, Any]) -> str:
        """按基础命令分组确认，例如 bash_run:ls, bash_run:git"""
        command = arguments.get('command', '')
        # 提取基础命令（第一个词）
        base_cmd = command.split()[0] if command else ''
        return f"{self.name}:{base_cmd}"

    def is_dangerous_operation(self, arguments: Dict[str, Any]) -> bool:
        """检查命令是否危险"""
        command = arguments.get('command', '')

        # 危险命令模式
        dangerous_patterns = [
            'rm -rf',
            'rm -r /',
            'chmod -R 777',
            'chown -R',
            '> /dev/',
            'mkfs',
            'dd if=',
            ':(){:|:&};:',  # fork bomb
        ]

        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return True

        return False
