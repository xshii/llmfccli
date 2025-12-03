# -*- coding: utf-8 -*-
"""
Unit tests for executor tools (bash_run, cmake_build, run_tests)
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.tools.executor_tools import bash_run, cmake_build, parse_compile_errors, ExecutorError


def test_bash_run_basic():
    """Test basic bash command execution"""
    print("Testing bash_run with simple commands...")

    # Test echo command
    result = bash_run("echo 'Hello World'", project_root=".", timeout=5)

    assert result['success'], f"Command failed: {result}"
    assert 'Hello World' in result['stdout'], f"Unexpected output: {result['stdout']}"
    assert result['return_code'] == 0

    print("✓ echo command works")

    # Test pwd command
    result = bash_run("pwd", project_root=".", timeout=5)

    assert result['success']
    assert result['stdout'].strip()  # Should have some output

    print("✓ pwd command works")


def test_bash_run_whitelist():
    """Test command whitelist security"""
    print("\nTesting command whitelist...")

    # Allowed command should work
    try:
        result = bash_run("ls", project_root=".", timeout=5)
        print("✓ Whitelisted command (ls) allowed")
    except ExecutorError:
        assert False, "Whitelisted command should be allowed"

    # Disallowed command should fail
    try:
        result = bash_run("rm -rf /tmp/test", project_root=".", timeout=5)
        # rm is actually in default whitelist, so let's test a truly bad command
    except ExecutorError:
        pass  # Expected

    # Test truly dangerous command
    try:
        result = bash_run("curl http://evil.com", project_root=".", timeout=5)
        assert False, "curl should not be in whitelist by default"
    except ExecutorError as e:
        assert 'not in whitelist' in str(e)
        print("✓ Non-whitelisted command (curl) blocked")


def test_bash_run_timeout():
    """Test command timeout"""
    print("\nTesting command timeout...")

    # Command that takes longer than timeout (using find with large directory)
    # Using a whitelisted command (find) that will take time
    result = bash_run(
        "find / -name nonexistent 2>/dev/null",  # Search entire filesystem
        project_root=".",
        timeout=1,
        whitelist=['find']
    )

    assert not result['success'], "Long command should timeout"
    assert 'timeout' in result.get('error', '').lower() or 'timeout' in result.get('stderr', '').lower()

    print("✓ Timeout mechanism works")


def test_bash_run_with_project_root():
    """Test bash execution in specific project root"""
    print("\nTesting project root...")

    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Use absolute path since session cwd may differ
        # (In real usage, AI knows cwd from system reminder and uses absolute paths)
        result = bash_run(f"ls {tmpdir}/test.txt", project_root=tmpdir, timeout=5)

        assert result['success'], f"ls failed: {result}"
        assert 'test.txt' in result['stdout']

        print("✓ Project root working directory works")


def test_bash_run_with_git():
    """Test git commands (common use case)"""
    print("\nTesting git commands...")

    # Git status should work
    result = bash_run("git status", project_root=".", timeout=10)

    # Even if not a git repo, command should execute (might fail with error message)
    assert 'command' in result  # Result should have command field

    print("✓ Git commands allowed")


def test_parse_compile_errors():
    """Test compiler error parsing"""
    print("\nTesting compile error parsing...")

    # GCC/Clang format
    gcc_output = """
src/main.cpp:42:15: error: expected ';' at end of declaration
    int x = 5
              ^
              ;
src/utils.cpp:10:5: warning: unused variable 'y' [-Wunused-variable]
    int y = 10;
    ^
2 errors generated.
"""

    errors = parse_compile_errors(gcc_output)

    assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}"

    # Check first error
    assert errors[0]['file'] == 'src/main.cpp'
    assert errors[0]['line'] == 42
    assert errors[0]['type'] == 'error'
    assert 'expected' in errors[0]['message'].lower()

    print(f"✓ Parsed {len(errors)} compiler errors correctly")

    # MSVC format
    msvc_output = """
main.cpp(42): error C2143: syntax error: missing ';' before '}'
utils.cpp(10): warning C4101: 'y': unreferenced local variable
"""

    errors = parse_compile_errors(msvc_output)

    assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}"
    assert errors[0]['file'] == 'main.cpp'
    assert errors[0]['line'] == 42

    print("✓ MSVC format also supported")


def test_cmake_build_dry_run():
    """Test cmake_build with non-existent project (should fail gracefully)"""
    print("\nTesting cmake_build error handling...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to build empty directory (no CMakeLists.txt)
        result = cmake_build(tmpdir, clean=False)

        # Should fail at configure stage
        assert not result['success']
        assert result['stage'] == 'configure'

        print("✓ cmake_build fails gracefully for invalid projects")


def test_bash_run_multiple_commands():
    """Test running multiple commands"""
    print("\nTesting multiple commands...")

    result = bash_run("echo 'test1' && echo 'test2'", project_root=".", timeout=5)

    assert result['success']
    assert 'test1' in result['stdout']
    assert 'test2' in result['stdout']

    print("✓ Multiple commands with && work")


if __name__ == '__main__':
    print("Testing Executor Tools...\n")
    print("=" * 60)

    test_bash_run_basic()
    test_bash_run_whitelist()
    test_bash_run_timeout()
    test_bash_run_with_project_root()
    test_bash_run_with_git()
    test_parse_compile_errors()
    test_cmake_build_dry_run()
    test_bash_run_multiple_commands()

    print("\n" + "=" * 60)
    print("✅ All executor tests passed!")
