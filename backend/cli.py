# -*- coding: utf-8 -*-
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
from .utils.precheck import PreCheck


class CLI:
    """Interactive CLI for Claude-Qwen"""
    
    def __init__(self, project_root: Optional[str] = None, skip_precheck: bool = False):
        """Initialize CLI

        Args:
            project_root: Project root directory
            skip_precheck: Skip environment pre-check (for testing)
        """
        self.console = Console()
        self.project_root = project_root or str(Path.cwd())

        # Run pre-check unless explicitly skipped
        if not skip_precheck:
            self._run_precheck()

        # Initialize agent
        self.client = OllamaClient()
        self.agent = AgentLoop(self.client, self.project_root)

        # Setup prompt session
        history_file = Path.home() / '.claude_qwen_history'
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )
    
    def _run_precheck(self):
        """Run environment pre-check"""
        self.console.print("\n[cyan]运行环境检查...[/cyan]\n")

        # Run pre-checks (skip project structure check)
        results = []
        results.append(PreCheck.check_ssh_tunnel())
        results.append(PreCheck.check_ollama_connection())
        results.append(PreCheck.check_ollama_model(model_name="qwen3:latest"))

        # Display results
        all_passed = all(r.success for r in results)

        for result in results:
            status = "✓" if result.success else "✗"
            color = "green" if result.success else "red"
            self.console.print(f"[{color}]{status}[/{color}] {result.message}")

        if not all_passed:
            self.console.print("\n[yellow]⚠ 环境检查失败[/yellow]")
            self.console.print("\n[yellow]建议操作:[/yellow]")

            for result in results:
                if not result.success:
                    if "SSH Tunnel" in result.name:
                        self.console.print("  • 启动 SSH 隧道: [cyan]ssh -fN ollama-tunnel[/cyan]")
                    elif "Ollama Connection" in result.name:
                        self.console.print("  • 验证远程服务器上的 Ollama 服务是否运行")
                    elif "Ollama Model" in result.name:
                        model = result.details.get('model', 'qwen3:latest')
                        self.console.print(f"  • 拉取模型: [cyan]ollama pull {model}[/cyan]")

            self.console.print("\n[yellow]提示: 使用 --skip-precheck 参数跳过环境检查[/yellow]\n")

            # Ask user if they want to continue
            try:
                response = input("是否继续? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    self.console.print("[red]已取消启动[/red]")
                    sys.exit(1)
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[red]已取消启动[/red]")
                sys.exit(1)
        else:
            self.console.print("\n[green]✓ 环境检查通过[/green]\n")

    def show_welcome(self):
        """Show welcome message"""
        stream_status = "✓ 启用" if self.client.stream_enabled else "✗ 禁用"
        stream_hint = "(实时输出)" if self.client.stream_enabled else "(等待完整响应)"

        welcome = """
# Claude-Qwen AI 编程助手

**项目根目录**: {root}
**流式输出**: {stream_status} {stream_hint}

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

💡 修改 `config/ollama.yaml` 中的 `stream` 配置可切换输出模式
"""
        self.console.print(Panel(
            Markdown(welcome.format(
                root=self.project_root,
                stream_status=stream_status,
                stream_hint=stream_hint
            )),
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
                    # Check if streaming is enabled in config
                    stream_enabled = self.client.stream_enabled

                    if stream_enabled:
                        # Streaming mode: real-time output
                        streamed_content = []

                        def on_chunk(chunk: str):
                            """Callback for streaming chunks"""
                            streamed_content.append(chunk)
                            # Print chunk in real-time
                            self.console.print(chunk, end='', style="white")

                        # Run with streaming enabled
                        response = self.agent.run(user_input, stream=True, on_chunk=on_chunk)

                        # Print newline after streaming
                        self.console.print("\n")

                        # If response is empty (fully streamed), use streamed content
                        if not response.strip() and streamed_content:
                            response = ''.join(streamed_content)
                    else:
                        # Non-streaming mode: wait for complete response
                        response = self.agent.run(user_input, stream=False)

                        # Display response in panel
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
    parser.add_argument('--skip-precheck', action='store_true',
                        help='跳过环境预检查（用于测试或离线环境）')
    parser.add_argument('--version', '-v', action='version', version='0.1.0')

    args = parser.parse_args()

    # Initialize and run CLI
    cli = CLI(project_root=args.root, skip_precheck=args.skip_precheck)

    try:
        cli.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
