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
            confirmation_file: Path to confirmation config file (kept for compatibility, but not used for session-level confirmations)
        """
        # Note: Confirmations are now session-level only (not persisted to disk)
        # The confirmation_file parameter is kept for backward compatibility but not used

        # In-memory confirmation state (session-level)
        # Store tool call signatures (tool_name + key arguments) instead of just tool names
        self.allowed_tool_calls: Set[str] = set()  # Stores "tool_name:key_arg_value"
        self.denied_tools: Set[str] = set()

        # Callback for user confirmation (set by CLI)
        self.confirm_callback: Optional[Callable[[str, str, Dict], ConfirmAction]] = None

    def _load_confirmations(self):
        """Load confirmations from file (disabled - session-level only)"""
        # Session-level only: do not load from file
        pass

    def _save_confirmations(self):
        """Save confirmations to file (disabled - session-level only)"""
        # Session-level only: do not save to file
        pass

    def set_confirmation_callback(self, callback: Callable[[str, str, Dict], ConfirmAction]):
        """Set the confirmation callback function"""
        self.confirm_callback = callback

    def _get_tool_signature(self, tool_name: str, arguments: Dict) -> str:
        """
        Get unique signature for a tool call based on tool name and key arguments

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Signature string like "edit_file:src/main.cpp" or "bash_run:ls"
        """
        # Define key arguments for each tool type
        key_arg_map = {
            'view_file': 'file_path',
            'edit_file': 'file_path',
            'create_file': 'file_path',
            'grep_search': 'pattern',  # Pattern + scope would be too strict
            'list_dir': 'directory',
            'bash_run': 'command',
            'cmake_build': 'project_root',
            'run_tests': 'test_target',
        }

        key_arg = key_arg_map.get(tool_name)
        if not key_arg:
            # Unknown tool, use just the tool name
            return tool_name

        # Get the key argument value
        key_value = arguments.get(key_arg, '')

        # For bash_run, extract just the base command
        if tool_name == 'bash_run' and key_value:
            key_value = key_value.split()[0] if key_value else ''

        # For file paths, normalize to avoid path variations
        if key_arg == 'file_path':
            import os
            # Normalize path separators
            key_value = key_value.replace('\\', '/')

        return f"{tool_name}:{key_value}"

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

        # Get tool call signature
        signature = self._get_tool_signature(tool_name, arguments)

        if debug:
            print(f"[DEBUG] Checking confirmation for tool: {tool_name}")
            print(f"[DEBUG] Tool signature: {signature}")
            print(f"[DEBUG] allowed_tool_calls: {self.allowed_tool_calls}")
            print(f"[DEBUG] denied_tools: {self.denied_tools}")

        # Check if tool is denied (by tool name only)
        if tool_name in self.denied_tools:
            if debug:
                print(f"[DEBUG] Tool {tool_name} is DENIED")
            return True

        # Check if this specific tool call is allowed
        if signature in self.allowed_tool_calls:
            if debug:
                print(f"[DEBUG] Tool call {signature} is ALLOWED (no confirmation needed)")
            return False

        # First time seeing this specific tool call, needs confirmation
        if debug:
            print(f"[DEBUG] Tool call {signature} needs confirmation (first time)")
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
            # Get tool call signature and add to allowed set
            signature = self._get_tool_signature(tool_name, arguments)
            self.allowed_tool_calls.add(signature)

            if debug:
                print(f"[DEBUG] Added tool call '{signature}' to allowed_tool_calls")
                print(f"[DEBUG] allowed_tool_calls now: {self.allowed_tool_calls}")

            self._save_confirmations()

        elif action == ConfirmAction.DENY:
            self.denied_tools.add(tool_name)
            self._save_confirmations()
            if debug:
                print(f"[DEBUG] Added tool '{tool_name}' to denied_tools")

        return action

    def reset_confirmations(self):
        """Reset all confirmations (session-level only)"""
        self.allowed_tool_calls.clear()
        self.denied_tools.clear()
        # Note: No file to delete - confirmations are session-level only

    def get_confirmation_status(self) -> Dict:
        """Get current confirmation status"""
        return {
            'allowed_tool_calls': list(self.allowed_tool_calls),
            'denied_tools': list(self.denied_tools)
        }
