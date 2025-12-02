"""
VSCode Integration Tools

Provides tools for integrating with VSCode extension:
- get_active_file: Get current file path and content
- show_diff: Show diff comparison in VSCode
- apply_changes: Apply code changes to files
- get_selection: Get currently selected text
"""

import os
from typing import Dict, Any, Optional


class VSCodeError(Exception):
    """VSCode integration error"""
    pass


# Mock data for testing (when not in VSCode mode)
MOCK_DATA = {
    "active_file": {
        "path": "/path/to/project/src/main.cpp",
        "content": """#include <iostream>

int main() {
    std::cout << "Hello World" << std::endl;
    return 0;
}
""",
        "language": "cpp",
        "lineCount": 7
    },
    "selection": {
        "text": 'std::cout << "Hello World" << std::endl;',
        "start": {"line": 3, "character": 4},
        "end": {"line": 3, "character": 49}
    },
    "workspace": "/path/to/project"
}


def _mock_response(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate mock response for testing"""
    if method == "getActiveFile":
        return {"success": True, "file": MOCK_DATA["active_file"]}
    elif method == "getSelection":
        return {"success": True, "selection": MOCK_DATA["selection"]}
    elif method == "showDiff":
        return {"success": True, "message": f"Diff shown: {params.get('title', 'Untitled')}"}
    elif method == "applyChanges":
        return {"success": True, "message": f"Applied changes to {params.get('path', 'unknown')}"}
    elif method == "openFile":
        return {"success": True, "message": f"Opened file: {params.get('path', 'unknown')}"}
    elif method == "getWorkspaceFolder":
        return {"success": True, "folder": MOCK_DATA["workspace"]}
    else:
        return {"success": False, "error": f"Unknown method: {method}"}


# Tool functions for agent

def get_active_file() -> Dict[str, Any]:
    """Get currently active file in VSCode

    Returns:
        dict: {
            'path': str,
            'content': str,
            'language': str,
            'lineCount': int
        }
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    if is_vscode_mode():
        # Use actual RPC communication
        response = send_vscode_request("getActiveFile", {})
        if response.get("success"):
            return response["file"]
        else:
            raise VSCodeError(response.get("error", "Failed to get active file"))
    else:
        # Use mock data
        response = _mock_response("getActiveFile", {})
        if response.get("success"):
            return response["file"]
        else:
            raise VSCodeError(response.get("error", "Failed to get active file"))


def get_selection() -> Dict[str, Any]:
    """Get currently selected text in VSCode

    Returns:
        dict: {
            'text': str,
            'start': {'line': int, 'character': int},
            'end': {'line': int, 'character': int}
        }
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    if is_vscode_mode():
        response = send_vscode_request("getSelection", {})
        if response.get("success"):
            return response["selection"]
        else:
            raise VSCodeError(response.get("error", "Failed to get selection"))
    else:
        response = _mock_response("getSelection", {})
        if response.get("success"):
            return response["selection"]
        else:
            raise VSCodeError(response.get("error", "Failed to get selection"))


def show_diff(title: str, original_path: str, modified_content: str) -> Dict[str, Any]:
    """Show diff comparison in VSCode

    Args:
        title: Diff title
        original_path: Path to original file
        modified_content: Modified content to compare

    Returns:
        dict: {'success': bool, 'message': str}
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    params = {
        "title": title,
        "originalPath": original_path,
        "modifiedContent": modified_content
    }

    if is_vscode_mode():
        return send_vscode_request("showDiff", params)
    else:
        return _mock_response("showDiff", params)


def apply_changes(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """Apply code changes to a file

    Args:
        path: File path
        old_str: Original string to replace
        new_str: New string

    Returns:
        dict: {'success': bool, 'message': str}
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    params = {
        "path": path,
        "oldStr": old_str,
        "newStr": new_str
    }

    if is_vscode_mode():
        return send_vscode_request("applyChanges", params)
    else:
        return _mock_response("applyChanges", params)


def open_file(path: str, line: Optional[int] = None, column: Optional[int] = None) -> Dict[str, Any]:
    """Open file in VSCode editor

    Args:
        path: File path
        line: Optional line number to jump to
        column: Optional column number

    Returns:
        dict: {'success': bool, 'message': str}
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    params = {"path": path}
    if line is not None:
        params["line"] = line
    if column is not None:
        params["column"] = column

    if is_vscode_mode():
        return send_vscode_request("openFile", params)
    else:
        return _mock_response("openFile", params)


def get_workspace_folder() -> str:
    """Get VSCode workspace folder path

    Returns:
        str: Workspace folder path
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    if is_vscode_mode():
        response = send_vscode_request("getWorkspaceFolder", {})
        if response.get("success"):
            return response["folder"]
        else:
            raise VSCodeError(response.get("error", "Failed to get workspace folder"))
    else:
        response = _mock_response("getWorkspaceFolder", {})
        if response.get("success"):
            return response["folder"]
        else:
            raise VSCodeError(response.get("error", "Failed to get workspace folder"))


def confirm_dialog(message: str, title: str = "Confirm") -> bool:
    """Show confirmation dialog in VSCode

    Args:
        message: Dialog message
        title: Dialog title (default: "Confirm")

    Returns:
        bool: True if user clicked "Yes", False if clicked "No"
    """
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    params = {
        "message": message,
        "title": title
    }

    if is_vscode_mode():
        try:
            response = send_vscode_request("confirmDialog", params, timeout=60.0)  # 60s timeout for user decision
            return response.get("confirmed", False)
        except Exception:
            # If RPC fails, default to no confirmation (safe fallback)
            return False
    else:
        # Mock mode: always return True
        return True
