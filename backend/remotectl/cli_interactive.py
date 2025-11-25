#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive CLI for Ollama Remote Control

Usage:
    python -m backend.remotectl.cli_interactive
    python backend/remotectl/cli_interactive.py
"""

import sys
import cmd
from pathlib import Path

# Add project root to path for standalone execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from backend.remotectl.client import RemoteOllamaClient
from backend.remotectl.model_manager import ModelManager


console = Console()


class OllamaShell(cmd.Cmd):
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
        console.print(self.intro, style="cyan")

    # ==================== Commands ====================

    def do_list(self, arg):
        """List all models

        Usage: list
        """
        result = self.manager.list_models()

        if not result['success']:
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            return

        if result['count'] == 0:
            console.print("[yellow]No models found[/yellow]")
            return

        table = Table(title=f"Ollama Models ({result['count']} total)")
        table.add_column("Model Name", style="cyan")
        table.add_column("Details", style="dim")

        for model in result['models']:
            table.add_row(model['name'], model.get('raw', ''))

        console.print(table)

    def do_create(self, arg):
        """Create claude-qwen model from Modelfile

        Usage: create
        """
        console.print("[cyan]Creating claude-qwen:latest model...[/cyan]")
        success = self.manager.sync_claude_qwen_model()

        if success:
            console.print("[green]✓ Model created successfully[/green]")
        else:
            console.print("[red]✗ Failed to create model[/red]")

    def do_ensure(self, arg):
        """Ensure model exists (create if not)

        Usage: ensure [model_name]
        Default model: claude-qwen:latest
        """
        model_name = arg.strip() or "claude-qwen:latest"
        console.print(f"[cyan]Ensuring {model_name} exists...[/cyan]")

        success = self.manager.ensure_model_exists(model_name)

        if success:
            console.print(f"[green]✓ Model {model_name} is available[/green]")
        else:
            console.print(f"[red]✗ Failed to ensure model {model_name}[/red]")

    def do_show(self, arg):
        """Show model details

        Usage: show <model_name>
        Example: show claude-qwen:latest
        """
        if not arg.strip():
            console.print("[red]Error: Model name required[/red]")
            console.print("Usage: show <model_name>")
            return

        result = self.manager.show_model_info(arg.strip())

        if not result['success']:
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            return

        console.print(Panel(
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
            console.print("[red]Error: Model name required[/red]")
            console.print("Usage: delete <model_name> [-y]")
            return

        parts = arg.strip().split()
        model_name = parts[0]
        skip_confirm = '-y' in parts or '--yes' in parts

        success = self.manager.delete_model(model_name, confirm=skip_confirm)

        if success:
            console.print(f"[green]✓ Model {model_name} deleted[/green]")
        else:
            console.print(f"[red]✗ Failed to delete model {model_name}[/red]")

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

        console.print(Panel(info, title="Ollama Server Health", border_style=status_color))

    def do_pull(self, arg):
        """Pull model from registry

        Usage: pull <model_name>
        Example: pull qwen3:latest
        """
        if not arg.strip():
            console.print("[red]Error: Model name required[/red]")
            console.print("Usage: pull <model_name>")
            return

        model_name = arg.strip()
        console.print(f"[cyan]Pulling model: {model_name}[/cyan]")
        console.print("[dim]This may take several minutes for large models...[/dim]")

        success, output = self.client.pull_model(model_name)

        if success:
            console.print(f"[green]✓ Model {model_name} pulled successfully[/green]")
            if output:
                console.print(output)
        else:
            console.print(f"[red]✗ Failed to pull model: {output}[/red]")

    def do_sync(self, arg):
        """Run model sync script

        Usage: sync
        """
        console.print("[cyan]Running sync_models.py...[/cyan]")
        console.print("[dim]This will sync all enabled models from config[/dim]")

        import subprocess
        result = subprocess.run(
            [sys.executable, str(project_root / "backend/remotectl/sync_models.py")],
            capture_output=False
        )

        if result.returncode == 0:
            console.print("[green]✓ Sync completed successfully[/green]")
        else:
            console.print("[red]✗ Sync failed[/red]")

    def do_clear(self, arg):
        """Clear the screen

        Usage: clear
        """
        console.clear()

    def do_exit(self, arg):
        """Exit the interactive shell

        Usage: exit
        """
        console.print("\n[cyan]Goodbye! 👋[/cyan]\n")
        return True

    def do_quit(self, arg):
        """Exit the interactive shell

        Usage: quit
        """
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Exit on Ctrl+D"""
        console.print()
        return self.do_exit(arg)

    # ==================== Help ====================

    def do_help(self, arg):
        """Show help information

        Usage: help [command]
        """
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            help_text = """
## Available Commands

### Model Management
- **list**        - List all models
- **create**      - Create claude-qwen model from Modelfile
- **ensure**      - Ensure model exists (create if not)
- **show**        - Show model details
- **delete**      - Delete a model
- **pull**        - Pull model from registry
- **sync**        - Run model sync script

### Server
- **health**      - Check Ollama server health

### Utility
- **clear**       - Clear the screen
- **help**        - Show this help message
- **exit/quit**   - Exit the shell

### Tips
- Use TAB for command completion
- Type 'help <command>' for detailed help on a command
- Press Ctrl+D or type 'exit' to quit
"""
            console.print(Markdown(help_text))

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

    # ==================== Error Handling ====================

    def emptyline(self):
        """Do nothing on empty line (don't repeat last command)"""
        pass

    def default(self, line):
        """Handle unknown commands"""
        console.print(f"[red]Unknown command: {line}[/red]")
        console.print("Type 'help' to see available commands")


def main():
    """Main entry point"""
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
