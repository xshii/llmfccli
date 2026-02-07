# -*- coding: utf-8 -*-
"""
PrecheckRunner - 环境预检查运行器

从 CLI 类提取的预检查逻辑，负责：
1. 运行环境检查
2. 显示检查结果
3. 处理用户交互（重试/退出）
4. 启动 SSH 隧道
"""

import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from backend.constants import Timeout
from backend.utils.precheck import PreCheck, PreCheckResult


class PrecheckRunner:
    """环境预检查运行器"""

    def __init__(self, console: Optional[Console] = None):
        """
        初始化预检查运行器

        Args:
            console: Rich Console 实例，用于输出
        """
        self.console = console or Console()
        self._ssh_host: Optional[str] = None
        self._extra_paths: List[str] = []
        self._load_ssh_config()

    def _load_ssh_config(self) -> None:
        """加载 SSH 配置"""
        try:
            import yaml
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "llm.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self._ssh_host = config.get('ssh', {}).get('host')
                self._extra_paths = config.get('ssh', {}).get('extra_paths', [])
        except Exception:
            pass

    def _get_path_prefix(self) -> str:
        """获取远程命令的 PATH 前缀"""
        if self._extra_paths:
            return f"export PATH=\"{':'.join(self._extra_paths)}:$PATH\" && "
        return ""

    def run(self) -> bool:
        """
        运行预检查

        Returns:
            bool: 是否通过所有检查
        """
        while True:
            self.console.print("\n[cyan]运行环境检查...[/cyan]")

            # 运行预检查
            results = self._run_checks()

            # 显示结果
            all_passed = self._display_results(results)

            if all_passed:
                self.console.print("\n[green]✓ 环境检查通过[/green]")
                return True

            # 显示建议和处理用户输入
            self._show_suggestions(results)
            action = self._get_user_action()

            if action == 'exit':
                return False
            elif action == 'ssh':
                self._start_ssh_and_ollama()
                continue
            else:  # retry
                continue

    def _run_checks(self) -> List[PreCheckResult]:
        """运行所有检查"""
        results = []
        results.append(PreCheck.check_and_kill_local_ollama())
        results.append(PreCheck.check_ssh_tunnel())
        results.append(PreCheck.check_ollama_connection())
        results.append(PreCheck.check_ollama_model())
        return results

    def _display_results(self, results: List[PreCheckResult]) -> bool:
        """显示检查结果"""
        all_passed = all(r.success for r in results)

        for result in results:
            status = "✓" if result.success else "✗"
            color = "green" if result.success else "red"
            self.console.print(f"[{color}]{status}[/{color}] {result.message}")

        return all_passed

    def _show_suggestions(self, results: List[PreCheckResult]) -> None:
        """显示修复建议"""
        self.console.print("\n[yellow]⚠ 环境检查失败[/yellow]")
        self.console.print("\n[yellow]建议操作:[/yellow]")

        path_prefix = self._get_path_prefix()

        for result in results:
            if not result.success:
                if "SSH Tunnel" in result.name:
                    if not self._ssh_host:
                        self.console.print(
                            "  • 配置 SSH host: [cyan]config/llm.yaml -> ssh.host[/cyan]"
                        )
                    elif "远程 Ollama 服务未运行" in result.message:
                        self.console.print(
                            f"  • 在远程服务器启动 Ollama: "
                            f"[cyan]ssh {self._ssh_host} '{path_prefix}ollama serve &'[/cyan]"
                        )
                    else:
                        self.console.print(
                            f"  • 启动 SSH 隧道: [cyan]ssh -fN {self._ssh_host}[/cyan]"
                        )
                elif "Ollama Connection" in result.name:
                    if self._ssh_host:
                        self.console.print(
                            f"  • 在远程服务器启动 Ollama: "
                            f"[cyan]ssh {self._ssh_host} '{path_prefix}nohup ollama serve > /dev/null 2>&1 &'[/cyan]"
                        )
                    else:
                        self.console.print("  • 启动本地 Ollama: [cyan]ollama serve[/cyan]")
                elif "Ollama Model" in result.name:
                    model = result.details.get('model', '(see config/llm.yaml)')
                    self.console.print(f"  • 拉取模型: [cyan]ollama pull {model}[/cyan]")

        self.console.print("\n[yellow]提示: 使用 --skip-precheck 参数跳过环境检查[/yellow]\n")

    def _get_user_action(self) -> str:
        """获取用户操作选择

        Returns:
            'ssh': 启动 SSH 并重试
            'retry': 重试
            'exit': 退出
        """
        try:
            self.console.print(
                "选择操作 - \\[s]启动SSH并重试 / \\[R]手动重试 / \\[n]退出: ",
                end=''
            )

            response = self._read_single_key()

            if response == 's':
                return 'ssh'
            elif response == 'n':
                self.console.print("[red]已取消启动[/red]")
                return 'exit'
            else:
                return 'retry'

        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[red]已取消启动[/red]")
            return 'exit'

    def _read_single_key(self) -> str:
        """读取单个按键"""
        if not sys.stdin.isatty():
            return input().strip().lower() or 'r'

        if platform.system() == 'Windows':
            import msvcrt
            response = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            self.console.print(response)
            return response

        try:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                response = sys.stdin.read(1).lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.console.print(response)
            return response
        except Exception:
            return input().strip().lower() or 'r'

    def _start_ssh_and_ollama(self) -> None:
        """启动 SSH 隧道和远程 Ollama"""
        if not self._ssh_host:
            self.console.print("[red]✗ SSH host 未配置，请在 config/llm.yaml 中设置 ssh.host[/red]")
            return

        # 清理占用端口的进程
        self._kill_port_process(11434)

        # 启动 SSH 隧道
        self.console.print(f"[cyan]启动 SSH 隧道: ssh -fN {self._ssh_host}[/cyan]")
        try:
            subprocess.run(['ssh', '-fN', self._ssh_host], check=True)
            self.console.print("[green]✓ SSH 隧道已启动[/green]")
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]✗ SSH 启动失败: {e}[/red]")
            return
        except FileNotFoundError:
            self.console.print("[red]✗ 未找到 ssh 命令[/red]")
            return

        # 等待隧道建立
        time.sleep(1)

        # 检查并启动远程 Ollama
        self._start_remote_ollama()

    def _kill_port_process(self, port: int) -> None:
        """终止占用指定端口的进程"""
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    f'netstat -ano | findstr :{port}',
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = set()
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split()
                        if parts:
                            pids.add(parts[-1])
                    for pid in pids:
                        if pid.strip() and pid != '0':
                            subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                    self.console.print(f"[dim]已终止占用端口 {port} 的进程 (PID: {', '.join(pids)})[/dim]")
            else:
                result = subprocess.run(
                    f'lsof -i tcp:{port}',
                    shell=True, capture_output=True, text=True
                )
                if result.stdout.strip():
                    lines = result.stdout.strip().split('\n')[1:]
                    pids = set()
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 2:
                            pids.add(parts[1])
                    if pids:
                        for pid in pids:
                            subprocess.run(['kill', '-9', pid], capture_output=True)
                        self.console.print(f"[dim]已终止占用端口 {port} 的进程 (PID: {', '.join(pids)})[/dim]")

            time.sleep(1)  # 等待端口释放
        except Exception as e:
            self.console.print(f"[dim]清理端口失败: {e}[/dim]")

    def _start_remote_ollama(self) -> None:
        """启动远程 Ollama 服务"""
        if not self._ssh_host:
            return
        try:
            # 检查 Ollama 是否响应
            check_result = subprocess.run(
                ['curl', '-s', '--connect-timeout', '2', 'http://localhost:11434/api/tags'],
                capture_output=True, text=True, timeout=Timeout.QUICK
            )
            if check_result.returncode != 0 or not check_result.stdout.strip():
                # Ollama 未运行，尝试启动
                self.console.print("[cyan]启动远程 Ollama 服务...[/cyan]")
                path_prefix = self._get_path_prefix()
                ollama_cmd = f"{path_prefix}nohup ollama serve > /dev/null 2>&1 &"
                subprocess.run(
                    ['ssh', '-o', 'ClearAllForwardings=yes', self._ssh_host, ollama_cmd],
                    capture_output=True, timeout=10
                )
                time.sleep(2)  # 等待 Ollama 启动
                self.console.print("[green]✓ 远程 Ollama 启动命令已发送[/green]")
        except Exception as e:
            self.console.print(f"[dim]启动远程 Ollama 失败: {e}[/dim]")
