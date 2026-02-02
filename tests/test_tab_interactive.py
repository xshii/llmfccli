#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Tab Completion Test

This script demonstrates the tab completion functionality.
Press Tab to see completions!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from backend.cli.completers import ClaudeQwenCompleter, PathCompleter, FileNameCompleter, CombinedCompleter


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Tab 补全交互式测试                                  ║
╚══════════════════════════════════════════════════════════════╝

按 Tab 键触发补全！试试这些：

1. 输入 /he 然后按 Tab
2. 输入 /model 然后按空格和 Tab
3. 输入 /model l 然后按 Tab
4. 输入 /cmd 然后按空格和 Tab
5. 输入 /cmd ls 然后按 Tab

输入 'quit' 或 'exit' 退出

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    # Create completers
    command_completer = ClaudeQwenCompleter()
    path_completer = PathCompleter()
    filename_completer = FileNameCompleter()
    combined_completer = CombinedCompleter([
        command_completer,
        path_completer,
        filename_completer
    ])

    # Create session with tab completion
    session = PromptSession(
        history=InMemoryHistory(),
        completer=combined_completer,
        complete_while_typing=False,  # Only complete on Tab
    )

    while True:
        try:
            # Get user input
            text = session.prompt('> ')

            # Check for exit
            if text.lower() in ['quit', 'exit', 'q']:
                print("\n再见！")
                break

            # Just echo what was typed
            if text:
                print(f"您输入了: {text}")

                # Show helpful hints
                if text.startswith('/model '):
                    print("💡 提示: /model 支持子命令: list, create, show, delete, pull, health")
                elif text.startswith('/cmd '):
                    print("💡 提示: /cmd 支持常用 shell 命令补全")
                elif text.startswith('/'):
                    print("💡 提示: 尝试在命令后加空格，然后按 Tab 查看子命令")

        except KeyboardInterrupt:
            print("\n\n使用 'quit' 或 Ctrl+D 退出")
            continue
        except EOFError:
            print("\n\n再见！")
            break


if __name__ == '__main__':
    main()
