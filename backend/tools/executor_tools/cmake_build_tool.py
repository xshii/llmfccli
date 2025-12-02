# -*- coding: utf-8 -*-
"""
CmakeBuildTool - CMake 构建工具类
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

from backend.tools.base import BaseTool
from .bash_session import BashSession


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
    def priority(self) -> int:
        return 60

    @property
    def parameters_model(self):
        return CmakeBuildParams

    def execute(self, build_dir: str = "build", config: str = "Release",
                target: Optional[str] = None, clean: bool = False) -> Dict[str, Any]:
        """执行 CMake 构建"""
        build_path = Path(self.project_root) / build_dir
        session = BashSession(self.project_root, timeout=300)
        results: List[tuple] = []

        try:
            # Clean if requested
            if clean and build_path.exists():
                result = session.execute(f"rm -rf {build_dir}", timeout=10)
                results.append(('clean', result))

            # Create build directory
            if not build_path.exists():
                result = session.execute(f"mkdir -p {build_dir}", timeout=5)
                results.append(('mkdir', result))

            # Configure
            result = session.execute(
                f"cmake -S . -B {build_dir} -DCMAKE_BUILD_TYPE={config}",
                timeout=60
            )
            results.append(('configure', result))

            if not result['success']:
                return {
                    'success': False,
                    'stage': 'configure',
                    'error': result['stderr'] or result['stdout'],
                    'results': results,
                }

            # Build
            build_cmd = f"cmake --build {build_dir}"
            if target:
                build_cmd += f" --target {target}"

            result = session.execute(build_cmd, timeout=300)
            results.append(('build', result))

            if not result['success']:
                return {
                    'success': False,
                    'stage': 'build',
                    'error': result['stderr'] or result['stdout'],
                    'results': results,
                }

            return {
                'success': True,
                'build_dir': str(build_path),
                'config': config,
                'results': results,
            }

        finally:
            session.close()


# Backward compatibility: function API
def cmake_build(project_root: str,
                build_dir: str = "build",
                config: str = "Release",
                target: Optional[str] = None,
                clean: bool = False,
                _verbose: bool = True) -> Dict[str, Any]:
    """
    Build project with CMake (backward compatible function API)

    Args:
        project_root: Project root directory
        build_dir: Build directory name
        config: Build configuration (Debug/Release)
        target: Optional specific target to build
        clean: Clean before building
        verbose: Print execution status (ignored, kept for compatibility)

    Returns:
        Build result dict
    """
    tool = CmakeBuildTool(project_root=project_root)
    return tool.execute(build_dir=build_dir, config=config, target=target, clean=clean)
