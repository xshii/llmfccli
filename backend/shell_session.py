# -*- coding: utf-8 -*-
"""
Persistent shell session manager for /cmd mode

Maintains a persistent shell process that preserves:
- Working directory (cd commands)
- Environment variables (export/set commands)
- Shell state across multiple commands

Supports:
- Linux/Mac: bash
- Windows: cmd.exe
"""

import subprocess
import threading
import time
import os
import platform
from typing import Optional, Tuple
from queue import Queue, Empty


class PersistentShellSession:
    """Manages a persistent interactive shell session (cross-platform)"""

    def __init__(self, initial_cwd: Optional[str] = None):
        """
        Initialize persistent shell session

        Args:
            initial_cwd: Initial working directory (defaults to current directory)
        """
        self.initial_cwd = initial_cwd or os.getcwd()
        self.process: Optional[subprocess.Popen] = None
        self.stdout_queue: Queue = Queue()
        self.stderr_queue: Queue = Queue()
        self.lock = threading.Lock()

        # Detect platform
        self.is_windows = platform.system() == 'Windows'

        self._start_shell()

    def _get_shell_command(self):
        """Get the appropriate shell command for this platform"""
        if self.is_windows:
            # Use cmd.exe on Windows
            return ['cmd.exe', '/Q']  # /Q disables echo
        else:
            # Use bash on Linux/Mac
            return ['/bin/bash', '--norc', '--noprofile']

    def _start_shell(self):
        """Start the persistent shell process"""
        with self.lock:
            if self.process is not None:
                self._cleanup_process()

            # Start platform-appropriate shell
            shell_cmd = self._get_shell_command()

            self.process = subprocess.Popen(
                shell_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.initial_cwd,
                text=True,
                bufsize=1,  # Line buffered
                env=os.environ.copy()
            )

            # Start output reader threads
            self.stdout_thread = threading.Thread(
                target=self._read_stream,
                args=(self.process.stdout, self.stdout_queue),
                daemon=True
            )
            self.stderr_thread = threading.Thread(
                target=self._read_stream,
                args=(self.process.stderr, self.stderr_queue),
                daemon=True
            )

            self.stdout_thread.start()
            self.stderr_thread.start()

            # Set initial directory (platform-specific)
            if self.is_windows:
                # Windows: use /d to change drives if needed
                self._send_raw_command(f'cd /d "{self.initial_cwd}"')
            else:
                # Unix: standard cd
                self._send_raw_command(f'cd "{self.initial_cwd}"')
            self._drain_output(timeout=0.5)

    def _read_stream(self, stream, queue):
        """Read from stream and put lines into queue"""
        try:
            for line in stream:
                queue.put(line)
        except Exception:
            pass

    def _send_raw_command(self, command: str):
        """Send raw command to shell (internal use only)"""
        if self.process and self.process.stdin:
            self.process.stdin.write(command + '\n')
            self.process.stdin.flush()

    def _drain_output(self, timeout: float = 0.1) -> Tuple[str, str]:
        """Drain output queues with timeout"""
        stdout_lines = []
        stderr_lines = []

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                line = self.stdout_queue.get_nowait()
                stdout_lines.append(line.rstrip('\n'))
            except Empty:
                pass

            try:
                line = self.stderr_queue.get_nowait()
                stderr_lines.append(line.rstrip('\n'))
            except Empty:
                pass

            time.sleep(0.01)

        return '\n'.join(stdout_lines), '\n'.join(stderr_lines)

    def execute(self, command: str, timeout: float = 30.0) -> Tuple[bool, str, str]:
        """
        Execute command in persistent shell

        Args:
            command: Command to execute
            timeout: Maximum time to wait for command output

        Returns:
            Tuple of (success, stdout, stderr)
        """
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                # Shell died, restart it
                self._start_shell()

            # Clear any pending output
            self._drain_output(timeout=0.1)

            # Use a unique marker to detect command completion
            marker = f"__CMD_DONE_{int(time.time() * 1000000)}__"
            exit_code_var = f"__EXIT_CODE_{int(time.time() * 1000000)}__"

            # Send command sequence (platform-specific):
            # 1. Execute the user command
            # 2. Capture exit code
            # 3. Print unique marker with exit code
            self._send_raw_command(command)

            if self.is_windows:
                # Windows cmd.exe syntax
                self._send_raw_command(f'set {exit_code_var}=%ERRORLEVEL%')
                self._send_raw_command(f'echo {marker}:%{exit_code_var}%')
            else:
                # Unix bash syntax
                self._send_raw_command(f'{exit_code_var}=$?')
                self._send_raw_command(f'echo "{marker}:${exit_code_var}"')

            # Collect output until we see the marker
            stdout_lines = []
            stderr_lines = []
            exit_code = 0
            found_marker = False

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    line = self.stdout_queue.get(timeout=0.1)
                    line = line.rstrip('\n')

                    # Check for completion marker
                    if line.startswith(marker):
                        parts = line.split(':')
                        if len(parts) == 2:
                            try:
                                exit_code = int(parts[1])
                            except ValueError:
                                pass
                        found_marker = True
                        break

                    stdout_lines.append(line)
                except Empty:
                    pass

                try:
                    line = self.stderr_queue.get_nowait()
                    stderr_lines.append(line.rstrip('\n'))
                except Empty:
                    pass

            if not found_marker:
                return False, '\n'.join(stdout_lines), "Command timed out"

            # Drain any remaining output
            extra_stdout, extra_stderr = self._drain_output(timeout=0.2)
            if extra_stdout:
                stdout_lines.append(extra_stdout)
            if extra_stderr:
                stderr_lines.append(extra_stderr)

            stdout = '\n'.join(stdout_lines)
            stderr = '\n'.join(stderr_lines)

            return exit_code == 0, stdout, stderr

    def get_cwd(self) -> str:
        """Get current working directory of the shell"""
        if self.is_windows:
            # Windows: 'cd' without arguments shows current directory
            # Or use 'echo %CD%'
            success, stdout, _ = self.execute('cd')
        else:
            # Unix: use pwd
            success, stdout, _ = self.execute('pwd')

        if success and stdout:
            return stdout.strip()
        return self.initial_cwd

    def reset(self):
        """Reset shell to initial state"""
        self._start_shell()

    def _cleanup_process(self):
        """Clean up the shell process"""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

    def close(self):
        """Close the persistent shell session"""
        with self.lock:
            self._cleanup_process()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
