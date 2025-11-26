#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TypeScript 集成测试

测试 VSCode 扩展的 TypeScript 代码（需要 Node.js 和 npm）
"""

import sys
import os
import subprocess
import shutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def check_prerequisites():
    """检查前置条件"""
    print("\n检查前置条件...")

    # Check Node.js
    if not shutil.which('node'):
        print("✗ Node.js 未安装")
        print("  请安装 Node.js: https://nodejs.org/")
        return False

    node_version = subprocess.run(['node', '--version'], capture_output=True, text=True)
    print(f"✓ Node.js {node_version.stdout.strip()}")

    # Check npm
    if not shutil.which('npm'):
        print("✗ npm 未安装")
        return False

    npm_version = subprocess.run(['npm', '--version'], capture_output=True, text=True)
    print(f"✓ npm {npm_version.stdout.strip()}")

    return True


def install_dependencies():
    """安装 npm 依赖"""
    extension_dir = os.path.join(project_root, 'vscode-extension')

    print("\n检查 npm 依赖...")
    node_modules = os.path.join(extension_dir, 'node_modules')

    if not os.path.exists(node_modules):
        print("安装 npm 依赖（首次运行可能需要几分钟）...")
        result = subprocess.run(
            ['npm', 'install'],
            cwd=extension_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("✗ npm install 失败:")
            print(result.stderr)
            return False

        print("✓ npm 依赖已安装")
    else:
        print("✓ npm 依赖已存在")

    return True


def compile_typescript():
    """编译 TypeScript"""
    extension_dir = os.path.join(project_root, 'vscode-extension')

    print("\n编译 TypeScript...")
    result = subprocess.run(
        ['npm', 'run', 'compile'],
        cwd=extension_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("✗ TypeScript 编译失败:")
        print(result.stderr)
        return False

    print("✓ TypeScript 编译成功")
    return True


def run_typescript_tests():
    """运行 TypeScript 测试"""
    extension_dir = os.path.join(project_root, 'vscode-extension')

    print("\n运行 TypeScript 测试...")
    print("=" * 70)

    result = subprocess.run(
        ['npm', 'test'],
        cwd=extension_dir,
        text=True
    )

    print("=" * 70)

    if result.returncode != 0:
        print("\n✗ TypeScript 测试失败")
        return False

    print("\n✓ TypeScript 测试通过")
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("VSCode 扩展 TypeScript 集成测试")
    print("=" * 70)

    try:
        # 1. 检查前置条件
        if not check_prerequisites():
            print("\n❌ 前置条件检查失败")
            print("\n💡 提示:")
            print("  此测试需要 Node.js 和 npm")
            print("  如果您只想测试 Python 端的 RPC 功能，请运行:")
            print("  python3 tests/run_rpc_tests.py")
            return 1

        # 2. 安装依赖
        if not install_dependencies():
            print("\n❌ 依赖安装失败")
            return 1

        # 3. 编译 TypeScript
        if not compile_typescript():
            print("\n❌ 编译失败")
            return 1

        # 4. 运行测试
        if not run_typescript_tests():
            print("\n❌ 测试失败")
            return 1

        print("\n" + "=" * 70)
        print("✅ 所有 TypeScript 测试通过")
        print("=" * 70)
        return 0

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 意外错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
