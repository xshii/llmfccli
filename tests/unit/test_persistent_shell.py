#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for persistent shell session

Tests the cross-platform persistent shell functionality:
- Linux/Mac: Uses /bin/bash
- Windows: Uses cmd.exe

Note: These tests run on the current platform.
Windows-specific behavior is tested when running on Windows.
"""

import os
import sys
import tempfile
import platform
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.shell_session import PersistentShellSession

IS_WINDOWS = platform.system() == 'Windows'


def test_basic_command():
    """Test basic command execution"""
    with PersistentShellSession() as session:
        success, stdout, stderr = session.execute('echo "hello world"')

        assert success, f"Command failed: {stderr}"
        assert 'hello world' in stdout, f"Unexpected output: {stdout}"
        print("✓ Test basic command execution passed")


def test_persistent_directory():
    """Test that directory changes persist across commands"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, 'test_subdir')
        os.makedirs(test_dir)

        with PersistentShellSession(initial_cwd=tmpdir) as session:
            # Change directory
            success, stdout, stderr = session.execute('cd test_subdir')
            assert success, f"cd failed: {stderr}"

            # Verify we're still in the subdirectory
            success, stdout, stderr = session.execute('pwd')
            assert success, f"pwd failed: {stderr}"
            assert 'test_subdir' in stdout, f"Directory didn't persist: {stdout}"

            # Verify get_cwd() works
            cwd = session.get_cwd()
            assert 'test_subdir' in cwd, f"get_cwd() returned wrong directory: {cwd}"

            print("✓ Test persistent directory passed")


def test_persistent_environment():
    """Test that environment variables persist across commands"""
    with PersistentShellSession() as session:
        # Set environment variable (platform-specific syntax)
        if IS_WINDOWS:
            # Windows: set VAR=value
            success, stdout, stderr = session.execute('set TEST_VAR=test_value')
            assert success, f"set failed: {stderr}"

            # Verify variable persists (Windows: %VAR%)
            success, stdout, stderr = session.execute('echo %TEST_VAR%')
        else:
            # Unix: export VAR=value
            success, stdout, stderr = session.execute('export TEST_VAR="test_value"')
            assert success, f"export failed: {stderr}"

            # Verify variable persists (Unix: $VAR)
            success, stdout, stderr = session.execute('echo $TEST_VAR')

        assert success, f"echo failed: {stderr}"
        assert 'test_value' in stdout, f"Environment variable didn't persist: {stdout}"

        print("✓ Test persistent environment passed")


def test_command_failure():
    """Test that command failures are properly reported"""
    with PersistentShellSession() as session:
        # Run a command that will fail
        success, stdout, stderr = session.execute('ls /nonexistent_directory_12345')

        assert not success, "Command should have failed but succeeded"
        print("✓ Test command failure detection passed")


def test_reset_session():
    """Test that session reset works correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, 'test_subdir')
        os.makedirs(test_dir)

        session = PersistentShellSession(initial_cwd=tmpdir)

        try:
            # Change directory
            session.execute('cd test_subdir')
            cwd = session.get_cwd()
            assert 'test_subdir' in cwd, f"cd didn't work: {cwd}"

            # Reset session
            session.reset()

            # Verify we're back to initial directory
            cwd = session.get_cwd()
            assert cwd.rstrip('/') == tmpdir.rstrip('/'), f"Reset didn't restore initial directory: {cwd} != {tmpdir}"

            print("✓ Test session reset passed")
        finally:
            session.close()


def test_multiline_output():
    """Test commands with multi-line output"""
    with PersistentShellSession() as session:
        if IS_WINDOWS:
            # Windows: use multiple echo commands
            success, stdout, stderr = session.execute('echo line1 && echo line2 && echo line3')
        else:
            # Unix: use echo -e with \n
            success, stdout, stderr = session.execute('echo -e "line1\\nline2\\nline3"')

        assert success, f"Command failed: {stderr}"
        lines = stdout.strip().split('\n')
        assert len(lines) >= 3, f"Expected multi-line output, got: {stdout}"

        print("✓ Test multiline output passed")


def test_piped_commands():
    """Test commands with pipes"""
    with PersistentShellSession() as session:
        if IS_WINDOWS:
            # Windows: use findstr instead of grep
            success, stdout, stderr = session.execute('echo hello world | findstr hello')
        else:
            # Unix: use grep
            success, stdout, stderr = session.execute('echo "hello world" | grep hello')

        assert success, f"Piped command failed: {stderr}"
        assert 'hello' in stdout, f"Pipe didn't work: {stdout}"

        print("✓ Test piped commands passed")


def main():
    """Run all tests"""
    print("\n=== Testing Persistent Shell Session ===")
    print(f"Platform: {platform.system()}")
    print(f"Shell: {'cmd.exe' if IS_WINDOWS else '/bin/bash'}\n")

    try:
        test_basic_command()
        test_persistent_directory()
        test_persistent_environment()
        test_command_failure()
        test_reset_session()
        test_multiline_output()
        test_piped_commands()

        print("\n✅ All tests passed!\n")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
