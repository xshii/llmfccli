#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to verify ALLOW_ALWAYS functionality
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only what we need to avoid full backend dependencies
import sys
if True:  # Hack to avoid import order issues
    import json
    from pathlib import Path as _Path
    from typing import Dict, Set, Optional, Callable
    from enum import Enum

    class ConfirmAction(Enum):
        """User confirmation actions"""
        ALLOW_ONCE = "allow_once"
        ALLOW_ALWAYS = "allow_always"
        DENY = "deny"

    # Import the actual class
    from backend.agent.tools.confirmation import ToolConfirmation


def test_allow_always_persistence():
    """Test that ALLOW_ALWAYS persists across checks"""

    # Use a temporary confirmation file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        confirmation_file = f.name

    try:
        # Create confirmation manager
        confirmation = ToolConfirmation(confirmation_file=confirmation_file)

        # Mock callback that always returns ALLOW_ALWAYS
        def mock_callback(tool_name, category, arguments):
            print(f"✓ Callback called for {tool_name}")
            return ConfirmAction.ALLOW_ALWAYS

        confirmation.set_confirmation_callback(mock_callback)

        # First check - should need confirmation
        tool_name = 'view_file'
        arguments = {'file_path': '/test/file.cpp'}

        print("\n=== First check ===")
        needs_confirm_1 = confirmation.needs_confirmation(tool_name, arguments)
        print(f"needs_confirmation: {needs_confirm_1}")
        assert needs_confirm_1 == True, "First time should need confirmation"

        # Confirm with ALLOW_ALWAYS
        print("\n=== Confirming with ALLOW_ALWAYS ===")
        action = confirmation.confirm_tool_execution(tool_name, arguments)
        print(f"Action: {action}")
        assert action == ConfirmAction.ALLOW_ALWAYS

        # Check status
        status = confirmation.get_confirmation_status()
        print(f"\nStatus after ALLOW_ALWAYS:")
        print(f"  allowed_tools: {status['allowed_tools']}")
        print(f"  allowed_bash_commands: {status['allowed_bash_commands']}")
        print(f"  denied_tools: {status['denied_tools']}")

        # Second check - should NOT need confirmation (same instance)
        print("\n=== Second check (same instance) ===")
        needs_confirm_2 = confirmation.needs_confirmation(tool_name, arguments)
        print(f"needs_confirmation: {needs_confirm_2}")

        if needs_confirm_2:
            print("❌ FAILED: Still needs confirmation in same instance!")
            return False
        else:
            print("✓ PASSED: No confirmation needed in same instance")

        # Create new instance to test file persistence
        print("\n=== Third check (new instance) ===")
        confirmation2 = ToolConfirmation(confirmation_file=confirmation_file)

        status2 = confirmation2.get_confirmation_status()
        print(f"Status in new instance:")
        print(f"  allowed_tools: {status2['allowed_tools']}")
        print(f"  allowed_bash_commands: {status2['allowed_bash_commands']}")
        print(f"  denied_tools: {status2['denied_tools']}")

        needs_confirm_3 = confirmation2.needs_confirmation(tool_name, arguments)
        print(f"needs_confirmation: {needs_confirm_3}")

        if needs_confirm_3:
            print("❌ FAILED: Still needs confirmation in new instance!")
            return False
        else:
            print("✓ PASSED: No confirmation needed in new instance")

        print("\n✅ All tests passed!")
        return True

    finally:
        # Cleanup
        if os.path.exists(confirmation_file):
            os.unlink(confirmation_file)


if __name__ == '__main__':
    success = test_allow_always_persistence()
    sys.exit(0 if success else 1)
