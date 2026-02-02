# -*- coding: utf-8 -*-
"""
SSH tunnel check
"""

import socket
import subprocess

from .result import PreCheckResult


def check_ssh_tunnel(host: str = "localhost", port: int = 11434) -> PreCheckResult:
    """
    Check if SSH tunnel is established

    Args:
        host: Target host (default: localhost)
        port: Target port (default: 11434 for Ollama)

    Returns:
        PreCheckResult
    """
    try:
        # Try to connect to the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            # Port is open, check if it's actually Ollama using curl
            try:
                curl_result = subprocess.run(
                    ['curl', '-s', '--connect-timeout', '3', f'http://{host}:{port}/api/tags'],
                    capture_output=True, text=True, timeout=5
                )
                if curl_result.returncode == 0 and curl_result.stdout.strip():
                    return PreCheckResult(
                        "SSH Tunnel",
                        True,
                        f"已连接到 {host}:{port} (Ollama 服务正常响应)",
                        {"host": host, "port": port, "service": "ollama"}
                    )
                else:
                    return PreCheckResult(
                        "SSH Tunnel",
                        False,
                        "SSH 隧道已建立，但远程 Ollama 服务未运行或未响应",
                        {"host": host, "port": port}
                    )
            except Exception as e:
                return PreCheckResult(
                    "SSH Tunnel",
                    False,
                    "SSH 隧道已建立，但远程 Ollama 服务未运行或未响应",
                    {"host": host, "port": port, "error": str(e)}
                )
        else:
            return PreCheckResult(
                "SSH Tunnel",
                False,
                f"Cannot connect to {host}:{port} - SSH tunnel may not be established",
                {"host": host, "port": port, "error_code": result}
            )
    except Exception as e:
        return PreCheckResult(
            "SSH Tunnel",
            False,
            f"Connection check failed: {e}",
            {"host": host, "port": port}
        )
