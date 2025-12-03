# -*- coding: utf-8 -*-
"""
Bash session management for persistent shell execution

Uses PersistentShellSession as backend for unified shell state
between CLI /cmd and Agent bash_run tool.
"""

import time
from typing import Dict, Any, Optional
from pathlib import Path

from backend.utils.shell_session import PersistentShellSession


class BashSession:
    """Wrapper around PersistentShellSession for tool execution"""

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
        self._shell: Optional[PersistentShellSession] = None

    def _get_shell(self) -> PersistentShellSession:
        """Get the shared persistent shell session"""
        global _shared_session
        if _shared_session is not None:
            return _shared_session
        # Fallback: create session if none shared (e.g., when used outside CLI)
        return get_shared_session(str(self.project_root))

    def execute(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute command using persistent shell

        Args:
            command: Command to execute
            timeout: Timeout in seconds (overrides default)

        Returns:
            Dict with stdout, stderr, return_code, duration, success
        """
        timeout = timeout or self.timeout
        start_time = time.time()

        try:
            shell = self._get_shell()
            success, stdout, stderr = shell.execute(command, timeout=float(timeout))
            duration = time.time() - start_time

            result = {
                'stdout': stdout,
                'stderr': stderr,
                'return_code': 0 if success else 1,
                'duration': duration,
                'success': success,
            }

            # Add error field for timeout detection
            if 'timed out' in stderr.lower():
                result['error'] = 'timeout'

            return result

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
        """Close bash session (delegates to shared session manager)"""
        # Don't close shared session here - managed globally
        pass


# Global shared session (singleton per project_root)
_shared_session: Optional[PersistentShellSession] = None
_shared_session_root: Optional[str] = None


def get_shared_session(project_root: str) -> PersistentShellSession:
    """
    Get the shared persistent shell session

    Args:
        project_root: Project root directory

    Returns:
        PersistentShellSession instance
    """
    global _shared_session, _shared_session_root

    # Create new session if none exists or project root changed
    if _shared_session is None or _shared_session_root != project_root:
        if _shared_session is not None:
            _shared_session.close()
        _shared_session = PersistentShellSession(initial_cwd=project_root)
        _shared_session_root = project_root

    return _shared_session


def set_shared_session(session: PersistentShellSession, project_root: str):
    """
    Set the shared session (called from CLI to share session with tools)

    Args:
        session: PersistentShellSession instance from CLI
        project_root: Project root directory
    """
    global _shared_session, _shared_session_root
    _shared_session = session
    _shared_session_root = project_root


def close_shared_session():
    """Close the shared session"""
    global _shared_session, _shared_session_root
    if _shared_session is not None:
        _shared_session.close()
        _shared_session = None
        _shared_session_root = None


# Legacy API compatibility
_sessions: Dict[str, BashSession] = {}


def get_session(session_id: str, project_root: str, timeout: int = 60) -> BashSession:
    """
    Get or create a bash session (legacy API)

    Args:
        session_id: Session identifier (ignored, uses shared session)
        project_root: Project root directory
        timeout: Default command timeout

    Returns:
        BashSession instance
    """
    if session_id not in _sessions:
        _sessions[session_id] = BashSession(project_root, timeout)
    return _sessions[session_id]


def close_session(session_id: str):
    """Close a specific bash session (legacy API)"""
    if session_id in _sessions:
        _sessions[session_id].close()
        del _sessions[session_id]


def close_all_sessions():
    """Close all bash sessions"""
    for session in _sessions.values():
        session.close()
    _sessions.clear()
    close_shared_session()
