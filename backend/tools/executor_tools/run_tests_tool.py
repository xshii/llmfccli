# -*- coding: utf-8 -*-
"""
RunTestsTool - 测试运行工具类
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from .executor import run_tests


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
    def parameters_model(self):
        return RunTestsParams

    def execute(self, build_dir: str = "build", test_pattern: Optional[str] = None,
                timeout: int = 120) -> Dict[str, Any]:
        """执行测试"""
        return run_tests(
            project_root=self.project_root,
            build_dir=build_dir,
            test_pattern=test_pattern,
            timeout=timeout,
            verbose=False
        )
