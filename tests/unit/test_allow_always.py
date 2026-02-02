#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to verify ALLOW_ALWAYS functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agent.tools.confirmation import ToolConfirmation, ConfirmAction


def test_allow_always_persistence():
    """Test that ALLOW_ALWAYS persists across checks within a session"""

    # Create confirmation manager (session-level, no file persistence)
    confirmation = ToolConfirmation()

    # Mock callback that always returns ALLOW_ALWAYS
    def mock_callback(tool_name, category, arguments):
        print(f"    Callback called for {tool_name}")
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
    result = confirmation.confirm(tool_name, arguments)
    print(f"Result: {result}")
    print(f"Action: {result.action}")
    assert result.action == ConfirmAction.ALLOW_ALWAYS

    # Check status
    status = confirmation.status()
    print(f"\nStatus after ALLOW_ALWAYS:")
    print(f"  allowed_signatures: {status['allowed_signatures']}")
    print(f"  denied_names: {status['denied_names']}")

    # Second check - should NOT need confirmation (same instance)
    print("\n=== Second check (same instance) ===")
    needs_confirm_2 = confirmation.needs_confirmation(tool_name, arguments)
    print(f"needs_confirmation: {needs_confirm_2}")

    if needs_confirm_2:
        print("FAILED: Still needs confirmation in same instance!")
        return False
    else:
        print("PASSED: No confirmation needed in same instance")

    # Third check: New instance (session-level, so should need confirmation again)
    print("\n=== Third check (new instance - session-level) ===")
    confirmation2 = ToolConfirmation()

    status2 = confirmation2.status()
    print(f"Status in new instance:")
    print(f"  allowed_signatures: {status2['allowed_signatures']}")
    print(f"  denied_names: {status2['denied_names']}")

    needs_confirm_3 = confirmation2.needs_confirmation(tool_name, arguments)
    print(f"needs_confirmation: {needs_confirm_3}")

    if not needs_confirm_3:
        print("FAILED: Should need confirmation in new instance (session-level)")
        return False
    else:
        print("PASSED: Confirmation needed in new instance (correct session-level behavior)")

    print("\nAll tests passed!")
    return True


if __name__ == '__main__':
    success = test_allow_always_persistence()
    sys.exit(0 if success else 1)
