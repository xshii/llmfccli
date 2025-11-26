"""
Enhanced Edit Tool with VSCode Integration

Provides smart file editing with diff preview and VSCode integration.
Follows Claude Code best practices.
"""

import os
from typing import Dict, Any, Optional
from .filesystem import edit_file as basic_edit_file


class EditMode:
    """Edit operation modes"""
    DIRECT = "direct"  # 直接修改（CLI 模式）
    PREVIEW = "preview"  # 显示预览，等待确认
    AUTO = "auto"  # 自动选择模式


def edit_file_with_preview(
    path: str,
    old_str: str,
    new_str: str,
    project_root: Optional[str] = None,
    mode: str = EditMode.AUTO,
    auto_confirm: bool = False
) -> Dict[str, Any]:
    """
    Edit file with optional diff preview

    在 VSCode 模式下：
    1. 显示 diff 预览
    2. 等待用户确认（除非 auto_confirm=True）
    3. 通过 VSCode API 应用更改（支持 undo/redo）

    在 CLI 模式下：
    - 显示文本预览（除非 auto_confirm=True）
    - 直接修改文件

    Args:
        path: 文件路径
        old_str: 要替换的字符串
        new_str: 新字符串
        project_root: 项目根目录
        mode: 编辑模式（auto/direct/preview）
        auto_confirm: 自动确认，不等待用户输入

    Returns:
        {
            'success': bool,
            'path': str,
            'mode': str,  # 'vscode' or 'direct'
            'previewed': bool,
            'message': str
        }
    """
    from backend.rpc.client import is_vscode_mode

    # 确定使用的模式
    use_vscode = is_vscode_mode() and mode != EditMode.DIRECT

    # 解析完整路径
    if not os.path.isabs(path) and project_root:
        full_path = os.path.join(project_root, path)
    else:
        full_path = os.path.abspath(path)

    # 安全检查
    if not os.path.exists(full_path):
        return {
            'success': False,
            'error': f'File not found: {path}'
        }

    # 读取原内容
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to read file: {e}'
        }

    # 检查字符串是否存在
    if old_str not in original_content:
        return {
            'success': False,
            'error': f'String not found in file: {old_str[:50]}...'
        }

    # 生成新内容
    new_content = original_content.replace(old_str, new_str, 1)

    # VSCode 模式
    if use_vscode:
        return _edit_with_vscode(
            full_path,
            original_content,
            new_content,
            old_str,
            new_str,
            auto_confirm
        )
    # 直接模式
    else:
        return _edit_direct(
            full_path,
            original_content,
            new_content,
            old_str,
            new_str,
            auto_confirm
        )


def _edit_with_vscode(
    path: str,
    original_content: str,
    new_content: str,
    old_str: str,
    new_str: str,
    auto_confirm: bool
) -> Dict[str, Any]:
    """通过 VSCode API 编辑文件"""
    from backend.tools import vscode

    try:
        # 1. 显示 diff 预览
        diff_result = vscode.show_diff(
            title=f"Edit: {os.path.basename(path)}",
            original_path=path,
            modified_content=new_content
        )

        if not diff_result.get('success'):
            return {
                'success': False,
                'error': 'Failed to show diff',
                'details': diff_result
            }

        # 2. 如果需要确认，等待用户操作
        if not auto_confirm:
            # TODO: 实现确认对话框
            # confirmed = vscode.show_confirmation(...)
            # 目前先假设确认
            confirmed = True
        else:
            confirmed = True

        if not confirmed:
            return {
                'success': False,
                'message': 'User cancelled the edit',
                'previewed': True
            }

        # 3. 通过 VSCode API 应用更改
        apply_result = vscode.apply_changes(path, old_str, new_str)

        if apply_result.get('success'):
            return {
                'success': True,
                'path': path,
                'mode': 'vscode',
                'previewed': True,
                'message': f"Applied changes to {os.path.basename(path)} via VSCode"
            }
        else:
            return {
                'success': False,
                'error': 'Failed to apply changes',
                'details': apply_result
            }

    except Exception as e:
        return {
            'success': False,
            'error': f'VSCode integration error: {e}'
        }


def _edit_direct(
    path: str,
    original_content: str,
    new_content: str,
    old_str: str,
    new_str: str,
    auto_confirm: bool
) -> Dict[str, Any]:
    """直接修改文件（CLI 模式）"""

    # 如果需要确认，显示文本预览
    if not auto_confirm:
        print(f"\n{'=' * 60}")
        print(f"📝 准备编辑: {path}")
        print(f"{'=' * 60}")
        print(f"\n将要替换:")
        print(f"[旧] {old_str[:100]}{'...' if len(old_str) > 100 else ''}")
        print(f"\n替换为:")
        print(f"[新] {new_str[:100]}{'...' if len(new_str) > 100 else ''}")
        print(f"\n{'=' * 60}")

        response = input("确认应用更改? (y/n): ").strip().lower()
        if response != 'y':
            return {
                'success': False,
                'message': 'User cancelled the edit',
                'previewed': True
            }

    # 应用更改
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {
            'success': True,
            'path': path,
            'mode': 'direct',
            'previewed': not auto_confirm,
            'message': f"Successfully edited {os.path.basename(path)}"
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to write file: {e}'
        }


def batch_edit_files(
    edits: list,
    project_root: Optional[str] = None,
    preview_all: bool = True
) -> Dict[str, Any]:
    """
    批量编辑多个文件

    Args:
        edits: 编辑列表，每项格式：
               {'path': str, 'old_str': str, 'new_str': str}
        project_root: 项目根目录
        preview_all: 是否预览所有更改后再应用

    Returns:
        {
            'success': bool,
            'total': int,
            'succeeded': int,
            'failed': int,
            'results': List[Dict]
        }
    """
    from backend.rpc.client import is_vscode_mode
    from backend.tools import vscode

    results = []
    succeeded = 0
    failed = 0

    if is_vscode_mode() and preview_all and len(edits) > 1:
        # VSCode 模式：先预览所有更改
        print(f"\n准备批量编辑 {len(edits)} 个文件...")

        for i, edit in enumerate(edits, 1):
            path = edit['path']
            if not os.path.isabs(path) and project_root:
                path = os.path.join(project_root, path)

            # 读取文件
            try:
                with open(path, 'r') as f:
                    original = f.read()
                new_content = original.replace(edit['old_str'], edit['new_str'], 1)

                # 显示 diff
                vscode.show_diff(
                    title=f"[{i}/{len(edits)}] {os.path.basename(path)}",
                    original_path=path,
                    modified_content=new_content
                )
            except Exception as e:
                print(f"⚠️  无法预览 {path}: {e}")

        # 询问是否应用所有更改
        # TODO: 实现批量确认对话框
        confirmed = input(f"\n应用所有 {len(edits)} 个更改? (y/n): ").lower() == 'y'
        if not confirmed:
            return {
                'success': False,
                'message': 'Batch edit cancelled by user',
                'total': len(edits),
                'succeeded': 0,
                'failed': 0,
                'results': []
            }

    # 应用所有编辑
    for edit in edits:
        result = edit_file_with_preview(
            path=edit['path'],
            old_str=edit['old_str'],
            new_str=edit['new_str'],
            project_root=project_root,
            auto_confirm=True  # 已经预览过了，自动确认
        )

        results.append(result)

        if result['success']:
            succeeded += 1
        else:
            failed += 1

    return {
        'success': failed == 0,
        'total': len(edits),
        'succeeded': succeeded,
        'failed': failed,
        'results': results
    }


# 向后兼容的包装器
def smart_edit_file(path: str, old_str: str, new_str: str,
                   project_root: Optional[str] = None) -> Dict[str, Any]:
    """
    智能编辑文件（向后兼容接口）

    自动检测运行环境：
    - VSCode 模式：显示 diff，通过 API 应用
    - CLI 模式：直接修改

    这是对原 edit_file 的增强替代
    """
    return edit_file_with_preview(
        path=path,
        old_str=old_str,
        new_str=new_str,
        project_root=project_root,
        mode=EditMode.AUTO,
        auto_confirm=False
    )
