#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common command implementations for all CLI modes

This module provides reusable command logic that can be used by:
- cli.py (module mode with argparse)
- cli_standalone.py (standalone script)
- cli_interactive.py (interactive shell)
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .client import RemoteOllamaClient
from .model_manager import ModelManager


class RemoteCommands:
    """Reusable command implementations"""

    def __init__(self, console=None):
        self.console = console or Console()
        self.client = RemoteOllamaClient()
        self.manager = ModelManager()

    def list_models(self):
        """List all models"""
        result = self.manager.list_models()

        if not result['success']:
            self.console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            return False

        if result['count'] == 0:
            self.console.print("[yellow]No models found[/yellow]")
            return True

        table = Table(title=f"Ollama Models ({result['count']} total)")
        table.add_column("Model Name", style="cyan")
        table.add_column("Details", style="dim")

        for model in result['models']:
            table.add_row(model['name'], model.get('raw', ''))

        self.console.print(table)
        return True

    def create_model(self):
        """Create claude-qwen model"""
        self.console.print("[cyan]Creating claude-qwen:latest model...[/cyan]")
        success = self.manager.sync_claude_qwen_model()

        if success:
            self.console.print("[green]✓ Model created successfully[/green]")
        else:
            self.console.print("[red]✗ Failed to create model[/red]")

        return success

    def ensure_model(self, model_name="claude-qwen:latest"):
        """Ensure model exists (create if not)"""
        return self.manager.ensure_model_exists(model_name)

    def show_model(self, model_name):
        """Show model details"""
        if not model_name:
            self.console.print("[red]Error: Model name required[/red]")
            return False

        result = self.manager.show_model_info(model_name)

        if not result['success']:
            self.console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            return False

        self.console.print(Panel(
            result['modelfile'],
            title=f"Model: {result['model_name']}",
            border_style="cyan"
        ))

        return True

    def delete_model(self, model_name, confirm=False):
        """Delete a model"""
        if not model_name:
            self.console.print("[red]Error: Model name required[/red]")
            return False

        success = self.manager.delete_model(model_name, confirm=confirm)
        return success

    def check_health(self):
        """Check Ollama server health"""
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

        self.console.print(Panel(info, title="Ollama Server Health", border_style=status_color))

        return health['healthy']

    def pull_model(self, model_name):
        """Pull a model from registry"""
        if not model_name:
            self.console.print("[red]Error: Model name required[/red]")
            return False

        self.console.print(f"[cyan]Pulling model: {model_name}[/cyan]")
        self.console.print("[dim]This may take several minutes for large models...[/dim]")

        success, output = self.client.pull_model(model_name)

        if success:
            self.console.print(f"[green]✓ Model {model_name} pulled successfully[/green]")
            if output:
                self.console.print(output)
        else:
            self.console.print(f"[red]✗ Failed to pull model: {output}[/red]")

        return success
