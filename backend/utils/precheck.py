# -*- coding: utf-8 -*-
"""
Pre-check utilities for verifying environment setup
"""

import subprocess
import socket
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml


class PreCheckResult:
    """Result of a pre-check"""

    def __init__(self, name: str, success: bool, message: str, details: Optional[Dict] = None):
        self.name = name
        self.success = success
        self.message = message
        self.details = details or {}

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.name}: {self.message}"


class PreCheck:
    """Environment pre-check utilities"""

    @staticmethod
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
                            f"SSH 隧道已建立，但远程 Ollama 服务未运行或未响应",
                            {"host": host, "port": port}
                        )
                except Exception as e:
                    return PreCheckResult(
                        "SSH Tunnel",
                        False,
                        f"SSH 隧道已建立，但远程 Ollama 服务未运行或未响应",
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

    @staticmethod
    def check_ollama_connection(base_url: str = "http://localhost:11434") -> PreCheckResult:
        """
        Check Ollama service connection

        Args:
            base_url: Ollama base URL

        Returns:
            PreCheckResult
        """
        try:
            # Use curl to test connection
            result = subprocess.run(
                ['curl', '-s', '--connect-timeout', '3', f'{base_url}/api/tags'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout:
                # Try to parse JSON
                import json
                try:
                    data = json.loads(result.stdout)
                    models = data.get('models', [])
                    model_names = [m.get('name', 'unknown') for m in models]

                    return PreCheckResult(
                        "Ollama Connection",
                        True,
                        f"Connected to Ollama ({len(models)} models available)",
                        {"url": base_url, "models": model_names}
                    )
                except json.JSONDecodeError:
                    return PreCheckResult(
                        "Ollama Connection",
                        False,
                        f"Connected but invalid response: {result.stdout[:100]}",
                        {"url": base_url}
                    )
            else:
                return PreCheckResult(
                    "Ollama Connection",
                    False,
                    f"无法连接 Ollama（远程服务可能未启动）",
                    {"url": base_url, "stderr": result.stderr}
                )
        except subprocess.TimeoutExpired:
            return PreCheckResult(
                "Ollama Connection",
                False,
                f"Connection timeout to {base_url}",
                {"url": base_url}
            )
        except Exception as e:
            return PreCheckResult(
                "Ollama Connection",
                False,
                f"Connection check failed: {e}",
                {"url": base_url}
            )

    @staticmethod
    def check_ollama_model(model_name: str = "qwen3:latest",
                          base_url: str = "http://localhost:11434") -> PreCheckResult:
        """
        Check if specific Ollama model is available

        Args:
            model_name: Model name to check
            base_url: Ollama base URL

        Returns:
            PreCheckResult
        """
        try:
            result = subprocess.run(
                ['curl', '-s', '--connect-timeout', '3', f'{base_url}/api/tags'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout:
                import json
                data = json.loads(result.stdout)
                models = data.get('models', [])
                model_names = [m.get('name', '') for m in models]

                # Check if model exists (exact match or prefix match)
                model_exists = any(
                    name == model_name or name.startswith(model_name.split(':')[0])
                    for name in model_names
                )

                if model_exists:
                    return PreCheckResult(
                        "Ollama Model",
                        True,
                        f"Model '{model_name}' is available",
                        {"model": model_name, "all_models": model_names}
                    )
                else:
                    return PreCheckResult(
                        "Ollama Model",
                        False,
                        f"Model '{model_name}' not found. Available: {', '.join(model_names)}",
                        {"model": model_name, "all_models": model_names}
                    )
            else:
                return PreCheckResult(
                    "Ollama Model",
                    False,
                    "Cannot retrieve model list from Ollama",
                    {"model": model_name}
                )
        except Exception as e:
            return PreCheckResult(
                "Ollama Model",
                False,
                f"Model check failed: {e}",
                {"model": model_name}
            )

    @staticmethod
    def test_ollama_hello(model_name: str = "qwen3:latest",
                         base_url: str = "http://localhost:11434") -> PreCheckResult:
        """
        Test Ollama with a simple 'hi' request

        Args:
            model_name: Model to test
            base_url: Ollama base URL

        Returns:
            PreCheckResult
        """
        try:
            # Send a simple chat request
            import json
            import tempfile

            request_data = {
                "model": model_name,
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(request_data, f)
                temp_file = f.name

            result = subprocess.run(
                ['curl', '-s', '--noproxy', 'localhost', '--connect-timeout', '5',
                 f'{base_url}/api/chat', '-d', f'@{temp_file}'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clean up
            import os
            try:
                os.unlink(temp_file)
            except:
                pass

            if result.returncode == 0 and result.stdout:
                try:
                    response = json.loads(result.stdout)
                    content = response.get('message', {}).get('content', '')

                    if content:
                        return PreCheckResult(
                            "Ollama Hello Test",
                            True,
                            f"Model responded: '{content[:50]}{'...' if len(content) > 50 else ''}'",
                            {"model": model_name, "response_length": len(content)}
                        )
                    else:
                        return PreCheckResult(
                            "Ollama Hello Test",
                            False,
                            "Model returned empty response",
                            {"model": model_name, "response": response}
                        )
                except json.JSONDecodeError as e:
                    return PreCheckResult(
                        "Ollama Hello Test",
                        False,
                        f"Invalid JSON response: {e}",
                        {"model": model_name}
                    )
            else:
                return PreCheckResult(
                    "Ollama Hello Test",
                    False,
                    f"Request failed: {result.stderr or 'empty response'}",
                    {"model": model_name}
                )
        except subprocess.TimeoutExpired:
            return PreCheckResult(
                "Ollama Hello Test",
                False,
                "Request timeout (>30s)",
                {"model": model_name}
            )
        except Exception as e:
            return PreCheckResult(
                "Ollama Hello Test",
                False,
                f"Test failed: {e}",
                {"model": model_name}
            )

    @staticmethod
    def check_and_kill_local_ollama() -> PreCheckResult:
        """
        Check if local Ollama is running and kill it if using remote Ollama.
        Reads config/ollama.yaml to determine if ssh.enabled is true.
        Supports both Windows (tasklist/taskkill) and Unix (pgrep/kill).

        Returns:
            PreCheckResult
        """
        import os
        import platform
        import yaml
        from pathlib import Path

        try:
            # Find config file
            config_path = Path(__file__).parent.parent.parent / 'config' / 'ollama.yaml'

            if not config_path.exists():
                return PreCheckResult(
                    "Local Ollama Check",
                    True,
                    "Config file not found, skipping local Ollama check",
                    {"config_path": str(config_path)}
                )

            # Load config
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            ssh_enabled = config.get('ssh', {}).get('enabled', False)

            if not ssh_enabled:
                return PreCheckResult(
                    "Local Ollama Check",
                    True,
                    "Using local Ollama, no need to kill local process",
                    {"ssh_enabled": False}
                )

            # SSH enabled (remote mode), check for local Ollama process
            is_windows = platform.system() == 'Windows'

            try:
                if is_windows:
                    # Windows: Check for both "ollama app.exe" and "ollama.exe"
                    # Must kill "ollama app.exe" first (GUI), then "ollama.exe" (service)
                    import csv
                    import io

                    all_killed_pids = []
                    process_names = ["ollama app.exe", "ollama.exe"]  # Order matters!

                    for process_name in process_names:
                        # Find processes
                        result = subprocess.run(
                            ['tasklist', '/FI', f'IMAGENAME eq {process_name}', '/FO', 'CSV', '/NH'],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            encoding='utf-8',
                            errors='ignore'  # Ignore encoding errors for non-UTF8 output
                        )

                        if result.returncode == 0 and process_name in result.stdout:
                            # Parse CSV output to get PIDs
                            pids = []
                            reader = csv.reader(io.StringIO(result.stdout))
                            for row in reader:
                                if len(row) >= 2 and process_name in row[0]:
                                    pids.append(row[1])  # PID is in second column

                            # Kill processes
                            for pid in pids:
                                try:
                                    kill_result = subprocess.run(
                                        ['taskkill', '/F', '/PID', pid],
                                        capture_output=True,
                                        text=True,
                                        timeout=5,
                                        encoding='utf-8',
                                        errors='ignore'  # Ignore encoding errors
                                    )
                                    if kill_result.returncode == 0:
                                        all_killed_pids.append(f"{process_name}:{pid}")
                                except Exception as e:
                                    pass

                    # Return result
                    if all_killed_pids:
                        return PreCheckResult(
                            "Local Ollama Check",
                            True,
                            f"Killed {len(all_killed_pids)} local Ollama process(es) (using remote Ollama)",
                            {"killed_pids": all_killed_pids, "ssh_enabled": True, "platform": "Windows"}
                        )
                    else:
                        # No processes found or all killed
                        return PreCheckResult(
                            "Local Ollama Check",
                            True,
                            "No local Ollama process found (using remote Ollama)",
                            {"ssh_enabled": True, "platform": "Windows"}
                        )
                else:
                    # Unix/Linux/macOS: Use pgrep to find Ollama processes
                    result = subprocess.run(
                        ['pgrep', '-f', 'ollama serve'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        # Found local Ollama process(es)
                        pids = result.stdout.strip().split('\n')

                        # Kill all Ollama processes
                        killed_pids = []
                        for pid in pids:
                            try:
                                kill_result = subprocess.run(
                                    ['kill', pid],
                                    capture_output=True,
                                    timeout=5
                                )
                                if kill_result.returncode == 0:
                                    killed_pids.append(pid)
                            except Exception as e:
                                pass

                        if killed_pids:
                            return PreCheckResult(
                                "Local Ollama Check",
                                True,
                                f"Killed {len(killed_pids)} local Ollama process(es) (using remote Ollama)",
                                {"killed_pids": killed_pids, "ssh_enabled": True, "platform": "Unix"}
                            )
                        else:
                            return PreCheckResult(
                                "Local Ollama Check",
                                False,
                                f"Found {len(pids)} local Ollama process(es) but failed to kill them",
                                {"pids": pids, "ssh_enabled": True, "platform": "Unix"}
                            )
                    else:
                        # No local Ollama running
                        return PreCheckResult(
                            "Local Ollama Check",
                            True,
                            "No local Ollama process found (using remote Ollama)",
                            {"ssh_enabled": True, "platform": "Unix"}
                        )
            except subprocess.TimeoutExpired:
                return PreCheckResult(
                    "Local Ollama Check",
                    False,
                    "Process check timeout",
                    {"ssh_enabled": True, "platform": platform.system()}
                )
            except FileNotFoundError as e:
                # Command not available
                cmd = "tasklist/taskkill" if is_windows else "pgrep/kill"
                return PreCheckResult(
                    "Local Ollama Check",
                    True,
                    f"{cmd} command not available, skipping process check",
                    {"ssh_enabled": True, "platform": platform.system()}
                )

        except Exception as e:
            return PreCheckResult(
                "Local Ollama Check",
                False,
                f"Check failed: {e}",
                {"platform": platform.system()}
            )

    @staticmethod
    def check_project_structure(project_root: str) -> PreCheckResult:
        """
        Check if project structure is valid

        Args:
            project_root: Project root directory

        Returns:
            PreCheckResult
        """
        import os
        from pathlib import Path

        project_path = Path(project_root)

        if not project_path.exists():
            return PreCheckResult(
                "Project Structure",
                False,
                f"Project root does not exist: {project_root}",
                {"path": project_root}
            )

        if not project_path.is_dir():
            return PreCheckResult(
                "Project Structure",
                False,
                f"Project root is not a directory: {project_root}",
                {"path": project_root}
            )

        # Check for common project files
        expected_items = ['backend', 'tests', 'config']
        found_items = [item for item in expected_items if (project_path / item).exists()]

        if len(found_items) >= 2:
            return PreCheckResult(
                "Project Structure",
                True,
                f"Valid project structure ({len(found_items)}/{len(expected_items)} expected dirs found)",
                {"path": project_root, "found": found_items}
            )
        else:
            return PreCheckResult(
                "Project Structure",
                False,
                f"Invalid project structure (only {len(found_items)}/{len(expected_items)} expected dirs found)",
                {"path": project_root, "found": found_items, "expected": expected_items}
            )

    @classmethod
    def run_all_checks(cls, model_name: str = "qwen3:latest",
                      project_root: Optional[str] = None) -> List[PreCheckResult]:
        """
        Run all pre-checks

        Args:
            model_name: Ollama model to check
            project_root: Optional project root to validate

        Returns:
            List of PreCheckResult
        """
        results = []

        # 0. Check and kill local Ollama if using remote (must be first)
        results.append(cls.check_and_kill_local_ollama())

        # 1. SSH Tunnel
        results.append(cls.check_ssh_tunnel())

        # 2. Ollama Connection
        results.append(cls.check_ollama_connection())

        # 3. Ollama Model
        results.append(cls.check_ollama_model(model_name))

        # 4. Hello Test
        results.append(cls.test_ollama_hello(model_name))

        # 5. Project Structure (if provided)
        if project_root:
            results.append(cls.check_project_structure(project_root))

        return results

    @staticmethod
    def print_results(results: List[PreCheckResult], verbose: bool = False):
        """
        Print check results

        Args:
            results: List of check results
            verbose: Show detailed information
        """
        print("\n" + "=" * 60)
        print("Environment Pre-Check Results")
        print("=" * 60)

        all_passed = all(r.success for r in results)

        for result in results:
            print(str(result))
            if verbose and result.details:
                for key, value in result.details.items():
                    print(f"  └─ {key}: {value}")

        print("=" * 60)

        if all_passed:
            print("✅ All checks passed!")
        else:
            failed = [r for r in results if not r.success]
            print(f"❌ {len(failed)} check(s) failed")
            print("\nRecommended actions:")
            # Load SSH host from config
            ssh_host = "ollama-tunnel"
            try:
                config_path = Path(__file__).parent.parent.parent / "config" / "ollama.yaml"
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    ssh_host = config.get('ssh', {}).get('host', 'ollama-tunnel')
            except Exception:
                pass
            for result in failed:
                if "SSH Tunnel" in result.name:
                    print(f"  • Start SSH tunnel: ssh -fN {ssh_host}")
                elif "Ollama Connection" in result.name:
                    print("  • Verify Ollama service is running on remote server")
                elif "Ollama Model" in result.name:
                    print(f"  • Pull model: ollama pull {result.details.get('model', 'qwen3:latest')}")

        print()

        return all_passed


def main():
    """Run pre-checks as standalone script"""
    import argparse

    parser = argparse.ArgumentParser(description="Pre-check environment setup")
    parser.add_argument('--model', default='qwen3:latest', help='Ollama model name')
    parser.add_argument('--project-root', help='Project root directory to validate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')

    args = parser.parse_args()

    results = PreCheck.run_all_checks(args.model, args.project_root)
    all_passed = PreCheck.print_results(results, args.verbose)

    return 0 if all_passed else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
