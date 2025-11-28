# -*- coding: utf-8 -*-
"""
CmakeBuildTool - CMake 构建工具类
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from .executor import cmake_build


class CmakeBuildParams(BaseModel):
    """CMake 构建参数"""
    build_dir: str = Field(default="build", description="构建目录名称")
    config: str = Field(default="Release", description="构建配置 (Debug/Release)")
    target: Optional[str] = Field(default=None, description="可选的特定目标")
    clean: bool = Field(default=False, description="构建前是否清理")


class CmakeBuildTool(BaseTool):
    """CMake 构建工具"""

    @property
    def name(self) -> str:
        return "cmake_build"

    @property
    def description(self) -> str:
        return "Build project with CMake"

    @property
    def category(self) -> str:
        return "executor"

    @property
    def parameters_model(self):
        return CmakeBuildParams

    def execute(self, build_dir: str = "build", config: str = "Release",
                target: Optional[str] = None, clean: bool = False) -> Dict[str, Any]:
        """执行 CMake 构建"""
        return cmake_build(
            project_root=self.project_root,
            build_dir=build_dir,
            config=config,
            target=target,
            clean=clean,
            verbose=False  # 类模式下不打印详细信息
        )
