#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test /cmd hanging issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.shell_session import PersistentShellSession
import time


def test_simple_command():
    """Test simple command execution"""
    print("Testing simple command (echo)...")

    with PersistentShellSession() as shell:
        start = time.time()
        success, stdout, stderr = shell.execute('echo "Hello World"', timeout=5.0)
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.2f}s")
        print(f"  Success: {success}")
        print(f"  Stdout: {repr(stdout)}")
        print(f"  Stderr: {repr(stderr)}")

        if elapsed > 4:
            print("  ⚠ WARNING: Command took longer than expected!")
        else:
            print("  ✓ Command completed quickly")

    return success


def test_ls_command():
    """Test ls command"""
    print("\nTesting ls command...")

    with PersistentShellSession() as shell:
        start = time.time()
        success, stdout, stderr = shell.execute('ls -la', timeout=5.0)
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.2f}s")
        print(f"  Success: {success}")
        print(f"  Output lines: {len(stdout.splitlines())}")

        if elapsed > 4:
            print("  ⚠ WARNING: Command took longer than expected!")
        else:
            print("  ✓ Command completed quickly")

    return success


def test_pwd_command():
    """Test pwd command"""
    print("\nTesting pwd command...")

    with PersistentShellSession() as shell:
        start = time.time()
        success, stdout, stderr = shell.execute('pwd', timeout=5.0)
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.2f}s")
        print(f"  Success: {success}")
        print(f"  Stdout: {repr(stdout)}")

        if elapsed > 4:
            print("  ⚠ WARNING: Command took longer than expected!")
        else:
            print("  ✓ Command completed quickly")

    return success


def test_git_status():
    """Test git status command"""
    print("\nTesting git status command...")

    with PersistentShellSession() as shell:
        start = time.time()
        success, stdout, stderr = shell.execute('git status --short', timeout=5.0)
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.2f}s")
        print(f"  Success: {success}")
        print(f"  Output lines: {len(stdout.splitlines())}")

        if elapsed > 4:
            print("  ⚠ WARNING: Command took longer than expected!")
        else:
            print("  ✓ Command completed quickly")

    return success


if __name__ == "__main__":
    print("=" * 60)
    print("DEBUG: Testing /cmd command execution")
    print("=" * 60)

    try:
        test_simple_command()
        test_ls_command()
        test_pwd_command()
        test_git_status()

        print("\n" + "=" * 60)
        print("✓ All tests completed")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
