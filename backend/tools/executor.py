# -*- coding: utf-8 -*-
"""
Executor tools for running commands and building projects
"""

import re
import subprocess
import time
import shlex
from typing import Dict, Any, Optional, List
from pathlib import Path


class ExecutorError(Exception):
    """Base exception for executor operations"""
    pass


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


def bash_run(command: str,
             project_root: str,
             timeout: int = 60,
             whitelist: Optional[List[str]] = None,
             session_id: Optional[str] = None,
             verbose: bool = True) -> Dict[str, Any]:
    """
    Execute bash command with security checks

    Args:
        command: Command to execute
        project_root: Project root directory
        timeout: Timeout in seconds
        whitelist: Allowed command prefixes (security)
        session_id: Optional session ID for persistent shell
        verbose: Print execution status (default: True)

    Returns:
        Dict with stdout, stderr, return_code, duration
    """
    # Default whitelist from config
    if whitelist is None:
        whitelist = [
            'cmake', 'make', 'g++', 'clang++', 'gcc', 'clang',
            'ctest', 'git', 'mkdir', 'cd', 'ls', 'cat',
            'echo', 'pwd', 'which', 'find', 'grep',
            'python', 'python3', 'pip', 'pip3'
        ]

    # Security check: validate command against whitelist
    command_parts = shlex.split(command)
    if not command_parts:
        raise ExecutorError("Empty command")

    base_command = command_parts[0]

    # Allow full paths if basename matches whitelist
    if '/' in base_command:
        base_command = Path(base_command).name

    # Check whitelist
    if not any(base_command.startswith(allowed) for allowed in whitelist):
        raise ExecutorError(
            f"Command '{base_command}' not in whitelist. "
            f"Allowed: {', '.join(whitelist)}"
        )

    # Print TODO: executing command
    if verbose:
        print(f"\n[TODO] 执行命令: {command}")
        print(f"[TODO] 工作目录: {project_root}")
        print(f"[TODO] 超时设置: {timeout}秒")

    # Use persistent session or create new one
    if session_id:
        if session_id not in _sessions:
            _sessions[session_id] = BashSession(project_root, timeout)
        session = _sessions[session_id]
    else:
        # One-shot execution
        session = BashSession(project_root, timeout)

    try:
        result = session.execute(command, timeout)

        # Add command to result
        result['command'] = command
        result['project_root'] = str(project_root)

        # Print result
        if verbose:
            status = "✓ 成功" if result['success'] else "✗ 失败"
            print(f"[TODO] 执行结果: {status} (耗时: {result['duration']:.2f}秒)")
            if result['return_code'] != 0:
                print(f"[TODO] 返回码: {result['return_code']}")

        return result

    finally:
        # Close one-shot sessions
        if not session_id:
            session.close()


def cmake_build(project_root: str,
                build_dir: str = "build",
                config: str = "Release",
                target: Optional[str] = None,
                clean: bool = False,
                verbose: bool = True) -> Dict[str, Any]:
    """
    Build project with CMake

    Args:
        project_root: Project root directory
        build_dir: Build directory name
        config: Build configuration (Debug/Release)
        target: Optional specific target to build
        clean: Clean before building
        verbose: Print execution status (default: True)

    Returns:
        Build result dict
    """
    if verbose:
        print("\n" + "=" * 60)
        print(f"[TODO] CMake 构建任务开始")
        print(f"[TODO] 项目路径: {project_root}")
        print(f"[TODO] 构建目录: {build_dir}")
        print(f"[TODO] 构建配置: {config}")
        if target:
            print(f"[TODO] 构建目标: {target}")
        if clean:
            print(f"[TODO] 清理模式: 启用")
        print("=" * 60)

    build_path = Path(project_root) / build_dir

    results = []

    # Clean if requested
    if clean and build_path.exists():
        if verbose:
            print(f"\n[TODO] 步骤 1/4: 清理构建目录")
        result = bash_run(
            f"rm -rf {build_dir}",
            project_root,
            timeout=10,
            whitelist=['rm'],
            verbose=verbose
        )
        results.append(('clean', result))

    # Create build directory
    if not build_path.exists():
        step_num = 2 if clean else 1
        if verbose:
            print(f"\n[TODO] 步骤 {step_num}/4: 创建构建目录")
        result = bash_run(
            f"mkdir -p {build_dir}",
            project_root,
            timeout=5,
            verbose=verbose
        )
        results.append(('mkdir', result))

    # Configure
    step_num = 3 if clean or not build_path.exists() else 1
    if verbose:
        print(f"\n[TODO] 步骤 {step_num}/4: CMake 配置")
    result = bash_run(
        f"cmake -S . -B {build_dir} -DCMAKE_BUILD_TYPE={config}",
        project_root,
        timeout=60,
        verbose=verbose
    )
    results.append(('configure', result))

    if not result['success']:
        if verbose:
            print(f"\n[TODO] ✗ 构建失败: CMake 配置阶段出错")
        return {
            'success': False,
            'stage': 'configure',
            'error': result['stderr'] or result['stdout'],
            'results': results,
        }

    # Build
    if verbose:
        print(f"\n[TODO] 步骤 4/4: 编译构建")
    build_cmd = f"cmake --build {build_dir}"
    if target:
        build_cmd += f" --target {target}"

    result = bash_run(build_cmd, project_root, timeout=300, verbose=verbose)
    results.append(('build', result))

    if not result['success']:
        if verbose:
            print(f"\n[TODO] ✗ 构建失败: 编译阶段出错")
        return {
            'success': False,
            'stage': 'build',
            'error': result['stderr'] or result['stdout'],
            'results': results,
        }

    if verbose:
        print(f"\n[TODO] ✓ CMake 构建成功完成!")
        print("=" * 60 + "\n")

    return {
        'success': True,
        'build_dir': str(build_path),
        'config': config,
        'results': results,
    }


def run_tests(project_root: str,
              build_dir: str = "build",
              test_pattern: Optional[str] = None,
              timeout: int = 120,
              verbose: bool = True) -> Dict[str, Any]:
    """
    Run tests with ctest

    Args:
        project_root: Project root directory
        build_dir: Build directory name
        test_pattern: Optional test name pattern
        timeout: Timeout in seconds
        verbose: Print execution status (default: True)

    Returns:
        Test result dict
    """
    if verbose:
        print("\n" + "=" * 60)
        print(f"[TODO] 测试任务开始")
        print(f"[TODO] 项目路径: {project_root}")
        print(f"[TODO] 构建目录: {build_dir}")
        if test_pattern:
            print(f"[TODO] 测试模式: {test_pattern}")
        print(f"[TODO] 超时设置: {timeout}秒")
        print("=" * 60)

    build_path = Path(project_root) / build_dir

    if not build_path.exists():
        if verbose:
            print(f"\n[TODO] ✗ 错误: 构建目录不存在: {build_path}")
        raise ExecutorError(f"Build directory not found: {build_path}")

    # Build ctest command
    cmd = f"cd {build_dir} && ctest --output-on-failure"
    if test_pattern:
        cmd += f" -R {test_pattern}"

    if verbose:
        print(f"\n[TODO] 运行测试...")

    result = bash_run(cmd, project_root, timeout=timeout, verbose=verbose)

    # Parse test results
    stdout = result['stdout']

    # Simple parsing: look for "X tests passed, Y tests failed"
    import re
    match = re.search(r'(\d+) tests? passed.*?(\d+) tests? failed', stdout)

    if match:
        passed = int(match.group(1))
        failed = int(match.group(2))
    else:
        # Try alternative format
        match = re.search(r'(\d+)/(\d+) Test', stdout)
        if match:
            passed = int(match.group(1))
            total = int(match.group(2))
            failed = total - passed
        else:
            passed = 0
            failed = 0

    total = passed + failed
    success = result['success'] and failed == 0

    if verbose:
        print(f"\n[TODO] 测试结果:")
        print(f"[TODO]   总计: {total} 个测试")
        print(f"[TODO]   通过: {passed} ✓")
        if failed > 0:
            print(f"[TODO]   失败: {failed} ✗")
        print(f"[TODO]   耗时: {result['duration']:.2f}秒")

        if success:
            print(f"\n[TODO] ✓ 所有测试通过!")
        else:
            print(f"\n[TODO] ✗ 有测试失败!")
        print("=" * 60 + "\n")

    return {
        'success': success,
        'passed': passed,
        'failed': failed,
        'total': total,
        'output': stdout,
        'duration': result['duration'],
    }


def parse_compile_errors(output: str) -> List[Dict[str, Any]]:
    """
    Parse compiler error messages

    Args:
        output: Compiler output (stdout + stderr)

    Returns:
        List of error dicts with file, line, column, message
    """
    errors = []

    # Patterns for different compilers
    patterns = [
        # GCC/Clang: file.cpp:line:column: error: message
        r'([^:]+):(\d+):(\d+):\s*(error|warning):\s*(.+)',
        # MSVC: file.cpp(line): error C1234: message
        r'([^(]+)\((\d+)\):\s*(error|warning)\s+\w+:\s*(.+)',
    ]

    for line in output.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                if len(match.groups()) == 5:  # GCC/Clang format
                    errors.append({
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'column': int(match.group(3)),
                        'type': match.group(4),
                        'message': match.group(5).strip(),
                    })
                elif len(match.groups()) == 4:  # MSVC format
                    errors.append({
                        'file': match.group(1),
                        'line': int(match.group(2)),
                        'column': 0,
                        'type': match.group(3),
                        'message': match.group(4).strip(),
                    })
                break

    return errors


def close_all_sessions():
    """Close all persistent bash sessions"""
    for session in _sessions.values():
        session.close()
    _sessions.clear()
