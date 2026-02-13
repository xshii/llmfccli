# -*- coding: utf-8 -*-
"""
Tool confirmation manager for user approval before executing tools

Supports dynamic tool discovery - uses BaseTool methods for:
- confirmation_signature(): Fine-grained confirmation grouping
- is_dangerous(): Check if operation needs extra confirmation
- skip_confirmation: Whether to skip confirmation entirely
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable, Dict, Optional, Set, Union

if TYPE_CHECKING:
    from .registry import ToolRegistry


class ConfirmAction(Enum):
    """User confirmation actions"""
    ALLOW_ONCE = "allow_once"      # 本次允许
    ALLOW_ALWAYS = "allow_always"  # 始终允许
    DENY = "deny"                   # 拒绝并停止


@dataclass
class ConfirmResult:
    """Result of user confirmation with optional reason"""
    action: ConfirmAction
    reason: Optional[str] = None  # User's reason for denial


class ToolConfirmation:
    """Manages tool execution confirmations"""

    def __init__(self, tool_registry: Optional['ToolRegistry'] = None):
        """
        Initialize tool confirmation manager

        Args:
            tool_registry: Optional ToolRegistry for dynamic tool lookup
        """
        # In-memory confirmation state (session-level)
        self.allowed_signatures: Set[str] = set()
        self.denied_names: Set[str] = set()

        # Tool registry for dynamic lookup
        self._registry = tool_registry

        # Callback for user confirmation (set by CLI)
        self._callback: Optional[Callable[[str, str, Dict], Union[ConfirmAction, ConfirmResult]]] = None

    def set_tool_registry(self, registry: 'ToolRegistry'):
        """Set the tool registry for dynamic lookup"""
        self._registry = registry

    def set_confirmation_callback(self, callback: Callable[[str, str, Dict], Union[ConfirmAction, ConfirmResult]]):
        """Set the confirmation callback function

        Callback can return either:
        - ConfirmAction: Simple action without reason
        - ConfirmResult: Action with optional reason (for denial)
        """
        self._callback = callback

    def _get_tool(self, tool_name: str):
        """Get tool instance from registry"""
        if self._registry:
            return self._registry.get(tool_name)
        return None

    def _get_signature(self, tool_name: str, arguments: Dict) -> str:
        """
        Get unique signature for a tool call

        Uses the tool's confirmation_signature() method if available,
        otherwise falls back to just the tool name.
        """
        tool = self._get_tool(tool_name)
        if tool and hasattr(tool, 'confirmation_signature'):
            return tool.confirmation_signature(arguments)
        return tool_name

    def _get_category(self, tool_name: str) -> str:
        """Get tool category for grouping"""
        tool = self._get_tool(tool_name)
        if tool and hasattr(tool, 'category'):
            return tool.category
        return 'unknown'

    def _is_dangerous(self, tool_name: str, arguments: Dict) -> bool:
        """Check if operation is dangerous (requires confirmation even if whitelisted)"""
        tool = self._get_tool(tool_name)
        if tool and hasattr(tool, 'is_dangerous'):
            return tool.is_dangerous(arguments)
        return False

    def _should_skip(self, tool_name: str) -> bool:
        """Check if tool declares skip_confirmation=True"""
        tool = self._get_tool(tool_name)
        if tool and hasattr(tool, 'skip_confirmation'):
            return tool.skip_confirmation
        return False

    def needs_confirmation(self, tool_name: str, arguments: Dict) -> bool:
        """
        Check if tool execution needs user confirmation

        Priority:
        1. skip_confirmation=True → skip
        2. denied_names → always confirm
        3. allowed_signatures + not dangerous → skip
        4. is_dangerous → always confirm
        5. first time → confirm
        """
        import os
        debug = os.getenv('DEBUG_CONFIRMATION', False)

        # 1. Check if tool declares skip_confirmation
        if self._should_skip(tool_name):
            if debug:
                print(f"[DEBUG] Tool {tool_name} declares skip_confirmation=True")
            return False

        signature = self._get_signature(tool_name, arguments)

        if debug:
            print(f"[DEBUG] Checking confirmation for tool: {tool_name}")
            print(f"[DEBUG] Signature: {signature}")
            print(f"[DEBUG] allowed_signatures: {self.allowed_signatures}")
            print(f"[DEBUG] denied_names: {self.denied_names}")

        # 2. Check if tool is denied
        if tool_name in self.denied_names:
            if debug:
                print(f"[DEBUG] Tool {tool_name} is DENIED")
            return True

        # 3. Check if signature is allowed
        if signature in self.allowed_signatures:
            # 4. But dangerous operations still need confirmation
            if self._is_dangerous(tool_name, arguments):
                if debug:
                    print(f"[DEBUG] Tool {tool_name} is dangerous - needs confirmation")
                return True

            if debug:
                print(f"[DEBUG] Signature {signature} is ALLOWED")
            return False

        # 5. First time - needs confirmation
        if debug:
            print(f"[DEBUG] Signature {signature} needs confirmation (first time)")
        return True

    def confirm(self, tool_name: str, arguments: Dict) -> ConfirmResult:
        """
        Get user confirmation for tool execution

        Returns:
            ConfirmResult with action and optional reason
        """
        # If no callback set, allow by default (for testing)
        if self._callback is None:
            return ConfirmResult(action=ConfirmAction.ALLOW_ONCE)

        category = self._get_category(tool_name)

        # Ask user
        callback_result = self._callback(tool_name, category, arguments)

        # Normalize to ConfirmResult
        if isinstance(callback_result, ConfirmResult):
            result = callback_result
        else:
            result = ConfirmResult(action=callback_result)

        # Update state based on action
        import os
        debug = os.getenv('DEBUG_CONFIRMATION', False)

        if result.action == ConfirmAction.ALLOW_ALWAYS:
            signature = self._get_signature(tool_name, arguments)
            self.allowed_signatures.add(signature)
            if debug:
                print(f"[DEBUG] Added '{signature}' to allowed_signatures")

        elif result.action == ConfirmAction.DENY:
            # Don't persist deny state - only reject the current call.
            # Future calls go through normal first-time confirmation flow.
            # Dangerous operations have their own is_dangerous() check.
            if debug:
                print(f"[DEBUG] Denied '{tool_name}' (this call only, not persisted)")

        return result

    def reset(self):
        """Reset all confirmations (session-level only)"""
        self.allowed_signatures.clear()
        self.denied_names.clear()

    def status(self) -> Dict:
        """Get current confirmation status"""
        return {
            'allowed_signatures': list(self.allowed_signatures),
            'denied_names': list(self.denied_names)
        }
