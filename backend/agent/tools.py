# -*- coding: utf-8 -*-
"""
Tool registration and schema generation for function calling
"""

from typing import Dict, Any, List, Callable, Optional
import json


class ToolRegistry:
    """Registry for managing tools and their schemas"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.implementations: Dict[str, Callable] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any],
                 implementation: Callable):
        """
        Register a tool with its schema and implementation
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            implementation: Python function to execute
        """
        self.tools[name] = {
            'type': 'function',
            'function': {
                'name': name,
                'description': description,
                'parameters': parameters
            }
        }
        self.implementations[name] = implementation
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in OpenAI format"""
        return list(self.tools.values())
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.implementations:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        func = self.implementations[tool_name]
        try:
            return func(**arguments)
        except Exception as e:
            return {
                'error': str(e),
                'tool': tool_name,
                'arguments': arguments
            }


# Global registry instance
registry = ToolRegistry()


def register_filesystem_tools(project_root: str):
    """Register filesystem tools"""
    from ..tools.filesystem_tools import view_file, edit_file, create_file, grep_search, list_dir
    
    # view_file
    registry.register(
        name='view_file',
        description='Read file contents with optional line range',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'format': 'filepath',
                    'description': 'File path relative to project root or absolute'
                },
                'line_range': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'minItems': 2,
                    'maxItems': 2,
                    'description': 'Optional [start_line, end_line] (1-indexed, use -1 for end)'
                }
            },
            'required': ['path']
        },
        implementation=lambda path, line_range=None: view_file(
            path, tuple(line_range) if line_range else None, project_root
        )
    )
    
    # edit_file
    registry.register(
        name='edit_file',
        description='Edit file using str_replace (old_str must be unique)',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'format': 'filepath',
                    'description': 'File path'
                },
                'old_str': {
                    'type': 'string',
                    'description': 'String to replace (must appear exactly once)'
                },
                'new_str': {
                    'type': 'string',
                    'description': 'Replacement string'
                },
                'confirm': {
                    'type': 'boolean',
                    'description': 'Require user confirmation (default: true)',
                    'default': True
                }
            },
            'required': ['path', 'old_str', 'new_str']
        },
        implementation=lambda path, old_str, new_str, confirm=True: edit_file(
            path, old_str, new_str, project_root, confirm=confirm
        )
    )
    
    # create_file
    registry.register(
        name='create_file',
        description='Create new file with content',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'format': 'filepath',
                    'description': 'File path'
                },
                'content': {
                    'type': 'string',
                    'description': 'File content'
                }
            },
            'required': ['path', 'content']
        },
        implementation=lambda path, content: create_file(
            path, content, project_root
        )
    )
    
    # grep_search
    registry.register(
        name='grep_search',
        description='Search for pattern in files (regex supported)',
        parameters={
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'Search pattern (regex)'
                },
                'scope': {
                    'type': 'string',
                    'format': 'filepath',
                    'description': 'Search scope directory (e.g., ".", "src/", "backend/")'
                },
                'file_pattern': {
                    'type': 'string',
                    'description': 'Optional file pattern filter (e.g., "*.cpp")'
                }
            },
            'required': ['pattern', 'scope']
        },
        implementation=lambda pattern, scope, file_pattern=None: grep_search(
            pattern, scope, project_root, file_pattern=file_pattern
        )
    )
    
    # list_dir
    registry.register(
        name='list_dir',
        description='List directory contents recursively',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'format': 'filepath',
                    'description': 'Directory path (default: ".")'
                },
                'max_depth': {
                    'type': 'integer',
                    'description': 'Maximum depth to traverse (default: 3)'
                }
            },
            'required': []
        },
        implementation=lambda path=".", max_depth=3: list_dir(
            path, project_root, max_depth
        )
    )


def register_executor_tools(project_root: str):
    """Register executor tools (bash, cmake, etc.)"""
    from ..tools.executor_tools import bash_run, cmake_build, run_tests

    # bash_run
    registry.register(
        name='bash_run',
        description='Execute bash command with security checks and timeout',
        parameters={
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'Bash command to execute'
                },
                'timeout': {
                    'type': 'integer',
                    'description': 'Timeout in seconds (default: 60)'
                }
            },
            'required': ['command']
        },
        implementation=lambda command, timeout=60: bash_run(
            command, project_root, timeout=timeout
        )
    )

    # cmake_build
    registry.register(
        name='cmake_build',
        description='Build project with CMake',
        parameters={
            'type': 'object',
            'properties': {
                'build_dir': {
                    'type': 'string',
                    'format': 'filepath',
                    'description': 'Build directory name (default: "build")'
                },
                'config': {
                    'type': 'string',
                    'description': 'Build configuration: Debug or Release (default: "Release")'
                },
                'target': {
                    'type': 'string',
                    'description': 'Optional specific target to build'
                },
                'clean': {
                    'type': 'boolean',
                    'description': 'Clean before building (default: false)'
                }
            },
            'required': []
        },
        implementation=lambda build_dir="build", config="Release", target=None, clean=False: cmake_build(
            project_root, build_dir=build_dir, config=config, target=target, clean=clean
        )
    )

    # run_tests
    registry.register(
        name='run_tests',
        description='Run tests with ctest',
        parameters={
            'type': 'object',
            'properties': {
                'build_dir': {
                    'type': 'string',
                    'description': 'Build directory name (default: "build")'
                },
                'test_pattern': {
                    'type': 'string',
                    'description': 'Optional test name pattern (regex)'
                },
                'timeout': {
                    'type': 'integer',
                    'description': 'Timeout in seconds (default: 120)'
                }
            },
            'required': []
        },
        implementation=lambda build_dir="build", test_pattern=None, timeout=120: run_tests(
            project_root, build_dir=build_dir, test_pattern=test_pattern, timeout=timeout
        )
    )


def register_analyzer_tools(project_root: str):
    """Register analyzer tools (tree-sitter, etc.)"""
    # TODO: Implement when analyzer.py is ready
    pass


def register_agent_tools(agent):
    """Register agent control tools that require agent instance"""

    def compact_last(count: int, replacement: str) -> Dict[str, Any]:
        """
        Compact recent conversation messages by replacing them with a summary

        Args:
            count: Number of recent messages to replace (from end of history)
            replacement: Summary text to replace the messages with

        Returns:
            Dict with compaction results
        """
        try:
            # Validate count
            history_len = len(agent.conversation_history)
            if count <= 0:
                return {
                    'success': False,
                    'error': f'Invalid count: {count}. Must be positive.'
                }

            if count > history_len:
                return {
                    'success': False,
                    'error': f'Count {count} exceeds history length {history_len}'
                }

            # Get token counter
            token_counter = agent.token_counter
            max_tokens = token_counter.max_tokens
            tokens_before = token_counter.usage.get('total', 0)

            # Store messages that will be removed
            removed_messages = agent.conversation_history[-count:]

            # Remove last 'count' messages
            agent.conversation_history = agent.conversation_history[:-count]

            # Add replacement summary as assistant message
            agent.conversation_history.append({
                'role': 'assistant',
                'content': replacement
            })

            # Recalculate tokens (trigger token counter update)
            agent.token_counter.count_messages(agent.conversation_history)
            tokens_after = token_counter.usage.get('total', 0)
            tokens_saved = tokens_before - tokens_after

            return {
                'success': True,
                'messages_removed': count,
                'messages_current': len(agent.conversation_history),
                'tokens_before': tokens_before,
                'tokens_after': tokens_after,
                'tokens_saved': tokens_saved,
                'current_usage_pct': (tokens_after / max_tokens * 100) if max_tokens > 0 else 0
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # Register compact_last tool
    registry.register(
        name='compact_last',
        description=(
            'Compact recent conversation messages by replacing them with your summary. '
            'Use this when you have completed a phase of work and can summarize it concisely. '
            'This is more efficient than compress_context because YOU generate the summary in your output, '
            'saving an extra LLM call. '
            'Use when: '
            '(1) Completed debugging/exploration and have a clear summary, OR '
            '(2) Finished implementing a feature with detailed steps but simple outcome, OR '
            '(3) Token usage is high and recent messages contain redundant details. '
            'Example: After 10 messages of debugging, replace with "Fixed bug X by doing Y".'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': 'Number of recent messages to replace (including tool calls and results)',
                    'minimum': 1
                },
                'replacement': {
                    'type': 'string',
                    'description': 'Your concise summary to replace those messages with. Should capture key insights and decisions while removing verbose details.'
                }
            },
            'required': ['count', 'replacement']
        },
        implementation=compact_last
    )


def register_git_tools(project_root: str):
    """Register git version control tools"""
    from ..tools.git_tools import git

    registry.register(
        name='git',
        description='Execute git version control operations (status, add, commit, push, pull, etc.)',
        parameters={
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'enum': [
                        'status', 'add', 'commit', 'reset',
                        'branch', 'checkout', 'push', 'pull', 'fetch',
                        'rebase', 'stash', 'cherry-pick',
                        'log', 'diff', 'show'
                    ],
                    'description': 'Git operation to perform'
                },
                'args': {
                    'type': 'object',
                    'description': 'Action-specific arguments',
                    'additionalProperties': True
                }
            },
            'required': ['action']
        },
        implementation=lambda action, args=None: git(action, args or {}, project_root)
    )


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Get all registered tool schemas"""
    return registry.get_schemas()


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool by name"""
    return registry.execute(tool_name, arguments)


def initialize_tools(project_root: str):
    """Initialize all available tools"""
    register_filesystem_tools(project_root)
    register_executor_tools(project_root)
    register_git_tools(project_root)
    # register_analyzer_tools(project_root)
