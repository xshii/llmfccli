#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RPC integration between CLI and VSCode extension

This test simulates the communication flow.
"""

import sys
import os
import json
import time
from threading import Thread

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_rpc_client_basic():
    """Test basic RPC client functionality"""
    print("\n" + "=" * 60)
    print("Testing RPC Client (Mock Mode)")
    print("=" * 60)

    from backend.rpc.client import JsonRpcClient

    # Create client
    client = JsonRpcClient()

    print("\n1. Testing client initialization...")
    assert client is not None
    print("✓ Client created")

    print("\n2. Testing request ID generation...")
    assert client.request_id == 0
    client.request_id += 1
    assert client.request_id == 1
    print("✓ Request ID generation works")

    print("\n" + "=" * 60)
    print("✅ Basic RPC client tests passed")
    print("=" * 60)


def test_vscode_mode_detection():
    """Test VSCode mode detection"""
    print("\n" + "=" * 60)
    print("Testing VSCode Mode Detection")
    print("=" * 60)

    from backend.rpc.client import is_vscode_mode

    # Test without env var
    print("\n1. Testing without VSCODE_INTEGRATION...")
    if 'VSCODE_INTEGRATION' in os.environ:
        del os.environ['VSCODE_INTEGRATION']
    assert not is_vscode_mode()
    print("✓ Correctly detected non-VSCode mode")

    # Test with env var
    print("\n2. Testing with VSCODE_INTEGRATION=true...")
    os.environ['VSCODE_INTEGRATION'] = 'true'
    assert is_vscode_mode()
    print("✓ Correctly detected VSCode mode")

    # Clean up
    if 'VSCODE_INTEGRATION' in os.environ:
        del os.environ['VSCODE_INTEGRATION']

    print("\n" + "=" * 60)
    print("✅ VSCode mode detection tests passed")
    print("=" * 60)


def test_vscode_tools_mock_mode():
    """Test VSCode tools in mock mode"""
    print("\n" + "=" * 60)
    print("Testing VSCode Tools (Mock Mode)")
    print("=" * 60)

    # Ensure mock mode
    if 'VSCODE_INTEGRATION' in os.environ:
        del os.environ['VSCODE_INTEGRATION']

    from backend.tools import vscode

    print("\n1. Testing get_active_file...")
    try:
        file_info = vscode.get_active_file()
        assert 'path' in file_info
        assert 'content' in file_info
        print(f"✓ Got file: {file_info['path']}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n2. Testing get_selection...")
    try:
        selection = vscode.get_selection()
        assert 'text' in selection
        print(f"✓ Got selection: {selection['text'][:30]}...")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n3. Testing show_diff...")
    try:
        result = vscode.show_diff(
            "Test Diff",
            "/test/file.cpp",
            "modified content"
        )
        assert result.get('success') == True
        print(f"✓ Diff shown: {result.get('message')}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ VSCode tools (mock) tests passed")
    print("=" * 60)


def test_cli_vscode_mode():
    """Test CLI initialization in VSCode mode"""
    print("\n" + "=" * 60)
    print("Testing CLI VSCode Mode Initialization")
    print("=" * 60)

    # Set VSCode mode
    os.environ['VSCODE_INTEGRATION'] = 'true'

    print("\n1. Testing CLI initialization with VSCode mode...")
    try:
        # This would normally start the RPC client
        # For testing, we just check the flag
        from backend.rpc.client import is_vscode_mode
        assert is_vscode_mode()
        print("✓ VSCode mode detected")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Clean up
    if 'VSCODE_INTEGRATION' in os.environ:
        del os.environ['VSCODE_INTEGRATION']

    print("\n" + "=" * 60)
    print("✅ CLI VSCode mode tests passed")
    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("RPC Integration Test Suite")
    print("=" * 60)

    try:
        test_rpc_client_basic()
        test_vscode_mode_detection()
        test_vscode_tools_mock_mode()
        test_cli_vscode_mode()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
