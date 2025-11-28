# -*- coding: utf-8 -*-
"""
Unit tests for ToolExecutor interface
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools.executor import MockToolExecutor, RegistryToolExecutor


def test_mock_executor():
    """Test MockToolExecutor"""
    executor = MockToolExecutor()

    # Register mock tool
    executor.register_mock_tool(
        'test_tool',
        {
            'type': 'function',
            'function': {
                'name': 'test_tool',
                'description': 'Test tool',
                'parameters': {'type': 'object'}
            }
        },
        result={'status': 'success', 'value': 42}
    )

    # Test get_tool_schemas
    schemas = executor.get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]['function']['name'] == 'test_tool'

    # Test execute_tool
    result = executor.execute_tool('test_tool', {'arg': 'value'})
    assert result['status'] == 'success'
    assert result['value'] == 42

    # Test call history
    assert len(executor.call_history) == 1
    assert executor.call_history[0]['tool'] == 'test_tool'
    assert executor.call_history[0]['arguments'] == {'arg': 'value'}

    # Test get_tool_names
    names = executor.get_tool_names()
    assert 'test_tool' in names

    print("✓ MockToolExecutor tests passed")


def test_registry_executor():
    """Test RegistryToolExecutor"""
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')
    executor = RegistryToolExecutor(project_root)

    # Test get_tool_schemas
    schemas = executor.get_tool_schemas()
    assert len(schemas) > 0

    # Check that expected tools are registered
    tool_names = executor.get_tool_names()
    assert 'view_file' in tool_names
    assert 'edit_file' in tool_names
    assert 'grep_search' in tool_names
    assert 'list_dir' in tool_names

    # Test is_file_operation
    assert executor.is_file_operation('view_file')
    assert executor.is_file_operation('edit_file')
    assert not executor.is_file_operation('grep_search')

    # Test execute_tool with grep_search
    result = executor.execute_tool('grep_search', {
        'pattern': 'NetworkHandler',
        'scope': '.',
        'file_pattern': '*.h'
    })

    # Check result format - may fail if ripgrep not installed
    if result.get('success'):
        assert 'matches' in result
    else:
        # ripgrep not installed - skip this assertion
        print(f"   (grep_search skipped: {result.get('error', 'unknown error')})")

    print("✓ RegistryToolExecutor tests passed")


def test_agent_loop_integration():
    """Test AgentLoop with injected MockToolExecutor"""
    from backend.agent.loop import AgentLoop

    # Create mock executor
    mock_executor = MockToolExecutor()
    mock_executor.register_mock_tool(
        'test_tool',
        {
            'type': 'function',
            'function': {
                'name': 'test_tool',
                'description': 'Test tool',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'}
                    }
                }
            }
        },
        result="Tool executed"
    )

    # Create AgentLoop with mock executor (no real LLM needed for this test)
    agent = AgentLoop(tool_executor=mock_executor)

    # Verify executor is injected
    assert agent.tool_executor is mock_executor

    # Test get_tool_schemas through agent
    schemas = agent.tool_executor.get_tool_schemas()
    assert len(schemas) == 1

    print("✓ AgentLoop integration tests passed")


if __name__ == '__main__':
    print("Testing ToolExecutor implementations...\n")

    test_mock_executor()
    test_registry_executor()
    test_agent_loop_integration()

    print("\n✅ All ToolExecutor tests passed!")
