# -*- coding: utf-8 -*-
"""
Filesystem tools for reading, writing, and searching files
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any


class FileSystemError(Exception):
    """Base exception for filesystem operations"""
    pass


def view_file(path: str, line_range: Optional[Tuple[int, int]] = None, 
              project_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Read file contents with optional line range
    
    Args:
        path: File path (absolute or relative to project_root)
        line_range: Optional (start_line, end_line), 1-indexed inclusive
        project_root: Project root directory
        
    Returns:
        Dict with 'content', 'path', 'total_lines', 'line_range'
    """
    # Resolve path
    if not os.path.isabs(path) and project_root:
        path = os.path.join(project_root, path)
    
    path = os.path.abspath(path)
    
    # Security check - prevent path traversal
    if project_root:
        project_root = os.path.abspath(project_root)
        if not path.startswith(project_root):
            raise FileSystemError(f"Path {path} is outside project root {project_root}")
    
    # Check file exists
    if not os.path.exists(path):
        raise FileSystemError(f"File not found: {path}")
    
    if not os.path.isfile(path):
        raise FileSystemError(f"Not a file: {path}")
    
    # Read file
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        raise FileSystemError(f"Failed to read file {path}: {e}")
    
    total_lines = len(lines)
    
    # Apply line range
    if line_range:
        start, end = line_range
        # Handle negative indices
        if end == -1:
            end = total_lines
        
        # Validate range
        if start < 1 or start > total_lines:
            raise FileSystemError(f"Invalid start line {start} (file has {total_lines} lines)")
        
        if end < start or end > total_lines:
            raise FileSystemError(f"Invalid end line {end}")
        
        # Extract lines (convert to 0-indexed)
        selected_lines = lines[start-1:end]
        content = ''.join(selected_lines)
        actual_range = (start, end)
    else:
        content = ''.join(lines)
        actual_range = (1, total_lines)
    
    return {
        'content': content,
        'path': path,
        'total_lines': total_lines,
        'line_range': actual_range,
    }


def edit_file(path: str, old_str: str, new_str: str,
              project_root: Optional[str] = None,
              confirm: bool = True,
              show_preview: bool = True) -> Dict[str, Any]:
    """
    Edit file using str_replace pattern (must be unique)

    行为模式：
    - confirm=True, show_preview=True: 显示 diff，等待确认（VSCode 模式下使用 GUI）
    - confirm=False: 直接修改，无交互（自动化、脚本模式）
    - 自动检测 VSCode 环境，提供最佳体验

    Args:
        path: File path
        old_str: String to replace (must appear exactly once)
        new_str: Replacement string
        project_root: Project root directory
        confirm: 是否需要用户确认（False=直接修改）
        show_preview: 是否显示预览（仅当 confirm=True 时有效）

    Returns:
        Dict with 'success', 'path', 'mode', 'message'
    """
    # Resolve path
    if not os.path.isabs(path) and project_root:
        full_path = os.path.join(project_root, path)
    else:
        full_path = path

    full_path = os.path.abspath(full_path)

    # Security check
    if project_root:
        project_root = os.path.abspath(project_root)
        if not full_path.startswith(project_root):
            raise FileSystemError(f"Path {path} is outside project root")

    # Check file exists
    if not os.path.exists(full_path):
        raise FileSystemError(f"File not found: {path}")

    # Read file
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        raise FileSystemError(f"Failed to read file {path}: {e}")

    # Check if old_str exists
    if old_str not in content:
        raise FileSystemError(f"String not found in file: {old_str[:50]}...")

    # Check uniqueness
    count = content.count(old_str)
    if count > 1:
        raise FileSystemError(f"String appears {count} times (must be unique): {old_str[:50]}...")

    # Generate new content
    new_content = content.replace(old_str, new_str)

    # 检测 VSCode 模式
    from backend.rpc.client import is_vscode_mode
    use_vscode = is_vscode_mode()

    # 模式 1: 需要确认（默认，安全模式）
    if confirm:
        if use_vscode and show_preview:
            # VSCode 模式：使用 GUI diff 和确认
            return _edit_with_vscode_preview(
                full_path, content, new_content, old_str, new_str
            )
        elif show_preview:
            # CLI 模式：显示文本预览
            return _edit_with_cli_preview(
                full_path, content, new_content, old_str, new_str
            )
        else:
            # 只确认，不预览
            return _edit_with_confirmation(
                full_path, new_content, old_str, new_str
            )

    # 模式 2: 直接修改（快速模式，无交互）
    else:
        return _edit_direct(full_path, new_content, old_str, new_str)


def _edit_with_vscode_preview(path: str, original: str, new_content: str,
                              old_str: str, new_str: str) -> Dict[str, Any]:
    """VSCode 模式：显示 diff 预览 + GUI 确认 + API 应用"""
    from backend.tools import vscode

    try:
        # 1. 显示 diff
        diff_result = vscode.show_diff(
            title=f"Edit: {os.path.basename(path)}",
            original_path=path,
            modified_content=new_content
        )

        if not diff_result.get('success'):
            raise FileSystemError(f"Failed to show diff: {diff_result.get('error')}")

        # 2. TODO: 添加确认对话框
        # confirmed = vscode.show_confirmation(...)
        # 暂时假设用户确认
        confirmed = True

        if not confirmed:
            return {
                'success': False,
                'message': 'Edit cancelled by user',
                'mode': 'vscode'
            }

        # 3. 通过 VSCode API 应用（支持 undo/redo）
        apply_result = vscode.apply_changes(path, old_str, new_str)

        if apply_result.get('success'):
            return {
                'success': True,
                'path': path,
                'mode': 'vscode',
                'message': f"Applied changes via VSCode API"
            }
        else:
            raise FileSystemError(f"Failed to apply changes: {apply_result.get('error')}")

    except Exception as e:
        # VSCode 失败，回退到直接修改
        import sys
        print(f"⚠️  VSCode integration error: {e}", file=sys.stderr)
        print(f"   Falling back to direct edit", file=sys.stderr)
        return _edit_direct(path, new_content, old_str, new_str)


def _edit_with_cli_preview(path: str, original: str, new_content: str,
                           old_str: str, new_str: str) -> Dict[str, Any]:
    """CLI 模式：显示文本预览 + 等待确认"""
    print(f"\n{'=' * 60}")
    print(f"📝 准备编辑: {path}")
    print(f"{'=' * 60}")
    print(f"\n将要替换:")
    print(f"[-] {old_str[:100]}{'...' if len(old_str) > 100 else ''}")
    print(f"\n替换为:")
    print(f"[+] {new_str[:100]}{'...' if len(new_str) > 100 else ''}")
    print(f"\n{'=' * 60}")

    response = input("确认应用更改? (y/n): ").strip().lower()
    if response != 'y':
        return {
            'success': False,
            'message': 'Edit cancelled by user',
            'mode': 'cli'
        }

    return _edit_direct(path, new_content, old_str, new_str)


def _edit_with_confirmation(path: str, new_content: str,
                           old_str: str, new_str: str) -> Dict[str, Any]:
    """简单确认，不显示预览"""
    response = input(f"确认编辑 {os.path.basename(path)}? (y/n): ").strip().lower()
    if response != 'y':
        return {
            'success': False,
            'message': 'Edit cancelled by user',
            'mode': 'simple'
        }

    return _edit_direct(path, new_content, old_str, new_str)


def _edit_direct(path: str, new_content: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """直接修改文件，无交互"""
    try:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)

        return {
            'success': True,
            'path': path,
            'mode': 'direct',
            'old_str': old_str[:100] + ('...' if len(old_str) > 100 else ''),
            'new_str': new_str[:100] + ('...' if len(new_str) > 100 else ''),
            'changes': len(new_str) - len(old_str),
            'message': f"Successfully edited {os.path.basename(path)}"
        }
    except Exception as e:
        raise FileSystemError(f"Failed to write file {path}: {e}")


def create_file(path: str, content: str, 
                project_root: Optional[str] = None,
                auto_mkdir: bool = True) -> Dict[str, Any]:
    """
    Create new file with content
    
    Args:
        path: File path
        content: File content
        project_root: Project root directory
        auto_mkdir: Automatically create parent directories
        
    Returns:
        Dict with 'success', 'path', 'size'
    """
    # Resolve path
    if not os.path.isabs(path) and project_root:
        path = os.path.join(project_root, path)
    
    path = os.path.abspath(path)
    
    # Security check
    if project_root:
        project_root = os.path.abspath(project_root)
        if not path.startswith(project_root):
            raise FileSystemError(f"Path {path} is outside project root")
    
    # Check if file already exists
    if os.path.exists(path):
        raise FileSystemError(f"File already exists: {path}")
    
    # Create parent directories
    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        if auto_mkdir:
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except Exception as e:
                raise FileSystemError(f"Failed to create directory {parent_dir}: {e}")
        else:
            raise FileSystemError(f"Directory does not exist: {parent_dir}")
    
    # Write file
    try:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
    except Exception as e:
        raise FileSystemError(f"Failed to create file {path}: {e}")
    
    return {
        'success': True,
        'path': path,
        'size': len(content),
    }


def grep_search(pattern: str, scope: str,
                project_root: Optional[str] = None,
                max_results: int = 50,
                file_pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for pattern in files (regex supported)

    Args:
        pattern: Search pattern (regex)
        scope: Search scope directory (required, e.g., ".", "src/", "backend/")
        project_root: Project root directory
        max_results: Maximum number of results
        file_pattern: Optional file pattern filter (e.g., "*.cpp")

    Returns:
        Dict with 'matches', 'total_files_searched', 'truncated'
    """
    # Resolve scope
    if not os.path.isabs(scope) and project_root:
        scope = os.path.join(project_root, scope)
    
    scope = os.path.abspath(scope)
    
    # Security check
    if project_root:
        project_root = os.path.abspath(project_root)
        if not scope.startswith(project_root):
            raise FileSystemError(f"Scope {scope} is outside project root")
    
    # Check scope exists
    if not os.path.exists(scope):
        raise FileSystemError(f"Scope not found: {scope}")
    
    # Compile regex
    try:
        regex = re.compile(pattern)
    except re.error as e:
        raise FileSystemError(f"Invalid regex pattern: {e}")
    
    # Search
    matches = []
    files_searched = 0
    
    # Determine if scope is file or directory
    if os.path.isfile(scope):
        search_files = [scope]
    else:
        search_files = []
        for root, dirs, files in os.walk(scope):
            # Skip hidden directories and common build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'build', '__pycache__']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                # Apply file pattern filter
                if file_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(file, file_pattern):
                        continue
                
                search_files.append(os.path.join(root, file))
    
    # Search in files
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
            # Skip files that can't be read
            continue
        
        if len(matches) >= max_results:
            break
    
    return {
        'matches': matches,
        'total_files_searched': files_searched,
        'truncated': len(matches) >= max_results,
        'pattern': pattern,
    }


def list_dir(path: str, project_root: Optional[str] = None,
             max_depth: int = 3) -> Dict[str, Any]:
    """
    List directory contents recursively
    
    Args:
        path: Directory path
        project_root: Project root directory
        max_depth: Maximum depth to traverse
        
    Returns:
        Dict with 'tree', 'total_files', 'total_dirs'
    """
    # Resolve path
    if not os.path.isabs(path) and project_root:
        path = os.path.join(project_root, path)
    
    path = os.path.abspath(path)
    
    # Security check
    if project_root:
        project_root = os.path.abspath(project_root)
        if not path.startswith(project_root):
            raise FileSystemError(f"Path {path} is outside project root")
    
    # Check exists
    if not os.path.exists(path):
        raise FileSystemError(f"Path not found: {path}")
    
    if not os.path.isdir(path):
        raise FileSystemError(f"Not a directory: {path}")
    
    # Build tree
    total_files = 0
    total_dirs = 0
    
    def build_tree(dir_path: str, depth: int) -> List[Dict[str, Any]]:
        nonlocal total_files, total_dirs
        
        if depth > max_depth:
            return []
        
        items = []
        
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return items
        
        for entry in entries:
            # Skip hidden files
            if entry.startswith('.'):
                continue
            
            full_path = os.path.join(dir_path, entry)
            
            if os.path.isdir(full_path):
                # Skip common build/cache directories
                if entry in ['node_modules', 'build', '__pycache__', '.git']:
                    continue
                
                total_dirs += 1
                children = build_tree(full_path, depth + 1)
                items.append({
                    'name': entry,
                    'type': 'directory',
                    'children': children,
                })
            else:
                total_files += 1
                items.append({
                    'name': entry,
                    'type': 'file',
                    'size': os.path.getsize(full_path),
                })
        
        return items
    
    tree = build_tree(path, 0)
    
    return {
        'tree': tree,
        'total_files': total_files,
        'total_dirs': total_dirs,
        'path': path,
    }
