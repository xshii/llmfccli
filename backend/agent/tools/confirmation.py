# -*- coding: utf-8 -*-
"""
Tool confirmation manager for user approval before executing tools

Supports dynamic tool discovery - uses BaseTool methods for:
- get_confirmation_signature(): Fine-grained confirmation grouping
- is_dangerous_operation(): Check if operation needs extra confirmation
- category property: Tool categorization
"""

from typing import Dict, Set, Optional, Callable, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .registry import ToolRegistry


class ConfirmAction(Enum):
    """User confirmation actions"""
    ALLOW_ONCE = "allow_once"      # 本次允许
    ALLOW_ALWAYS = "allow_always"  # 始终允许
    DENY = "deny"                   # 拒绝并停止


class ToolConfirmation:
    """Manages tool execution confirmations"""

    def __init__(self, tool_registry: Optional['ToolRegistry'] = None):
        """
        Initialize tool confirmation manager

        Args:
            tool_registry: Optional ToolRegistry for dynamic tool lookup
        """
        # In-memory confirmation state (session-level)
        self.allowed_tool_calls: Set[str] = set()
        self.denied_tools: Set[str] = set()

        # Tool registry for dynamic lookup
        self._tool_registry = tool_registry

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

    def set_tool_registry(self, registry: 'ToolRegistry'):
        """Set the tool registry for dynamic lookup"""
        self._tool_registry = registry

    def set_confirmation_callback(self, callback: Callable[[str, str, Dict], ConfirmAction]):
        """Set the confirmation callback function"""
        self.confirm_callback = callback

    def _get_tool_instance(self, tool_name: str):
        """Get tool instance from registry"""
        if self._tool_registry:
            return self._tool_registry.get(tool_name)
        return None

    def _get_tool_signature(self, tool_name: str, arguments: Dict) -> str:
        """
        Get unique signature for a tool call

        Uses the tool's get_confirmation_signature() method if available,
        otherwise falls back to just the tool name.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Signature string like "edit_file", "bash_run:ls", or "git:status"
        """
        tool = self._get_tool_instance(tool_name)
        if tool and hasattr(tool, 'get_confirmation_signature'):
            return tool.get_confirmation_signature(arguments)

        # Fallback: just tool name
        return tool_name

    def get_tool_category(self, tool_name: str) -> str:
        """
        Get tool category for grouping

        Uses the tool's category property if available.

        Args:
            tool_name: Tool name

        Returns:
            Category name
        """
        tool = self._get_tool_instance(tool_name)
        if tool and hasattr(tool, 'category'):
            return tool.category

        # Fallback
        return 'unknown'

    def is_dangerous_operation(self, tool_name: str, arguments: Dict) -> bool:
        """
        Check if operation is dangerous

        Uses the tool's is_dangerous_operation() method if available.
        Dangerous operations require confirmation even if the tool is whitelisted.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            True if operation is dangerous
        """
        tool = self._get_tool_instance(tool_name)
        if tool and hasattr(tool, 'is_dangerous_operation'):
            return tool.is_dangerous_operation(arguments)

        return False

    # Backward compatibility alias
    def is_dangerous_git_operation(self, action: str, args: Dict) -> bool:
        """Deprecated: Use is_dangerous_operation() instead"""
        return self.is_dangerous_operation('git', {'action': action, 'args': args})

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
            # Check if it's a dangerous operation even if the tool is whitelisted
            # Uses dynamic lookup via tool's is_dangerous_operation() method
            if self.is_dangerous_operation(tool_name, arguments):
                if debug:
                    print(f"[DEBUG] Tool {tool_name} with dangerous parameters - needs confirmation")
                return True

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

        # Show preview if tool supports it (e.g., edit_file shows diff before confirmation)
        tool = self._get_tool_instance(tool_name)
        if tool and hasattr(tool, 'get_diff_preview'):
            try:
                tool.get_diff_preview(**arguments)
            except Exception:
                # Preview failed, continue with confirmation
                pass

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
