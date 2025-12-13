# -*- coding: utf-8 -*-
"""
超链接生成工具模块

统一管理文件和工具的超链接生成逻辑：
- file:// 协议：大多数终端支持
- vscode:// 协议：VS Code 专用，支持行号跳转
- 无协议模式：仅显示原始路径（适用于不支持超链接的环境）

协议配置在 config/feature.yaml 中的 cli_output.hyperlink_protocol.protocol
"""

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .path_utils import PathUtils


# 工具注册器缓存
_tool_registry = None


def _get_hyperlink_protocol() -> str:
    """获取超链接协议配置，默认 'file'"""
    try:
        from backend.utils.feature import get_feature_value
        return get_feature_value("cli_output.hyperlink_protocol.protocol", "file")
    except Exception:
        return "file"


def _get_show_line_number() -> bool:
    """获取是否显示行号配置，默认 True"""
    try:
        from backend.utils.feature import get_feature_value
        return get_feature_value("cli_output.hyperlink_protocol.show_line_number", True)
    except Exception:
        return True


def _get_tool_registry():
    """获取全局工具注册器"""
    global _tool_registry
    if _tool_registry is None:
        try:
            from backend.agent.tools import registry
            _tool_registry = registry
        except Exception:
            pass
    return _tool_registry


def create_file_hyperlink(
    path: str,
    project_root: str,
    path_utils: Optional['PathUtils'] = None,
    line: Optional[int] = None,
    column: Optional[int] = None,
    max_display_length: int = 50
) -> str:
    """
    创建文件超链接

    根据 config/feature.yaml 中的 cli_output.hyperlink_protocol.protocol 配置：
    - "file"   : 使用 file:// 协议（默认）
    - "vscode" : 使用 vscode://file/ 协议（支持行号跳转）
    - "none"   : 不使用协议，仅显示原始路径

    Args:
        path: 文件路径（相对或绝对）
        project_root: 项目根目录
        path_utils: PathUtils 实例（用于路径压缩，可选）
        line: 行号（可选）
        column: 列号（可选）
        max_display_length: 显示路径的最大长度

    Returns:
        Rich markup 格式的超链接字符串，或纯文本路径
    """
    # 获取绝对路径
    if not os.path.isabs(path):
        abs_path = os.path.join(project_root, path)
    else:
        abs_path = path

    # 压缩路径用于显示
    if path_utils:
        display_path = path_utils.compress_path(path, max_length=max_display_length)
    else:
        # 简单截断
        display_path = path if len(path) <= max_display_length else '...' + path[-(max_display_length - 3):]

    # 获取协议配置
    protocol = _get_hyperlink_protocol()
    show_line = _get_show_line_number()

    # 构建显示文本（行号包含在内）
    display = display_path
    if show_line and line is not None:
        display += f":{line}"

    if protocol == "none":
        return display

    elif protocol == "vscode":
        # VS Code 协议：URI 中包含行号和列号
        uri = f"vscode://file{abs_path}"
        if line is not None:
            uri += f":{line}"
            if column is not None:
                uri += f":{column}"
        return f"[link={uri}]{display}[/link]"

    else:
        # 默认 file:// 协议
        file_uri = f"file://{abs_path}"
        return f"[link={file_uri}]{display}[/link]"


def create_tool_hyperlink(tool_name: str) -> str:
    """
    创建工具名称超链接（指向工具的 py 文件）

    根据 cli_output.hyperlink_protocol.protocol 配置选择协议

    Args:
        tool_name: 工具名称

    Returns:
        Rich markup 格式的超链接字符串
    """
    protocol = _get_hyperlink_protocol()

    # 无协议模式：直接返回工具名
    if protocol == "none":
        return f"[cyan bold]{tool_name}[/cyan bold]"

    try:
        registry = _get_tool_registry()
        # 访问内部的 dynamic_registry 获取工具元数据
        if registry and registry._dynamic_registry:
            dynamic_registry = registry._dynamic_registry
            if tool_name in dynamic_registry._tool_metadata:
                metadata = dynamic_registry._tool_metadata[tool_name]
                # 从 module_path 获取文件路径
                # 格式: backend.tools.filesystem_tools.view_file -> backend/tools/filesystem_tools/view_file.py
                module_path = metadata.module_path

                # 基于当前文件位置计算工具文件路径
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent.parent  # llmfccli/

                # 将 module_path 转换为文件路径
                file_rel_path = module_path.replace('.', '/') + '.py'
                tool_file = project_root / file_rel_path

                if tool_file.exists():
                    abs_path = str(tool_file.resolve())
                    # 根据配置选择协议
                    if protocol == "vscode":
                        uri = f"vscode://file{abs_path}"
                    else:
                        uri = f"file://{abs_path}"
                    return f"[link={uri}][cyan bold]{tool_name}[/cyan bold][/link]"
    except Exception:
        pass

    # 回退：无超链接
    return f"[cyan bold]{tool_name}[/cyan bold]"


def open_file_via_rpc(
    path: str,
    line: Optional[int] = None,
    column: Optional[int] = None
) -> bool:
    """
    通过 RPC 在 VS Code 中打开文件（支持行号跳转）

    仅在 VS Code 模式下有效。

    Args:
        path: 文件路径
        line: 行号（可选）
        column: 列号（可选）

    Returns:
        True 如果成功打开，False 如果不在 VS Code 模式或失败
    """
    try:
        from backend.rpc.client import is_vscode_mode
        if not is_vscode_mode():
            return False

        from backend.tools.vscode_tools.vscode import open_file
        result = open_file(path, line=line, column=column)
        return result.get('success', False)
    except Exception:
        return False
