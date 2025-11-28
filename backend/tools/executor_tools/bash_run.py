# -*- coding: utf-8 -*-
"""
BashRun Tool - 执行 bash 命令
"""

import shlex
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from .bash_session import BashSession
from .exceptions import ExecutorError


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
        session = BashSession(self.project_root, timeout=timeout)
        try:
            return session.execute(command, timeout=timeout)
        finally:
            session.close()

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


# Backward compatibility: function API
def bash_run(command: str,
             project_root: str,
             timeout: int = 60,
             whitelist: Optional[List[str]] = None,
             _session_id: Optional[str] = None,
             verbose: bool = True) -> Dict[str, Any]:
    """
    Execute bash command with security checks (backward compatible function API)

    Args:
        command: Command to execute
        project_root: Project root directory
        timeout: Timeout in seconds
        whitelist: Allowed command prefixes (security)
        session_id: Optional session ID (ignored, kept for compatibility)
        verbose: Print execution status

    Returns:
        Dict with stdout, stderr, return_code, duration
    """
    # Default whitelist from config
    if whitelist is None:
        whitelist = [
            'cmake', 'make', 'g++', 'clang++', 'gcc', 'clang',
            'ctest', 'git', 'mkdir', 'cd', 'ls', 'cat',
            'echo', 'pwd', 'which', 'find', 'grep',
            'python', 'python3', 'pip', 'pip3', 'rm'
        ]

    # Security check: validate command against whitelist
    command_parts = shlex.split(command)
    if not command_parts:
        raise ExecutorError("Empty command")

    base_command = command_parts[0]

    # Allow full paths if basename matches whitelist
    if '/' in base_command:
        base_command = Path(base_command).name

    # Check whitelist
    if not any(base_command.startswith(allowed) for allowed in whitelist):
        raise ExecutorError(
            f"Command '{base_command}' not in whitelist. "
            f"Allowed: {', '.join(whitelist)}"
        )

    # Print verbose output
    if verbose:
        print(f"\n[TODO] 执行命令: {command}")
        print(f"[TODO] 工作目录: {project_root}")
        print(f"[TODO] 超时设置: {timeout}秒")

    # Execute using BashRunTool
    tool = BashRunTool(project_root=project_root)
    result = tool.execute(command=command, timeout=timeout)

    # Add extra fields for compatibility
    result['command'] = command
    result['project_root'] = str(project_root)

    # Print result
    if verbose:
        status = "✓ 成功" if result['success'] else "✗ 失败"
        print(f"[TODO] 执行结果: {status} (耗时: {result['duration']:.2f}秒)")
        if result['return_code'] != 0:
            print(f"[TODO] 返回码: {result['return_code']}")

    return result
