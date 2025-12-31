#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E Test Runner for fixture cases

Usage:
    python tests/e2e/test_e2e_cases.py [case1|case2|case3|all]
"""

import os
import sys
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path
from typing import Tuple, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agent.loop import AgentLoop


class E2ETestRunner:
    """Runner for E2E test cases"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures" / "e2e-cases"
        self.results = {}

    def log(self, msg: str):
        """Print log message"""
        print(f"  {msg}")

    def run_cmake_build(self, project_dir: Path) -> Tuple[bool, str]:
        """Run cmake build in project directory"""
        build_dir = project_dir / "build"
        build_dir.mkdir(exist_ok=True)

        # cmake configure
        result = subprocess.run(
            ["cmake", ".."],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            return False, f"CMake configure failed:\n{result.stderr}"

        # cmake build
        result = subprocess.run(
            ["cmake", "--build", "."],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            return False, f"CMake build failed:\n{result.stderr}"

        return True, "Build succeeded"

    def run_tests(self, project_dir: Path) -> Tuple[bool, str]:
        """Run ctest in project directory"""
        build_dir = project_dir / "build"

        result = subprocess.run(
            ["ctest", "--output-on-failure"],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            return False, f"Tests failed:\n{result.stdout}\n{result.stderr}"

        return True, "All tests passed"

    def run_agent(self, project_dir: Path, prompt: str) -> Tuple[bool, str]:
        """Run AI agent on project with given prompt"""
        try:
            agent = AgentLoop(project_root=str(project_dir))

            # Hook to print tool calls if verbose
            if self.verbose and hasattr(agent, 'tool_executor'):
                original_execute = agent.tool_executor.execute_tool
                def verbose_execute(tool_name, arguments):
                    print(f"\n    [TOOL] {tool_name}")
                    if "file" in str(arguments):
                        file_path = arguments.get('file_path') or arguments.get('path', '')
                        if file_path:
                            print(f"           file: {Path(file_path).name}")
                    result = original_execute(tool_name, arguments)
                    if hasattr(result, 'success'):
                        status = "✓" if result.success else "✗"
                        print(f"           {status}")
                    return result
                agent.tool_executor.execute_tool = verbose_execute

            response = agent.run(prompt)
            return True, response
        except Exception as e:
            import traceback
            return False, f"Agent error: {e}\n{traceback.format_exc()}"

    def setup_temp_project(self, case_dir: Path) -> Path:
        """Copy case to temp directory for testing"""
        temp_dir = Path(tempfile.mkdtemp(prefix="e2e_test_"))
        shutil.copytree(case_dir, temp_dir / case_dir.name)
        return temp_dir / case_dir.name

    def cleanup_temp(self, temp_dir: Path):
        """Clean up temporary directory"""
        try:
            shutil.rmtree(temp_dir.parent)
        except Exception:
            pass

    def test_case1_implement_function(self) -> bool:
        """Test Case 1: Implement function from scratch"""
        print("\n" + "=" * 60)
        print("Case 1: Implement Function")
        print("=" * 60)

        case_dir = self.fixtures_dir / "case1-implement-function"
        prompt_file = case_dir / "prompt.txt"

        if not prompt_file.exists():
            self.log("[SKIP] prompt.txt not found")
            return False

        prompt = prompt_file.read_text().strip()
        self.log(f"Prompt: {prompt}")

        # Setup temp project
        temp_project = self.setup_temp_project(case_dir)
        self.log(f"Temp project: {temp_project}")

        try:
            # Run AI agent
            self.log("Running AI agent...")
            success, response = self.run_agent(temp_project, prompt)
            if not success:
                self.log(f"[FAIL] Agent failed: {response}")
                return False
            if self.verbose:
                self.log(f"Agent response: {response[:500]}...")

            # Build project
            self.log("Building project...")
            success, msg = self.run_cmake_build(temp_project)
            if not success:
                self.log(f"[FAIL] {msg}")
                return False
            self.log("[OK] Build succeeded")

            # Run tests
            self.log("Running tests...")
            success, msg = self.run_tests(temp_project)
            if not success:
                self.log(f"[FAIL] {msg}")
                return False
            self.log("[OK] Tests passed")

            print("\n[PASS] Case 1: Implement Function")
            return True

        finally:
            self.cleanup_temp(temp_project)

    def test_case2_fix_compile_error(self) -> bool:
        """Test Case 2: Fix compile errors"""
        print("\n" + "=" * 60)
        print("Case 2: Fix Compile Error")
        print("=" * 60)

        case_dir = self.fixtures_dir / "case2-fix-compile-error"
        prompt_file = case_dir / "prompt.txt"

        if not prompt_file.exists():
            self.log("[SKIP] prompt.txt not found")
            return False

        prompt = prompt_file.read_text().strip()
        self.log(f"Prompt: {prompt}")

        # Setup temp project
        temp_project = self.setup_temp_project(case_dir)
        self.log(f"Temp project: {temp_project}")

        try:
            # Verify initial build fails
            self.log("Verifying initial build fails...")
            success, _ = self.run_cmake_build(temp_project)
            if success:
                self.log("[WARN] Initial build should fail but succeeded")

            # Clean build dir for fresh start
            build_dir = temp_project / "build"
            if build_dir.exists():
                shutil.rmtree(build_dir)

            # Run AI agent
            self.log("Running AI agent...")
            success, response = self.run_agent(temp_project, prompt)
            if not success:
                self.log(f"[FAIL] Agent failed: {response}")
                return False
            if self.verbose:
                self.log(f"Agent response: {response[:500]}...")

            # Build project (should now succeed)
            self.log("Building project after fix...")
            success, msg = self.run_cmake_build(temp_project)
            if not success:
                self.log(f"[FAIL] {msg}")
                return False
            self.log("[OK] Build succeeded after fix")

            # Run tests
            self.log("Running tests...")
            success, msg = self.run_tests(temp_project)
            if not success:
                self.log(f"[FAIL] {msg}")
                return False
            self.log("[OK] Tests passed")

            print("\n[PASS] Case 2: Fix Compile Error")
            return True

        finally:
            self.cleanup_temp(temp_project)

    def test_case3_tdd_write_tests(self) -> bool:
        """Test Case 3: TDD - implement based on tests"""
        print("\n" + "=" * 60)
        print("Case 3: TDD Write Tests")
        print("=" * 60)

        case_dir = self.fixtures_dir / "case3-tdd-write-tests"
        prompt_file = case_dir / "prompt.txt"

        if not prompt_file.exists():
            self.log("[SKIP] prompt.txt not found")
            return False

        prompt = prompt_file.read_text().strip()
        self.log(f"Prompt: {prompt}")

        # Setup temp project
        temp_project = self.setup_temp_project(case_dir)
        self.log(f"Temp project: {temp_project}")

        try:
            # Run AI agent
            self.log("Running AI agent...")
            success, response = self.run_agent(temp_project, prompt)
            if not success:
                self.log(f"[FAIL] Agent failed: {response}")
                return False
            if self.verbose:
                self.log(f"Agent response: {response[:500]}...")

            # Build project
            self.log("Building project...")
            success, msg = self.run_cmake_build(temp_project)
            if not success:
                self.log(f"[FAIL] {msg}")
                return False
            self.log("[OK] Build succeeded")

            # Run tests
            self.log("Running tests...")
            success, msg = self.run_tests(temp_project)
            if not success:
                self.log(f"[FAIL] {msg}")
                return False
            self.log("[OK] Tests passed")

            print("\n[PASS] Case 3: TDD Write Tests")
            return True

        finally:
            self.cleanup_temp(temp_project)

    def run_all(self, filter_ids: Optional[list] = None) -> dict:
        """Run all test cases

        Args:
            filter_ids: List of case IDs to run (e.g., [1, 3]). None means all.
        """
        all_cases = {
            1: ("case1", self.test_case1_implement_function),
            2: ("case2", self.test_case2_fix_compile_error),
            3: ("case3", self.test_case3_tdd_write_tests),
        }

        # Filter cases if specified
        if filter_ids:
            cases_to_run = {k: v for k, v in all_cases.items() if k in filter_ids}
        else:
            cases_to_run = all_cases

        results = {}
        for case_id, (name, test_func) in cases_to_run.items():
            results[name] = test_func()

        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        for case, passed in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {case}")

        passed_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        print(f"\nTotal: {passed_count}/{total_count} passed ({passed_count/total_count*100:.0f}%)")

        return results


def main():
    parser = argparse.ArgumentParser(description="Run E2E test cases")
    parser.add_argument(
        "-f", "--filter",
        type=str,
        default=None,
        help="Filter cases by ID (e.g., '1,3' or '2')"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    args = parser.parse_args()

    runner = E2ETestRunner(verbose=args.verbose)

    # Parse filter IDs
    filter_ids = None
    if args.filter:
        filter_ids = [int(x.strip()) for x in args.filter.split(",")]

    results = runner.run_all(filter_ids=filter_ids)
    sys.exit(0 if all(results.values()) else 1)



if __name__ == "__main__":
    main()
