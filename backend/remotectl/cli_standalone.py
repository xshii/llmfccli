#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Control CLI for Ollama Management (Standalone Version)

This is a standalone version that can be run directly as a script.

Usage:
    python backend/remotectl/cli_standalone.py list
    python backend/remotectl/cli_standalone.py create
    python backend/remotectl/cli_standalone.py health
"""

import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Use absolute imports
from backend.remotectl.client import RemoteOllamaClient
from backend.remotectl.model_manager import ModelManager


console = Console()


def cmd_list(args):
    """List all models"""
    manager = ModelManager()
    result = manager.list_models()

    if not result['success']:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
        return 1

    if result['count'] == 0:
        console.print("[yellow]No models found[/yellow]")
        return 0

    # Create table
    table = Table(title=f"Ollama Models ({result['count']} total)")
    table.add_column("Model Name", style="cyan")
    table.add_column("Details", style="dim")

    for model in result['models']:
        table.add_row(model['name'], model.get('raw', ''))

    console.print(table)
    return 0


def cmd_create(args):
    """Create claude-qwen model"""
    manager = ModelManager()

    console.print("[cyan]Creating claude-qwen:latest model...[/cyan]")

    success = manager.sync_claude_qwen_model()

    if success:
        console.print("[green]✓ Model created successfully[/green]")
        return 0
    else:
        console.print("[red]✗ Failed to create model[/red]")
        return 1


def cmd_ensure(args):
    """Ensure claude-qwen model exists"""
    manager = ModelManager()

    model_name = args.model or "claude-qwen:latest"
    success = manager.ensure_model_exists(model_name)

    return 0 if success else 1


def cmd_show(args):
    """Show model details"""
    if not args.model:
        console.print("[red]Error: Model name required[/red]")
        console.print("Usage: cli show <model_name>")
        return 1

    manager = ModelManager()
    result = manager.show_model_info(args.model)

    if not result['success']:
        console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
        return 1

    console.print(Panel(
        result['modelfile'],
        title=f"Model: {result['model_name']}",
        border_style="cyan"
    ))

    return 0


def cmd_delete(args):
    """Delete a model"""
    if not args.model:
        console.print("[red]Error: Model name required[/red]")
        console.print("Usage: cli delete <model_name>")
        return 1

    manager = ModelManager()
    success = manager.delete_model(args.model, confirm=args.yes)

    return 0 if success else 1


def cmd_health(args):
    """Check Ollama server health"""
    client = RemoteOllamaClient()
    health = client.check_health()

    # Display health status
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

    return 0 if health['healthy'] else 1


def cmd_pull(args):
    """Pull a model from registry"""
    if not args.model:
        console.print("[red]Error: Model name required[/red]")
        console.print("Usage: cli pull <model_name>")
        return 1

    client = RemoteOllamaClient()

    console.print(f"[cyan]Pulling model: {args.model}[/cyan]")
    console.print("[dim]This may take several minutes for large models...[/dim]")

    success, output = client.pull_model(args.model)

    if success:
        console.print(f"[green]✓ Model {args.model} pulled successfully[/green]")
        if output:
            console.print(output)
        return 0
    else:
        console.print(f"[red]✗ Failed to pull model: {output}[/red]")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Remote Control CLI for Ollama Management",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # list command
    subparsers.add_parser('list', help='List all models')

    # create command
    subparsers.add_parser('create', help='Create claude-qwen model from Modelfile')

    # ensure command
    parser_ensure = subparsers.add_parser('ensure', help='Ensure model exists')
    parser_ensure.add_argument('--model', default='claude-qwen:latest', help='Model name')

    # show command
    parser_show = subparsers.add_parser('show', help='Show model details')
    parser_show.add_argument('model', nargs='?', help='Model name')

    # delete command
    parser_delete = subparsers.add_parser('delete', help='Delete a model')
    parser_delete.add_argument('model', nargs='?', help='Model name')
    parser_delete.add_argument('-y', '--yes', action='store_true', help='Skip confirmation')

    # health command
    subparsers.add_parser('health', help='Check server health')

    # pull command
    parser_pull = subparsers.add_parser('pull', help='Pull model from registry')
    parser_pull.add_argument('model', nargs='?', help='Model name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    commands = {
        'list': cmd_list,
        'create': cmd_create,
        'ensure': cmd_ensure,
        'show': cmd_show,
        'delete': cmd_delete,
        'health': cmd_health,
        'pull': cmd_pull
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
