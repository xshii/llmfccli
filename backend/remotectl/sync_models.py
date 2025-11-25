#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立脚本：同步 Ollama 模型

功能：
- 检查并拉取基础模型（base_models）
- 同步所有启用的自定义模型（models）
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.remotectl.model_manager import ModelManager


def main():
    """主函数"""
    print("=" * 60)
    print("模型同步脚本")
    print("=" * 60)
    print()

    manager = ModelManager()

    # 步骤 1: 确保基础模型存在
    print("步骤 1: 检查基础模型")
    print("-" * 60)
    base_results = manager.ensure_base_models()

    if not base_results:
        print("⚠ 配置中没有基础模型定义")
    else:
        print()
        print("基础模型状态：")
        all_base_ok = True
        for model_name, success in base_results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {model_name}")
            if not success:
                all_base_ok = False

        if not all_base_ok:
            print()
            print("⚠ 部分基础模型不可用，请检查网络连接或手动拉取")
            print("  提示：可以手动运行 'ollama pull <model_name>'")
            return 1

    print()

    # 步骤 2: 同步自定义模型
    print("步骤 2: 同步自定义模型")
    print("-" * 60)
    custom_results = manager.sync_all_models()

    if not custom_results:
        print("⚠ 配置中没有启用的自定义模型")
    else:
        print()
        print("自定义模型同步结果：")
        all_custom_ok = True
        for model_name, success in custom_results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {model_name}")
            if not success:
                all_custom_ok = False

        if not all_custom_ok:
            print()
            print("⚠ 部分自定义模型同步失败")
            return 1

    print()
    print("=" * 60)
    print("✓ 所有模型已同步完成")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
