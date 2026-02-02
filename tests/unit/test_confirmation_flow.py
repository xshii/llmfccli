#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complete confirmation flow to verify session-level behavior
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Import ToolConfirmation and ConfirmAction
from backend.agent.tools.confirmation import ToolConfirmation, ConfirmAction


def test_session_level_confirmation():
    """Test that confirmations are session-level only (not persisted)"""

    print(f"\n=== Testing Session-Level Confirmation ===")
    print(f"Note: Confirmations are session-level only (not persisted to disk)")

    # Create confirmation manager (session-level)
    confirmation = ToolConfirmation()

    # Mock callback that returns ALLOW_ALWAYS
    def mock_callback(tool_name, category, arguments):
        print(f"\n[Callback] Asked to confirm: {tool_name}")
        return ConfirmAction.ALLOW_ALWAYS

    confirmation.set_confirmation_callback(mock_callback)

    # Simulate a tool call with typical structure
    tool_call = {
        'id': 'call_abc123',  # This is the ID
        'function': {
            'name': 'view_file',  # This is the function name
            'arguments': {
                'file_path': '/test/file.cpp'
            }
        }
    }

    # Extract tool_name the same way loop.py does
    tool_name = tool_call['function']['name']
    arguments = tool_call['function']['arguments']

    print(f"\n[Test] Tool call:")
    print(f"  - ID: {tool_call['id']}")
    print(f"  - Function name: {tool_name}")
    print(f"  - Arguments: {arguments}")

    # Check if needs confirmation (should be True for first time)
    print(f"\n=== First Check (same instance) ===")
    needs_confirm = confirmation.needs_confirmation(tool_name, arguments)
    print(f"[Test] Needs confirmation: {needs_confirm}")
    assert needs_confirm == True, "First time should need confirmation"

    # Get user confirmation (mock will return ALLOW_ALWAYS)
    result = confirmation.confirm(tool_name, arguments)
    print(f"[Test] Result returned: {result}")
    print(f"[Test] Action: {result.action}")
    assert result.action == ConfirmAction.ALLOW_ALWAYS

    # Check internal state
    print(f"\n[Test] Internal state after confirmation:")
    print(f"  allowed_signatures: {confirmation.allowed_signatures}")
    print(f"  denied_names: {confirmation.denied_names}")

    # For file tools, signature is just the tool name (not file-specific)
    expected_signature = "view_file"
    assert expected_signature in confirmation.allowed_signatures, f"Tool signature '{expected_signature}' should be in allowed_signatures"
    assert 'call_abc123' not in confirmation.allowed_signatures, "ID should NOT be in allowed_signatures"

    # Second check in same instance - should NOT need confirmation
    print(f"\n=== Second Check (same instance, same file) ===")
    needs_confirm_2 = confirmation.needs_confirmation(tool_name, arguments)
    print(f"[Test] Needs confirmation: {needs_confirm_2}")

    if needs_confirm_2:
        print(f"  ❌ FAILED: Still needs confirmation in same instance!")
        return False
    else:
        print(f"  ✅ PASSED: No confirmation needed in same instance")

    # Third check: Same tool, different file - should ALSO NOT need confirmation
    # (File operations allow all files once approved)
    print(f"\n=== Third Check (same tool, different file) ===")
    different_file_args = {'file_path': '/test/other_file.cpp'}
    needs_confirm_3 = confirmation.needs_confirmation(tool_name, different_file_args)
    print(f"[Test] Needs confirmation for different file: {needs_confirm_3}")

    if needs_confirm_3:
        print(f"  ❌ FAILED: File operations should allow all files once approved")
        return False
    else:
        print(f"  ✅ PASSED: Different file does NOT need confirmation (correct behavior)")

    # Fourth check: Create new instance - should need confirmation (session-level)
    print(f"\n=== Fourth Check (new instance - session-level) ===")
    confirmation2 = ToolConfirmation()
    needs_confirm_4 = confirmation2.needs_confirmation(tool_name, arguments)
    print(f"[Test] Needs confirmation in new instance: {needs_confirm_4}")
    print(f"  allowed_signatures in new instance: {confirmation2.allowed_signatures}")

    if not needs_confirm_4:
        print(f"  ❌ FAILED: Should need confirmation in new instance (session-level)")
        return False
    else:
        print(f"  ✅ PASSED: Confirmation needed in new instance (session-level behavior correct)")

    print("\n✅ All tests passed!")
    print("✓ File tools use tool name only (allow all files of same operation type)")
    print("✓ ALLOW_ALWAYS works within same session for tool type")
    print("✓ Different files with same tool do NOT require re-confirmation")
    print("✓ New instance requires new confirmation (session-level)")
    return True


if __name__ == '__main__':
    success = test_session_level_confirmation()
    print(f"\n{'='*50}")
    if success:
        print("✅ Test PASSED: Session-level confirmation works correctly")
        sys.exit(0)
    else:
        print("❌ Test FAILED: Session-level confirmation has issues")
        sys.exit(1)
