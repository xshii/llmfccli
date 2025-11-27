# -*- coding: utf-8 -*-
"""
Tool confirmation manager for user approval before executing tools
"""

import json
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from enum import Enum


class ConfirmAction(Enum):
    """User confirmation actions"""
    ALLOW_ONCE = "allow_once"      # 本次允许
    ALLOW_ALWAYS = "allow_always"  # 始终允许
    DENY = "deny"                   # 拒绝并停止


class ToolConfirmation:
    """Manages tool execution confirmations"""

    def __init__(self, confirmation_file: Optional[str] = None):
        """
        Initialize tool confirmation manager

        Args:
            confirmation_file: Path to confirmation config file
        """
        if confirmation_file is None:
            confirmation_file = str(Path.home() / '.claude_qwen_confirmations.json')

        self.confirmation_file = Path(confirmation_file)

        # Load saved confirmations
        self.allowed_tools: Set[str] = set()
        self.allowed_bash_commands: Set[str] = set()
        self.denied_tools: Set[str] = set()

        self._load_confirmations()

        # Callback for user confirmation (set by CLI)
        self.confirm_callback: Optional[Callable[[str, str, Dict], ConfirmAction]] = None

    def _load_confirmations(self):
        """Load confirmations from file"""
        if self.confirmation_file.exists():
            try:
                with open(self.confirmation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.allowed_tools = set(data.get('allowed_tools', []))
                    self.allowed_bash_commands = set(data.get('allowed_bash_commands', []))
                    self.denied_tools = set(data.get('denied_tools', []))
            except Exception as e:
                print(f"Warning: Failed to load confirmations: {e}")

    def _save_confirmations(self):
        """Save confirmations to file"""
        try:
            data = {
                'allowed_tools': list(self.allowed_tools),
                'allowed_bash_commands': list(self.allowed_bash_commands),
                'denied_tools': list(self.denied_tools)
            }
            with open(self.confirmation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save confirmations: {e}")

    def set_confirmation_callback(self, callback: Callable[[str, str, Dict], ConfirmAction]):
        """Set the confirmation callback function"""
        self.confirm_callback = callback

    def get_tool_category(self, tool_name: str) -> str:
        """
        Get tool category for grouping

        Args:
            tool_name: Tool name

        Returns:
            Category name
        """
        # Define tool categories
        categories = {
            'filesystem': ['view_file', 'edit_file', 'create_file', 'grep_search', 'list_dir'],
            'executor': ['bash_run', 'cmake_build', 'run_tests'],
            'analyzer': ['parse_cpp', 'find_functions', 'get_dependencies']
        }

        for category, tools in categories.items():
            if tool_name in tools:
                return category

        return 'unknown'

    def needs_confirmation(self, tool_name: str, arguments: Dict) -> bool:
        """
        Check if tool execution needs user confirmation

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            True if confirmation needed
        """
        import os
        debug = os.getenv('DEBUG_CONFIRMATION', False)

        if debug:
            print(f"[DEBUG] Checking confirmation for tool: {tool_name}")
            print(f"[DEBUG] allowed_tools: {self.allowed_tools}")
            print(f"[DEBUG] allowed_bash_commands: {self.allowed_bash_commands}")
            print(f"[DEBUG] denied_tools: {self.denied_tools}")

        # Check if tool is denied
        if tool_name in self.denied_tools:
            if debug:
                print(f"[DEBUG] Tool {tool_name} is DENIED")
            return True

        # Check if tool is allowed
        if tool_name in self.allowed_tools:
            if debug:
                print(f"[DEBUG] Tool {tool_name} is ALLOWED (no confirmation needed)")
            return False

        # Special handling for bash_run
        if tool_name == 'bash_run':
            command = arguments.get('command', '')
            # Extract base command
            base_cmd = command.split()[0] if command else ''
            is_allowed = base_cmd in self.allowed_bash_commands
            if debug:
                print(f"[DEBUG] bash_run command: {base_cmd}, is_allowed: {is_allowed}")
            return not is_allowed

        # First time seeing this tool, needs confirmation
        if debug:
            print(f"[DEBUG] Tool {tool_name} needs confirmation (first time)")
        return True

    def confirm_tool_execution(self, tool_name: str, arguments: Dict) -> ConfirmAction:
        """
        Get user confirmation for tool execution

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            User's confirmation action
        """
        # If no callback set, allow by default (for testing)
        if self.confirm_callback is None:
            return ConfirmAction.ALLOW_ONCE

        # Get tool category
        category = self.get_tool_category(tool_name)

        # Ask user
        action = self.confirm_callback(tool_name, category, arguments)

        # Update allowed/denied lists based on action
        import os
        debug = os.getenv('DEBUG_CONFIRMATION', False)

        if action == ConfirmAction.ALLOW_ALWAYS:
            if tool_name == 'bash_run':
                # For bash_run, allow the specific command
                command = arguments.get('command', '')
                base_cmd = command.split()[0] if command else ''
                if base_cmd:
                    self.allowed_bash_commands.add(base_cmd)
                    if debug:
                        print(f"[DEBUG] Added bash command '{base_cmd}' to allowed_bash_commands")
                        print(f"[DEBUG] allowed_bash_commands now: {self.allowed_bash_commands}")
            else:
                self.allowed_tools.add(tool_name)
                if debug:
                    print(f"[DEBUG] Added tool '{tool_name}' to allowed_tools")
                    print(f"[DEBUG] allowed_tools now: {self.allowed_tools}")

            self._save_confirmations()
            if debug:
                print(f"[DEBUG] Confirmations saved to {self.confirmation_file}")

        elif action == ConfirmAction.DENY:
            self.denied_tools.add(tool_name)
            self._save_confirmations()
            if debug:
                print(f"[DEBUG] Added tool '{tool_name}' to denied_tools")

        return action

    def reset_confirmations(self):
        """Reset all confirmations"""
        self.allowed_tools.clear()
        self.allowed_bash_commands.clear()
        self.denied_tools.clear()

        if self.confirmation_file.exists():
            self.confirmation_file.unlink()

    def get_confirmation_status(self) -> Dict:
        """Get current confirmation status"""
        return {
            'allowed_tools': list(self.allowed_tools),
            'allowed_bash_commands': list(self.allowed_bash_commands),
            'denied_tools': list(self.denied_tools)
        }
