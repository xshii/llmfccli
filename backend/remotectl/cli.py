#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Control CLI for Ollama Management

Usage:
    python -m backend.remotectl.cli list
    python -m backend.remotectl.cli create
    python -m backend.remotectl.cli health
    python -m backend.remotectl.cli show <model_name>
"""

import sys
import argparse
from rich.console import Console

from .commands import RemoteCommands


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

    # Initialize commands
    console = Console()
    commands = RemoteCommands(console)

    # Execute command
    try:
        if args.command == 'list':
            success = commands.list_models()
        elif args.command == 'create':
            success = commands.create_model()
        elif args.command == 'ensure':
            success = commands.ensure_model(args.model)
        elif args.command == 'show':
            success = commands.show_model(args.model)
        elif args.command == 'delete':
            success = commands.delete_model(args.model, confirm=args.yes)
        elif args.command == 'health':
            success = commands.check_health()
        elif args.command == 'pull':
            success = commands.pull_model(args.model)
        else:
            console.print(f"[red]Unknown command: {args.command}[/red]")
            return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == '__main__':
    sys.exit(main())
