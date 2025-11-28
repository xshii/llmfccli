# -*- coding: utf-8 -*-
"""
CLI 模块 - 重构版

提供交互式命令行界面和相关工具
"""

# 延迟导入以避免循环依赖和减少启动时间
def __getattr__(name):
    """延迟导入模块成员"""
    if name == 'CLI':
        from .main import CLI
        return CLI
    elif name == 'PathUtils':
        from .path_utils import PathUtils
        return PathUtils
    elif name == 'ToolOutputManager':
        from .output_manager import ToolOutputManager
        return ToolOutputManager
    elif name == 'main':
        from .main import main
        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'CLI',
    'PathUtils',
    'ToolOutputManager',
    'main',
]
