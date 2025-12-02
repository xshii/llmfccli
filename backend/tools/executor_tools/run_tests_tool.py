# -*- coding: utf-8 -*-
"""
RunTestsTool - 测试运行工具类
"""

import re
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from .bash_session import BashSession
from .exceptions import ExecutorError


class RunTestsParams(BaseModel):
    """测试运行参数"""
    build_dir: str = Field(default="build", description="构建目录名称")
    test_pattern: Optional[str] = Field(default=None, description="可选的测试名称模式")
    timeout: int = Field(default=120, description="超时时间（秒）")


class RunTestsTool(BaseTool):
    """测试运行工具"""

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def description(self) -> str:
        return "Run unit tests with ctest"

    @property
    def category(self) -> str:
        return "executor"

    @property
    def priority(self) -> int:
        return 35

    @property
    def parameters_model(self):
        return RunTestsParams

    def execute(self, build_dir: str = "build", test_pattern: Optional[str] = None,
                timeout: int = 120) -> Dict[str, Any]:
        """执行测试"""
        build_path = Path(self.project_root) / build_dir

        if not build_path.exists():
            raise ExecutorError(f"Build directory not found: {build_path}")

        # Build ctest command
        cmd = f"cd {build_dir} && ctest --output-on-failure"
        if test_pattern:
            cmd += f" -R {test_pattern}"

        session = BashSession(self.project_root, timeout=timeout)
        try:
            result = session.execute(cmd, timeout=timeout)

            # Parse test results
            stdout = result['stdout']
            passed, failed = self._parse_test_output(stdout)

            total = passed + failed
            success = result['success'] and failed == 0

            return {
                'success': success,
                'passed': passed,
                'failed': failed,
                'total': total,
                'output': stdout,
                'duration': result['duration'],
            }
        finally:
            session.close()

    def _parse_test_output(self, stdout: str) -> tuple:
        """Parse ctest output to extract pass/fail counts"""
        # Simple parsing: look for "X tests passed, Y tests failed"
        match = re.search(r'(\d+) tests? passed.*?(\d+) tests? failed', stdout)

        if match:
            return int(match.group(1)), int(match.group(2))

        # Try alternative format
        match = re.search(r'(\d+)/(\d+) Test', stdout)
        if match:
            passed = int(match.group(1))
            total = int(match.group(2))
            return passed, total - passed

        return 0, 0


# Backward compatibility: function API
def run_tests(project_root: str,
              build_dir: str = "build",
              test_pattern: Optional[str] = None,
              timeout: int = 120,
              _verbose: bool = True) -> Dict[str, Any]:
    """
    Run tests with ctest (backward compatible function API)

    Args:
        project_root: Project root directory
        build_dir: Build directory name
        test_pattern: Optional test name pattern
        timeout: Timeout in seconds
        verbose: Print execution status (ignored, kept for compatibility)

    Returns:
        Test result dict
    """
    tool = RunTestsTool(project_root=project_root)
    return tool.execute(build_dir=build_dir, test_pattern=test_pattern, timeout=timeout)
