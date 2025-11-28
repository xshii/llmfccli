# -*- coding: utf-8 -*-
"""
Bash session management for persistent shell execution
"""

import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path


class BashSession:
    """Simplified one-shot bash execution (persistent sessions for future)"""

    def __init__(self, project_root: str, timeout: int = 60):
        """
        Initialize bash session

        Args:
            project_root: Project root directory
            timeout: Default command timeout in seconds
        """
        self.project_root = Path(project_root).resolve()
        self.timeout = timeout
        self.session_id = f"bash_{int(time.time())}"

    def execute(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute command (simplified one-shot version)

        Args:
            command: Command to execute
            timeout: Timeout in seconds (overrides default)

        Returns:
            Dict with stdout, stderr, return_code, duration
        """
        timeout = timeout or self.timeout
        start_time = time.time()

        try:
            # Execute command directly using subprocess.run
            result = subprocess.run(
                ['bash', '-c', command],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            duration = time.time() - start_time

            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'duration': duration,
                'success': result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'return_code': -1,
                'duration': duration,
                'success': False,
                'error': 'timeout',
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'duration': duration,
                'success': False,
                'error': str(e),
            }

    def close(self):
        """Close bash session (no-op for one-shot execution)"""
        pass


# Global session manager
_sessions: Dict[str, BashSession] = {}


def get_session(session_id: str, project_root: str, timeout: int = 60) -> BashSession:
    """
    Get or create a persistent bash session

    Args:
        session_id: Session identifier
        project_root: Project root directory
        timeout: Default command timeout

    Returns:
        BashSession instance
    """
    if session_id not in _sessions:
        _sessions[session_id] = BashSession(project_root, timeout)
    return _sessions[session_id]


def close_session(session_id: str):
    """Close a specific bash session"""
    if session_id in _sessions:
        _sessions[session_id].close()
        del _sessions[session_id]


def close_all_sessions():
    """Close all persistent bash sessions"""
    for session in _sessions.values():
        session.close()
    _sessions.clear()
