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
    from ..tools.filesystem import view_file, edit_file, create_file, grep_search, list_dir
    
    # view_file
    registry.register(
        name='view_file',
        description='Read file contents with optional line range',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
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
    from ..tools.executor import bash_run, cmake_build, run_tests

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

    def compress_context(target_ratio: float = None) -> Dict[str, Any]:
        """
        Compress conversation context to save tokens

        Args:
            target_ratio: Target token usage ratio (0.0-1.0), defaults to 0.6 (60%)

        Returns:
            Dict with compression results
        """
        try:
            # Get token counter
            token_counter = agent.token_counter
            max_tokens = token_counter.max_tokens
            current_total = token_counter.usage.get('total', 0)

            # Set default target ratio if not provided
            if target_ratio is None:
                target_ratio = token_counter.compression_config['target_after_compress']

            # Validate ratio
            if not (0.0 < target_ratio < 1.0):
                return {
                    'success': False,
                    'error': f'Invalid target_ratio: {target_ratio}. Must be between 0.0 and 1.0'
                }

            target_tokens = int(max_tokens * target_ratio)

            # Store counts before compression
            msg_count_before = len(agent.conversation_history)
            tokens_before = current_total

            # Perform compression
            agent._compress_context()

            # Get counts after compression
            msg_count_after = len(agent.conversation_history)
            tokens_after = token_counter.usage.get('total', 0)
            tokens_saved = tokens_before - tokens_after

            return {
                'success': True,
                'messages_before': msg_count_before,
                'messages_after': msg_count_after,
                'messages_removed': msg_count_before - msg_count_after,
                'tokens_before': tokens_before,
                'tokens_after': tokens_after,
                'tokens_saved': tokens_saved,
                'target_ratio': target_ratio,
                'current_usage_pct': (tokens_after / max_tokens * 100) if max_tokens > 0 else 0
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # Register compress_context tool
    registry.register(
        name='compress_context',
        description=(
            'Compress conversation history intelligently. Use when: '
            '(1) Token usage is high (>70%), OR '
            '(2) Completed a phase of work and formed a summary, OR '
            '(3) The ratio of valuable summary to raw details is good for compression. '
            'This tool helps maintain context efficiency by condensing completed work while preserving key insights. '
            'You should proactively evaluate when compression would be beneficial, not just when tokens are full.'
        ),
        parameters={
            'type': 'object',
            'properties': {
                'target_ratio': {
                    'type': 'number',
                    'description': 'Target token usage ratio after compression (0.0-1.0), defaults to 0.6',
                    'minimum': 0.1,
                    'maximum': 0.9
                }
            },
            'required': []
        },
        implementation=compress_context
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
    # register_analyzer_tools(project_root)
