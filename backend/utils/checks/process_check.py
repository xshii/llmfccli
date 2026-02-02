# -*- coding: utf-8 -*-
"""
Local process check (kill local Ollama when using remote)
"""

import platform
import subprocess
from pathlib import Path

import yaml

from .result import PreCheckResult


def check_and_kill_local_ollama() -> PreCheckResult:
    """
    Check if local Ollama is running and kill it if using remote Ollama.
    Reads config/llm.yaml to determine if ssh.enabled is true.
    Supports both Windows (tasklist/taskkill) and Unix (pgrep/kill).

    Returns:
        PreCheckResult
    """
    try:
        # Find config file
        config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'llm.yaml'

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
                return _check_windows_ollama()
            else:
                return _check_unix_ollama()
        except subprocess.TimeoutExpired:
            return PreCheckResult(
                "Local Ollama Check",
                False,
                "Process check timeout",
                {"ssh_enabled": True, "platform": platform.system()}
            )
        except FileNotFoundError:
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


def _check_windows_ollama() -> PreCheckResult:
    """Check and kill Ollama on Windows"""
    import csv
    import io

    all_killed_pids = []
    process_names = ["ollama app.exe", "ollama.exe"]  # Order matters!

    for process_name in process_names:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {process_name}', '/FO', 'CSV', '/NH'],
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0 and process_name in result.stdout:
            pids = []
            reader = csv.reader(io.StringIO(result.stdout))
            for row in reader:
                if len(row) >= 2 and process_name in row[0]:
                    pids.append(row[1])

            for pid in pids:
                try:
                    kill_result = subprocess.run(
                        ['taskkill', '/F', '/PID', pid],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if kill_result.returncode == 0:
                        all_killed_pids.append(f"{process_name}:{pid}")
                except Exception:
                    pass

    if all_killed_pids:
        return PreCheckResult(
            "Local Ollama Check",
            True,
            f"Killed {len(all_killed_pids)} local Ollama process(es) (using remote Ollama)",
            {"killed_pids": all_killed_pids, "ssh_enabled": True, "platform": "Windows"}
        )
    else:
        return PreCheckResult(
            "Local Ollama Check",
            True,
            "No local Ollama process found (using remote Ollama)",
            {"ssh_enabled": True, "platform": "Windows"}
        )


def _check_unix_ollama() -> PreCheckResult:
    """Check and kill Ollama on Unix/Linux/macOS"""
    result = subprocess.run(
        ['pgrep', '-f', 'ollama serve'],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode == 0 and result.stdout.strip():
        pids = result.stdout.strip().split('\n')

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
            except Exception:
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
        return PreCheckResult(
            "Local Ollama Check",
            True,
            "No local Ollama process found (using remote Ollama)",
            {"ssh_enabled": True, "platform": "Unix"}
        )
