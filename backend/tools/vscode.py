"""
VSCode Integration Tools

Provides tools for integrating with VSCode extension:
- get_active_file: Get current file path and content
- show_diff: Show diff comparison in VSCode
- apply_changes: Apply code changes to files
- get_selection: Get currently selected text
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path


class VSCodeError(Exception):
    """VSCode integration error"""
    pass


class VSCodeClient:
    """Client for communicating with VSCode extension

    Communication modes:
    1. Mock mode: Returns simulated responses (for testing)
    2. IPC mode: Communicates via stdin/stdout with VSCode extension
    3. Socket mode: Communicates via local socket
    """

    def __init__(self, mode: str = "mock", socket_path: Optional[str] = None):
        """Initialize VSCode client

        Args:
            mode: Communication mode ("mock", "ipc", "socket")
            socket_path: Path to socket file (for socket mode)
        """
        self.mode = mode
        self.socket_path = socket_path
        self.request_id = 0

        # Mock data for testing
        self.mock_active_file = "/path/to/project/src/main.cpp"
        self.mock_file_content = """#include <iostream>

int main() {
    std::cout << "Hello World" << std::endl;
    return 0;
}
"""
        self.mock_selection = {
            "text": 'std::cout << "Hello World" << std::endl;',
            "start": {"line": 3, "character": 4},
            "end": {"line": 3, "character": 49}
        }

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to VSCode extension

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Response from VSCode
        """
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }

        if self.mode == "mock":
            return self._mock_response(method, params)
        elif self.mode == "ipc":
            return self._ipc_request(request)
        elif self.mode == "socket":
            return self._socket_request(request)
        else:
            raise VSCodeError(f"Unknown communication mode: {self.mode}")

    def _mock_response(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response for testing

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Mock response
        """
        if method == "getActiveFile":
            return {
                "success": True,
                "file": {
                    "path": self.mock_active_file,
                    "content": self.mock_file_content,
                    "language": "cpp",
                    "lineCount": len(self.mock_file_content.split('\n'))
                }
            }

        elif method == "getSelection":
            return {
                "success": True,
                "selection": self.mock_selection
            }

        elif method == "showDiff":
            return {
                "success": True,
                "message": f"Diff shown: {params.get('title', 'Untitled')}"
            }

        elif method == "applyChanges":
            return {
                "success": True,
                "message": f"Applied changes to {params.get('path', 'unknown')}"
            }

        elif method == "openFile":
            return {
                "success": True,
                "message": f"Opened file: {params.get('path', 'unknown')}"
            }

        elif method == "getWorkspaceFolder":
            return {
                "success": True,
                "folder": "/path/to/project"
            }

        else:
            return {
                "success": False,
                "error": f"Unknown method: {method}"
            }

    def _ipc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via IPC (stdin/stdout)

        Args:
            request: JSON-RPC request

        Returns:
            Response from VSCode
        """
        # TODO: Implement IPC communication
        # This would write to stdout and read from stdin
        raise NotImplementedError("IPC mode not yet implemented")

    def _socket_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via Unix socket

        Args:
            request: JSON-RPC request

        Returns:
            Response from VSCode
        """
        # TODO: Implement socket communication
        import socket
        raise NotImplementedError("Socket mode not yet implemented")


# Global VSCode client instance
_vscode_client: Optional[VSCodeClient] = None


def init_vscode_client(mode: str = "mock", socket_path: Optional[str] = None) -> VSCodeClient:
    """Initialize global VSCode client

    Args:
        mode: Communication mode
        socket_path: Socket path (for socket mode)

    Returns:
        VSCode client instance
    """
    global _vscode_client
    _vscode_client = VSCodeClient(mode=mode, socket_path=socket_path)
    return _vscode_client


def get_vscode_client() -> VSCodeClient:
    """Get global VSCode client instance

    Returns:
        VSCode client instance
    """
    global _vscode_client
    if _vscode_client is None:
        _vscode_client = VSCodeClient(mode="mock")
    return _vscode_client


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
    # Check if in VSCode integration mode
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    if is_vscode_mode():
        # Use actual RPC communication
        response = send_vscode_request("getActiveFile", {})
        if response.get("success"):
            return response["file"]
        else:
            raise VSCodeError(response.get("error", "Failed to get active file"))
    else:
        # Use mock client
        client = get_vscode_client()
        response = client._send_request("getActiveFile", {})
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
        client = get_vscode_client()
        response = client._send_request("getSelection", {})
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

    if is_vscode_mode():
        return send_vscode_request("showDiff", {
            "title": title,
            "originalPath": original_path,
            "modifiedContent": modified_content
        })
    else:
        client = get_vscode_client()
        return client._send_request("showDiff", {
            "title": title,
            "originalPath": original_path,
            "modifiedContent": modified_content
        })


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

    if is_vscode_mode():
        return send_vscode_request("applyChanges", {
            "path": path,
            "oldStr": old_str,
            "newStr": new_str
        })
    else:
        client = get_vscode_client()
        return client._send_request("applyChanges", {
            "path": path,
            "oldStr": old_str,
            "newStr": new_str
        })


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
        client = get_vscode_client()
        return client._send_request("openFile", params)


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
        client = get_vscode_client()
        response = client._send_request("getWorkspaceFolder", {})
        if response.get("success"):
            return response["folder"]
        else:
            raise VSCodeError(response.get("error", "Failed to get workspace folder"))
