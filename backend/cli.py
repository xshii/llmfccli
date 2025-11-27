# -*- coding: utf-8 -*-
"""
CLI 入口点 - 向后兼容层

此文件保持与旧代码的向后兼容性，
重定向到重构后的 backend/cli/ 模块
"""

# 从新模块导入
from backend.cli.main import CLI


# 为了保持向后兼容，重新导出 main 函数
def main():
    """主入口点"""
    import argparse

    parser = argparse.ArgumentParser(description='Claude-Qwen AI 编程助手')
    parser.add_argument('--root', '-r', help='项目根目录', default=None)
    parser.add_argument('--skip-precheck', action='store_true',
                        help='跳过环境预检查（用于测试或离线环境）')
    parser.add_argument('--version', '-v', action='version', version='0.1.0')

    args = parser.parse_args()

    # 初始化并运行 CLI
    cli = CLI(project_root=args.root, skip_precheck=args.skip_precheck)

    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main()
