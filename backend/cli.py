"""
Command-line interface for Claude-Qwen
"""

import sys
import os
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent.loop import AgentLoop
from .llm.client import OllamaClient


class CLI:
    """Interactive CLI for Claude-Qwen"""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize CLI"""
        self.console = Console()
        self.project_root = project_root or str(Path.cwd())
        
        # Initialize agent
        self.client = OllamaClient()
        self.agent = AgentLoop(self.client, self.project_root)
        
        # Skip model check to avoid network requests
        
        # Setup prompt session
        history_file = Path.home() / '.claude_qwen_history'
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )
    
    def show_welcome(self):
        """Show welcome message"""
        welcome = """
# Claude-Qwen AI 编程助手

**项目根目录**: {root}

**可用命令**:
- `/help` - 显示帮助
- `/clear` - 清除对话历史（保留文件访问）
- `/compact` - 手动压缩上下文
- `/usage` - 显示 Token 使用情况
- `/exit` - 退出

**快速开始**: 直接输入您的请求，例如：
- "找到 network_handler.cpp 并添加超时重试机制"
- "编译项目并修复错误"
- "为当前文件生成单元测试"
"""
        self.console.print(Panel(
            Markdown(welcome.format(root=self.project_root)),
            title="欢迎",
            border_style="blue"
        ))
    
    def run(self):
        """Run interactive loop"""
        self.show_welcome()
        
        while True:
            try:
                # Get user input
                user_input = self.session.prompt('\n> ').strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if not self.handle_command(user_input):
                        break
                    continue
                
                # Execute task
                self.console.print("\n[cyan]执行中...[/cyan]\n")
                
                try:
                    response = self.agent.run(user_input)
                    
                    # Display response
                    self.console.print(Panel(
                        Markdown(response),
                        title="响应",
                        border_style="green"
                    ))
                    
                except Exception as e:
                    self.console.print(f"[red]错误: {e}[/red]")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]已取消[/yellow]")
                continue
            except EOFError:
                break
        
        self.console.print("\n[blue]再见![/blue]")
    
    def handle_command(self, command: str) -> bool:
        """
        Handle slash commands
        
        Returns:
            False to exit, True to continue
        """
        cmd = command.lower().split()[0]
        
        if cmd == '/exit' or cmd == '/quit':
            return False
        
        elif cmd == '/help':
            self.show_help()
        
        elif cmd == '/clear':
            self.agent.conversation_history.clear()
            self.agent.tool_calls.clear()
            self.console.print("[green]已清除对话历史[/green]")
        
        elif cmd == '/compact':
            self.console.print("[cyan]压缩中...[/cyan]")
            self.agent._compress_context()
            self.console.print("[green]压缩完成[/green]")
            self.console.print(self.agent.get_usage_report())
        
        elif cmd == '/usage':
            report = self.agent.get_usage_report()
            self.console.print(Panel(report, title="Token 使用情况"))
        
        elif cmd == '/root':
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                new_root = parts[1]
                if os.path.exists(new_root):
                    self.project_root = os.path.abspath(new_root)
                    self.agent.set_project_root(self.project_root)
                    self.console.print(f"[green]项目根目录已设置为: {self.project_root}[/green]")
                else:
                    self.console.print(f"[red]目录不存在: {new_root}[/red]")
            else:
                self.console.print(f"当前项目根目录: {self.project_root}")
        
        else:
            self.console.print(f"[yellow]未知命令: {cmd}[/yellow]")
            self.console.print("输入 /help 查看可用命令")
        
        return True
    
    def show_help(self):
        """Show help message"""
        help_text = """
## 可用命令

- `/help` - 显示此帮助信息
- `/clear` - 清除对话历史（保留文件访问权限）
- `/compact` - 手动触发上下文压缩
- `/usage` - 显示 Token 使用情况
- `/root [path]` - 查看或设置项目根目录
- `/exit` 或 `/quit` - 退出程序

## 示例用法

**文件操作**:
```
找到 network_handler.cpp 并添加超时重试机制
```

**编译修复**:
```
编译项目并修复所有错误
```

**测试生成**:
```
为当前文件生成单元测试
分析 HTTP 模块并生成集成测试
```

**代码分析**:
```
分析项目结构
查找所有网络相关的函数
```
"""
        self.console.print(Panel(Markdown(help_text), title="帮助"))


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude-Qwen AI 编程助手')
    parser.add_argument('--root', '-r', help='项目根目录', default=None)
    parser.add_argument('--version', '-v', action='version', version='0.1.0')
    
    args = parser.parse_args()
    
    # Initialize and run CLI
    cli = CLI(project_root=args.root)
    
    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
