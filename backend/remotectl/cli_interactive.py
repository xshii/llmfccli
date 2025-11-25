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

from backend.interactive_base import InteractiveShellBase
from backend.remotectl.commands import RemoteCommands


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
        self.commands = RemoteCommands(self.console)

    # ==================== Commands ====================

    def do_list(self, arg):
        """List all models

        Usage: list
        """
        self.commands.list_models()

    def do_create(self, arg):
        """Create claude-qwen model from Modelfile

        Usage: create
        """
        self.commands.create_model()

    def do_ensure(self, arg):
        """Ensure model exists (create if not)

        Usage: ensure [model_name]
        Default model: claude-qwen:latest
        """
        model_name = arg.strip() or "claude-qwen:latest"
        self.commands.ensure_model(model_name)

    def do_show(self, arg):
        """Show model details

        Usage: show <model_name>
        Example: show claude-qwen:latest
        """
        if not arg.strip():
            self.print_error("Model name required")
            self.console.print("Usage: show <model_name>")
            return

        self.commands.show_model(arg.strip())

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

        self.commands.delete_model(model_name, confirm=skip_confirm)

    def do_health(self, arg):
        """Check Ollama server health

        Usage: health
        """
        self.commands.check_health()

    def do_pull(self, arg):
        """Pull model from registry

        Usage: pull <model_name>
        Example: pull qwen3:latest
        """
        if not arg.strip():
            self.print_error("Model name required")
            self.console.print("Usage: pull <model_name>")
            return

        self.commands.pull_model(arg.strip())

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
        result = self.commands.manager.list_models()
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
