# -*- coding: utf-8 -*-
"""
Pre-check utilities for verifying environment setup

此模块为向后兼容层，实际实现在 checks/ 子目录中。
"""

from pathlib import Path
from typing import List, Optional

import yaml

from .checks import (
    PreCheckResult,
    check_ssh_tunnel,
    check_ollama_connection,
    check_ollama_model,
    test_ollama_hello,
    get_ollama_config,
    check_and_kill_local_ollama,
    check_project_structure,
)

# 重新导出供外部使用
__all__ = [
    'PreCheckResult',
    'PreCheck',
    'get_ollama_config',
]


class PreCheck:
    """Environment pre-check utilities (向后兼容接口)"""

    # 静态方法直接委托给函数
    check_ssh_tunnel = staticmethod(check_ssh_tunnel)
    check_ollama_connection = staticmethod(check_ollama_connection)
    check_ollama_model = staticmethod(check_ollama_model)
    test_ollama_hello = staticmethod(test_ollama_hello)
    check_and_kill_local_ollama = staticmethod(check_and_kill_local_ollama)
    check_project_structure = staticmethod(check_project_structure)

    @classmethod
    def run_all_checks(cls, model_name: Optional[str] = None,
                       project_root: Optional[str] = None) -> List[PreCheckResult]:
        """
        Run all pre-checks

        Args:
            model_name: Ollama model to check (default: from config)
            project_root: Optional project root to validate

        Returns:
            List of PreCheckResult
        """
        results = []

        # 0. Check and kill local Ollama if using remote (must be first)
        results.append(check_and_kill_local_ollama())

        # 1. SSH Tunnel
        results.append(check_ssh_tunnel())

        # 2. Ollama Connection
        results.append(check_ollama_connection())

        # 3. Ollama Model
        results.append(check_ollama_model(model_name))

        # 4. Hello Test
        results.append(test_ollama_hello(model_name))

        # 5. Project Structure (if provided)
        if project_root:
            results.append(check_project_structure(project_root))

        return results

    @staticmethod
    def print_results(results: List[PreCheckResult], verbose: bool = False) -> bool:
        """
        Print check results

        Args:
            results: List of check results
            verbose: Show detailed information

        Returns:
            True if all checks passed
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
            from backend.llm.config import get_ssh_host
            ssh_host = get_ssh_host()
            for result in failed:
                if "SSH Tunnel" in result.name:
                    if ssh_host:
                        print(f"  • Start SSH tunnel: ssh -fN {ssh_host}")
                    else:
                        print("  • Configure ssh.host in config/llm.yaml")
                elif "Ollama Connection" in result.name:
                    print("  • Verify Ollama service is running on remote server")
                elif "Ollama Model" in result.name:
                    model = result.details.get('model', '(see config/llm.yaml)')
                    print(f"  • Pull model: ollama pull {model}")

        print()

        return all_passed


def main():
    """Run pre-checks as standalone script"""
    import argparse

    parser = argparse.ArgumentParser(description="Pre-check environment setup")
    parser.add_argument('--model', default=None, help='Ollama model name (default: from config/llm.yaml)')
    parser.add_argument('--project-root', help='Project root directory to validate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')

    args = parser.parse_args()

    results = PreCheck.run_all_checks(args.model, args.project_root)
    all_passed = PreCheck.print_results(results, args.verbose)

    return 0 if all_passed else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
