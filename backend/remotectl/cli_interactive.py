#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive CLI for Ollama Remote Control

Usage:
    python -m backend.remotectl.cli_interactive
    python backend/remotectl/cli_interactive.py
"""

import sys
from pathlib import Path

# Add project root to path for standalone execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from backend.interactive_base import InteractiveShellBase
from backend.remotectl.client import RemoteOllamaClient
from backend.remotectl.model_manager import ModelManager


class OllamaShell(InteractiveShellBase):
    """Interactive shell for Ollama remote control"""

    intro = """
╔════════════════════════════════════════════════════════════════╗
║           Ollama Remote Control - Interactive Mode            ║
╚════════════════════════════════════════════════════════════════╝

Type 'help' or '?' to list commands.
Type 'exit' or 'quit' to exit.
"""

    prompt = '(ollama) '

    def __init__(self):
        super().__init__()
        self.client = RemoteOllamaClient()
        self.manager = ModelManager()

    # ==================== Commands ====================

    def do_list(self, arg):
        """List all models

        Usage: list
        """
        result = self.manager.list_models()

        if not result['success']:
            self.print_error(f"Error: {result.get('error', 'Unknown error')}")
            return

        if result['count'] == 0:
            self.print_warning("No models found")
            return

        table = Table(title=f"Ollama Models ({result['count']} total)")
        table.add_column("Model Name", style="cyan")
        table.add_column("Details", style="dim")

        for model in result['models']:
            table.add_row(model['name'], model.get('raw', ''))

        self.console.print(table)

    def do_create(self, arg):
        """Create claude-qwen model from Modelfile

        Usage: create
        """
        self.print_info("Creating claude-qwen:latest model...")
        success = self.manager.sync_claude_qwen_model()

        if success:
            self.print_success("Model created successfully")
        else:
            self.print_error("Failed to create model")

    def do_ensure(self, arg):
        """Ensure model exists (create if not)

        Usage: ensure [model_name]
        Default model: claude-qwen:latest
        """
        model_name = arg.strip() or "claude-qwen:latest"
        self.print_info(f"Ensuring {model_name} exists...")

        success = self.manager.ensure_model_exists(model_name)

        if success:
            self.print_success(f"Model {model_name} is available")
        else:
            self.print_error(f"Failed to ensure model {model_name}")

    def do_show(self, arg):
        """Show model details

        Usage: show <model_name>
        Example: show claude-qwen:latest
        """
        if not arg.strip():
            self.print_error("Model name required")
            self.console.print("Usage: show <model_name>")
            return

        result = self.manager.show_model_info(arg.strip())

        if not result['success']:
            self.print_error(f"Error: {result.get('error', 'Unknown error')}")
            return

        self.console.print(Panel(
            result['modelfile'],
            title=f"Model: {result['model_name']}",
            border_style="cyan"
        ))

    def do_delete(self, arg):
        """Delete a model

        Usage: delete <model_name> [-y]
        Example: delete test-model:latest
                 delete test-model:latest -y  (skip confirmation)
        """
        if not arg.strip():
            self.print_error("Model name required")
            self.console.print("Usage: delete <model_name> [-y]")
            return

        parts = arg.strip().split()
        model_name = parts[0]
        skip_confirm = '-y' in parts or '--yes' in parts

        success = self.manager.delete_model(model_name, confirm=skip_confirm)

        if success:
            self.print_success(f"Model {model_name} deleted")
        else:
            self.print_error(f"Failed to delete model {model_name}")

    def do_health(self, arg):
        """Check Ollama server health

        Usage: health
        """
        health = self.client.check_health()

        status_color = "green" if health['healthy'] else "red"
        status_text = "Healthy" if health['healthy'] else "Unhealthy"

        info = f"""
**Status**: [{status_color}]{status_text}[/{status_color}]

**Details**:
- Process Running: {'✓' if health['process_running'] else '✗'}
- API Accessible: {'✓' if health['api_accessible'] else '✗'}
- Models Available: {health['model_count']}
"""

        self.print_panel(info, title="Ollama Server Health", style=status_color)

    def do_pull(self, arg):
        """Pull model from registry

        Usage: pull <model_name>
        Example: pull qwen3:latest
        """
        if not arg.strip():
            self.print_error("Model name required")
            self.console.print("Usage: pull <model_name>")
            return

        model_name = arg.strip()
        self.print_info(f"Pulling model: {model_name}")
        self.console.print("[dim]This may take several minutes for large models...[/dim]")

        success, output = self.client.pull_model(model_name)

        if success:
            self.print_success(f"Model {model_name} pulled successfully")
            if output:
                self.console.print(output)
        else:
            self.print_error(f"Failed to pull model: {output}")

    def do_sync(self, arg):
        """Run model sync script

        Usage: sync
        """
        self.print_info("Running sync_models.py...")
        self.console.print("[dim]This will sync all enabled models from config[/dim]")

        import subprocess
        result = subprocess.run(
            [sys.executable, str(project_root / "backend/remotectl/sync_models.py")],
            capture_output=False
        )

        if result.returncode == 0:
            self.print_success("Sync completed successfully")
        else:
            self.print_error("Sync failed")

    # ==================== Help ====================

    def do_help(self, arg):
        """Show help information

        Usage: help [command]
        """
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help using table
            from rich.table import Table

            self.console.print("\n[bold cyan]Available Commands[/bold cyan]\n")

            # Model Management commands
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Command", style="cyan", no_wrap=True)
            table.add_column("Description", style="dim")

            self.console.print("[bold]Model Management[/bold]")
            table.add_row("list", "List all models")
            table.add_row("create", "Create claude-qwen model from Modelfile")
            table.add_row("ensure", "Ensure model exists (create if not)")
            table.add_row("show", "Show model details")
            table.add_row("delete", "Delete a model")
            table.add_row("pull", "Pull model from registry")
            table.add_row("sync", "Run model sync script")
            self.console.print(table)

            # Server commands
            self.console.print("\n[bold]Server[/bold]")
            table2 = Table(show_header=False, box=None, padding=(0, 2))
            table2.add_column("Command", style="cyan", no_wrap=True)
            table2.add_column("Description", style="dim")
            table2.add_row("health", "Check Ollama server health")
            self.console.print(table2)

            # Utility commands
            self.console.print("\n[bold]Utility[/bold]")
            table3 = Table(show_header=False, box=None, padding=(0, 2))
            table3.add_column("Command", style="cyan", no_wrap=True)
            table3.add_column("Description", style="dim")
            table3.add_row("clear", "Clear the screen")
            table3.add_row("help", "Show this help message")
            table3.add_row("exit/quit", "Exit the shell")
            self.console.print(table3)

            # Tips
            self.console.print("\n[bold]Tips[/bold]")
            self.console.print("  • Use TAB for command completion")
            self.console.print("  • Type 'help <command>' for detailed help")
            self.console.print("  • Press Ctrl+D or type 'exit' to quit\n")

    # ==================== Completion ====================

    def complete_show(self, text, line, begidx, endidx):
        """Auto-complete model names for 'show' command"""
        return self._complete_model_name(text)

    def complete_delete(self, text, line, begidx, endidx):
        """Auto-complete model names for 'delete' command"""
        return self._complete_model_name(text)

    def complete_ensure(self, text, line, begidx, endidx):
        """Auto-complete model names for 'ensure' command"""
        return self._complete_model_name(text)

    def _complete_model_name(self, text):
        """Helper to get model names for completion"""
        result = self.manager.list_models()
        if result['success']:
            model_names = [m['name'] for m in result['models']]
            return [name for name in model_names if name.startswith(text)]
        return []


def main():
    """Main entry point"""
    from rich.console import Console
    console = Console()

    try:
        shell = OllamaShell()
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[cyan]Interrupted. Goodbye! 👋[/cyan]\n")
        return 0
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
