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
              project_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Edit file using str_replace pattern (must be unique)
    
    Args:
        path: File path
        old_str: String to replace (must appear exactly once)
        new_str: Replacement string
        project_root: Project root directory
        
    Returns:
        Dict with 'success', 'path', 'old_str', 'new_str', 'changes'
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
    
    # Check file exists
    if not os.path.exists(path):
        raise FileSystemError(f"File not found: {path}")
    
    # Read file
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
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
    
    # Perform replacement
    new_content = content.replace(old_str, new_str)
    
    # Write back
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        raise FileSystemError(f"Failed to write file {path}: {e}")
    
    return {
        'success': True,
        'path': path,
        'old_str': old_str[:100] + ('...' if len(old_str) > 100 else ''),
        'new_str': new_str[:100] + ('...' if len(new_str) > 100 else ''),
        'changes': len(new_str) - len(old_str),
    }


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
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise FileSystemError(f"Failed to create file {path}: {e}")
    
    return {
        'success': True,
        'path': path,
        'size': len(content),
    }


def grep_search(pattern: str, scope: str = ".", 
                project_root: Optional[str] = None,
                max_results: int = 50,
                file_pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for pattern in files (regex supported)
    
    Args:
        pattern: Search pattern (regex)
        scope: Search scope directory
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
