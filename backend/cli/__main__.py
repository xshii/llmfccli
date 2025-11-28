# -*- coding: utf-8 -*-
"""
允许通过 python -m backend.cli 运行
"""

from backend.cli.main import CLI
import argparse
import sys


def main():
    """主入口点"""
    parser = argparse.ArgumentParser(description='Claude-Qwen AI 编程助手')
    parser.add_argument('--root', '-r', help='项目根目录', default=None)
    parser.add_argument('--skip-precheck', action='store_true',
                        help='跳过环境预检查（用于测试或离线环境）')
    parser.add_argument('--version', '-v', action='version', version='0.1.0')

    args = parser.parse_args()

    cli = CLI(project_root=args.root, skip_precheck=args.skip_precheck)

    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
