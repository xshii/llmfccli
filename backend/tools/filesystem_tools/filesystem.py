# -*- coding: utf-8 -*-
"""
Filesystem tools - 函数式接口（向后兼容层）

此模块提供函数式接口，内部委托给类实现。
新代码应直接使用类版本：ViewFileTool, EditFileTool 等。
"""

from typing import Any, Dict, Optional, Tuple

from backend.tools.base import FileSystemError

# 导出 FileSystemError 供外部使用
__all__ = ['FileSystemError', 'view_file', 'edit_file', 'create_file', 'grep_search', 'list_dir']


def view_file(
    path: str,
    line_range: Optional[Tuple[int, int]] = None,
    project_root: Optional[str] = None
) -> Dict[str, Any]:
    """读取文件内容（向后兼容接口）"""
    import os

    # 解析路径
    if not os.path.isabs(path) and project_root:
        full_path = os.path.join(project_root, path)
    else:
        full_path = path
    full_path = os.path.abspath(full_path)

    # 安全检查
    if project_root:
        project_root_abs = os.path.abspath(project_root)
        if not full_path.startswith(project_root_abs):
            raise FileSystemError(f"Path {path} is outside project root")

    if not os.path.exists(full_path):
        raise FileSystemError(f"File not found: {path}")

    if not os.path.isfile(full_path):
        raise FileSystemError(f"Not a file: {path}")

    # 读取文件
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        raise FileSystemError(f"Failed to read file {path}: {e}")

    total_lines = len(lines)

    # 处理行范围
    if line_range:
        start, end = line_range
        if end == -1:
            end = total_lines
        if start < 1 or start > total_lines:
            raise FileSystemError(f"Invalid start line {start}")
        if end < start or end > total_lines:
            raise FileSystemError(f"Invalid end line {end}")
        selected_lines = lines[start - 1:end]
        content = ''.join(selected_lines)
        actual_range = (start, end)
    else:
        content = ''.join(lines)
        actual_range = (1, total_lines)

    return {
        'content': content,
        'path': full_path,
        'total_lines': total_lines,
        'line_range': actual_range,
    }


def edit_file(
    path: str,
    old_str: str,
    new_str: str,
    project_root: Optional[str] = None,
    confirm: bool = True,
    show_preview: bool = True
) -> Dict[str, Any]:
    """编辑文件（向后兼容接口）"""
    from .edit_file import EditFileTool
    tool = EditFileTool(project_root=project_root)

    # 旧接口支持 confirm 参数，新类版本不支持
    # 如果 confirm=False，直接执行
    if not confirm:
        result = tool.execute(path=path, old_str=old_str, new_str=new_str)
        if hasattr(result, 'ok'):
            return {'success': result.ok, 'message': result.output, 'mode': 'direct'}
        return result

    # confirm=True 时，显示预览
    if show_preview:
        tool.get_diff_preview(path=path, old_str=old_str, new_str=new_str)

    result = tool.execute(path=path, old_str=old_str, new_str=new_str)
    if hasattr(result, 'ok'):
        return {'success': result.ok, 'message': result.output, 'mode': 'confirm'}
    return result


def create_file(
    path: str,
    content: str,
    project_root: Optional[str] = None,
    auto_mkdir: bool = True
) -> Dict[str, Any]:
    """创建文件（向后兼容接口）"""
    from .create_file import CreateFileTool
    tool = CreateFileTool(project_root=project_root)
    result = tool.execute(path=path, content=content)
    if hasattr(result, 'ok'):
        return {'success': result.ok, 'message': result.output, 'path': path}
    return result


def grep_search(
    pattern: str,
    scope: str,
    project_root: Optional[str] = None,
    max_results: int = 50,
    file_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """搜索文件内容（向后兼容接口）

    优先使用 ripgrep，不可用时回退到 Python regex。
    """
    import os
    import re

    # 解析 scope 路径
    if not os.path.isabs(scope) and project_root:
        scope = os.path.join(project_root, scope)
    scope = os.path.abspath(scope)

    # 安全检查
    if project_root:
        project_root_abs = os.path.abspath(project_root)
        if not scope.startswith(project_root_abs):
            raise FileSystemError(f"Scope {scope} is outside project root")

    if not os.path.exists(scope):
        raise FileSystemError(f"Scope not found: {scope}")

    # 尝试使用 ripgrep
    try:
        from .grep_search import GrepSearchTool
        tool = GrepSearchTool(project_root=project_root)
        result = tool.execute(pattern=pattern, scope=scope, file_pattern=file_pattern)
        if hasattr(result, 'ok'):
            matches = []
            if result.ok and result.output:
                for line in result.output.split('\n'):
                    if ':' in line and not line.startswith('...'):
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            matches.append({
                                'file': parts[0],
                                'line': int(parts[1]) if parts[1].isdigit() else 0,
                                'content': parts[2].strip()
                            })
            return {
                'success': result.ok,
                'matches': matches,
                'pattern': pattern,
                'truncated': len(matches) >= max_results
            }
        return result
    except FileSystemError as e:
        if "ripgrep" not in str(e).lower() and "rg" not in str(e).lower():
            raise
        # ripgrep 不可用，回退到 Python regex

    # Python regex 回退实现
    try:
        regex = re.compile(pattern)
    except re.error as e:
        raise FileSystemError(f"Invalid regex pattern: {e}")

    matches = []
    files_searched = 0

    if os.path.isfile(scope):
        search_files = [scope]
    else:
        search_files = []
        for root, dirs, files in os.walk(scope):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'build', '__pycache__']]
            for file in files:
                if file.startswith('.'):
                    continue
                if file_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(file, file_pattern):
                        continue
                search_files.append(os.path.join(root, file))

    for file_path in search_files:
        files_searched += 1
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append({
                            'file': file_path,
                            'line': line_num,
                            'content': line.rstrip(),
                        })
                        if len(matches) >= max_results:
                            break
        except Exception:
            continue
        if len(matches) >= max_results:
            break

    return {
        'success': True,
        'matches': matches,
        'total_files_searched': files_searched,
        'truncated': len(matches) >= max_results,
        'pattern': pattern,
    }


def list_dir(
    path: str,
    project_root: Optional[str] = None,
    max_depth: int = 3
) -> Dict[str, Any]:
    """列出目录内容（向后兼容接口）"""
    from .list_dir import ListDirTool
    tool = ListDirTool(project_root=project_root)
    result = tool.execute(path=path, max_depth=max_depth)
    if hasattr(result, 'ok'):
        return {'success': result.ok, 'output': result.output, 'path': path}
    return result
