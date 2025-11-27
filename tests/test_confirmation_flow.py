#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complete confirmation flow to verify tool_name is saved correctly
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from enum import Enum
from typing import Dict, Set, Optional, Callable

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Import ToolConfirmation and use its ConfirmAction
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tool_confirmation",
    str(Path(__file__).parent.parent / "backend" / "agent" / "tool_confirmation.py")
)
tool_confirmation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_confirmation_module)

# Use the module's own ConfirmAction
ToolConfirmation = tool_confirmation_module.ToolConfirmation
ConfirmAction = tool_confirmation_module.ConfirmAction


def test_tool_name_saved_correctly():
    """Test that tool name (not id) is saved to confirmation file"""

    # Use a temporary confirmation file (don't write to it yet)
    fd, confirmation_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)  # Close the file descriptor
    os.unlink(confirmation_file)  # Delete the empty file so ToolConfirmation will create it

    print(f"\n=== Testing Tool Name Save ===")
    print(f"Confirmation file: {confirmation_file}")

    try:
        # Create confirmation manager
        confirmation = ToolConfirmation(confirmation_file=confirmation_file)

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
        needs_confirm = confirmation.needs_confirmation(tool_name, arguments)
        print(f"\n[Test] Needs confirmation: {needs_confirm}")
        assert needs_confirm == True

        # Get user confirmation (mock will return ALLOW_ALWAYS)
        action = confirmation.confirm_tool_execution(tool_name, arguments)
        print(f"[Test] Action returned: {action}")
        print(f"[Test] Action type: {type(action)}")
        print(f"[Test] Action value: {action.value if hasattr(action, 'value') else action}")
        print(f"[Test] Expected: {ConfirmAction.ALLOW_ALWAYS}")
        print(f"[Test] Are they equal: {action == ConfirmAction.ALLOW_ALWAYS}")

        # Check internal state
        print(f"\n[Test] Internal state after confirmation:")
        print(f"  allowed_tools: {confirmation.allowed_tools}")
        print(f"  allowed_bash_commands: {confirmation.allowed_bash_commands}")
        print(f"  denied_tools: {confirmation.denied_tools}")

        assert action == ConfirmAction.ALLOW_ALWAYS

        # Read the saved file
        print(f"\n[Test] Reading saved confirmation file...")

        # Check if file exists and has content
        if not os.path.exists(confirmation_file):
            print(f"  ❌ ERROR: Confirmation file was not created!")
            return False

        file_size = os.path.getsize(confirmation_file)
        print(f"  File size: {file_size} bytes")

        if file_size == 0:
            print(f"  ❌ ERROR: Confirmation file is empty!")
            return False

        # Read raw content first
        with open(confirmation_file, 'r') as f:
            raw_content = f.read()
        print(f"  Raw content: {raw_content[:200]}")

        # Parse JSON
        saved_data = json.loads(raw_content)

        print(f"\n[Test] Saved data:")
        print(json.dumps(saved_data, indent=2))

        # Verify what was saved
        print(f"\n[Test] Verification:")
        if 'view_file' in saved_data.get('allowed_tools', []):
            print(f"  ✅ CORRECT: Function name 'view_file' was saved")
        else:
            print(f"  ❌ ERROR: Function name 'view_file' NOT found in saved data")

        if 'call_abc123' in saved_data.get('allowed_tools', []):
            print(f"  ❌ ERROR: ID 'call_abc123' was incorrectly saved")
        else:
            print(f"  ✅ CORRECT: ID 'call_abc123' was NOT saved")

        # Double-check by creating new instance
        print(f"\n[Test] Creating new instance to verify persistence...")
        confirmation2 = ToolConfirmation(confirmation_file=confirmation_file)
        needs_confirm_2 = confirmation2.needs_confirmation(tool_name, arguments)
        print(f"[Test] Second check needs confirmation: {needs_confirm_2}")

        if needs_confirm_2:
            print(f"  ❌ ERROR: Still needs confirmation after ALLOW_ALWAYS")
            print(f"  allowed_tools: {confirmation2.allowed_tools}")
            return False
        else:
            print(f"  ✅ CORRECT: No confirmation needed (tool is remembered)")
            return True

    finally:
        # Cleanup
        if os.path.exists(confirmation_file):
            os.unlink(confirmation_file)


if __name__ == '__main__':
    success = test_tool_name_saved_correctly()
    print(f"\n{'='*50}")
    if success:
        print("✅ Test PASSED: Tool name is saved correctly")
        sys.exit(0)
    else:
        print("❌ Test FAILED: Tool name is NOT saved correctly")
        sys.exit(1)
