"""
Agent main loop for executing tasks with LLM and tools
"""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..llm.client import OllamaClient
from .token_counter import TokenCounter
from .tools import initialize_tools, get_tool_schemas, execute_tool


class AgentLoop:
    """Main agent loop for task execution"""
    
    def __init__(self, client: Optional[OllamaClient] = None, 
                 project_root: Optional[str] = None):
        """
        Initialize agent loop
        
        Args:
            client: OllamaClient instance
            project_root: Project root directory
        """
        self.client = client or OllamaClient()
        self.project_root = project_root or str(Path.cwd())
        
        # Initialize components
        self.token_counter = TokenCounter()
        
        # Initialize tools
        initialize_tools(self.project_root)
        
        # State
        self.conversation_history: List[Dict[str, str]] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.active_files: List[str] = []
        
        # Configuration
        self.max_iterations = 20
        self.max_retries = 3
        self.stopped_due_to_max_retries = False
        
        # Active file (for VSCode integration)
        self.active_file: Optional[str] = None
    
    def set_project_root(self, root: str):
        """Set project root and reinitialize tools"""
        self.project_root = root
        initialize_tools(self.project_root)
    
    def set_active_file(self, file_path: str):
        """Set active file (from VSCode)"""
        self.active_file = file_path
    
    def set_max_retries(self, max_retries: int):
        """Set maximum retry count"""
        self.max_retries = max_retries
    
    def run(self, user_input: str) -> str:
        """
        Execute agent loop for user input
        
        Args:
            user_input: User's request
            
        Returns:
            Agent's final response
        """
        # Add user message
        user_message = {'role': 'user', 'content': user_input}
        self.conversation_history.append(user_message)
        
        # Update token count
        self.token_counter.update_usage(
            'recent_messages',
            self.token_counter.count_messages(self.conversation_history)
        )
        
        # Get system prompt
        from ..llm.prompts import get_system_prompt
        messages = [
            {'role': 'system', 'content': get_system_prompt()},
            *self.conversation_history
        ]
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Get tool schemas
            tools = get_tool_schemas()

            # DEBUG: Log request
            import os
            if os.getenv('DEBUG_AGENT'):
                print(f"\n=== LLM REQUEST (iteration {iteration}) ===")
                import json
                print(f"Messages count: {len(messages)}")
                print(f"Last message: {messages[-1] if messages else 'none'}")
                print(f"Tools count: {len(tools)}")
                if tools:
                    print(f"First tool: {tools[0]['function']['name']}")
                print("=== END REQUEST ===\n")

            # Call LLM
            try:
                response = self.client.chat_with_tools(messages, tools)

                # DEBUG: Log raw response
                if os.getenv('DEBUG_AGENT'):
                    print(f"\n=== RAW LLM RESPONSE (iteration {iteration}) ===")
                    import json
                    print(json.dumps(response, indent=2, ensure_ascii=False))
                    print("=== END RAW RESPONSE ===\n")

            except Exception as e:
                error_msg = f"LLM call failed: {e}"
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': error_msg
                })
                return error_msg

            # Extract message
            assistant_message = response.get('message', {})
            content = assistant_message.get('content', '')

            # Parse tool calls
            tool_calls = self.client.parse_tool_calls(response)
            
            # No tool calls - conversation complete
            if not tool_calls:
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': content
                })
                return content
            
            # Execute tool calls
            self.tool_calls.extend(tool_calls)
            
            # Add assistant message with tool calls
            self.conversation_history.append({
                'role': 'assistant',
                'content': content,
                'tool_calls': tool_calls
            })
            
            # Execute each tool
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                
                # Parse arguments
                try:
                    arguments = tool_call['function']['arguments']
                    if isinstance(arguments, str):
                        import json
                        arguments = json.loads(arguments)
                except Exception as e:
                    arguments = {}
                
                # Execute tool
                result = execute_tool(tool_name, arguments)

                # DEBUG: Log tool results
                import os
                if os.getenv('DEBUG_AGENT'):
                    print(f"\n=== TOOL RESULT: {tool_name} ===")
                    print(f"Args: {arguments}")
                    result_str = str(result)[:500]  # First 500 chars
                    print(f"Result: {result_str}...")
                    print("=== END TOOL RESULT ===\n")

                # Track active files
                if tool_name in ['view_file', 'edit_file', 'create_file']:
                    file_path = arguments.get('path', '')
                    if file_path and file_path not in self.active_files:
                        self.active_files.append(file_path)

                # Add tool result to history
                tool_message = {
                    'role': 'tool',
                    'content': self._format_tool_result(result),
                    'tool_call_id': tool_call.get('id', f'call_{iteration}')
                }
                self.conversation_history.append(tool_message)
            
            # Update messages for next iteration
            messages = [
                {'role': 'system', 'content': get_system_prompt()},
                *self.conversation_history
            ]
            
            # Check if should compress
            if self.token_counter.should_compress(time.time()):
                self._compress_context()
        
        # Max iterations reached
        final_msg = f"Reached maximum iterations ({self.max_iterations}). Task may be incomplete."
        self.conversation_history.append({
            'role': 'assistant',
            'content': final_msg
        })
        return final_msg
    
    def _format_tool_result(self, result: Any) -> str:
        """Format tool result for LLM"""
        import json
        
        if isinstance(result, dict):
            # Truncate large content
            if 'content' in result:
                content = result['content']
                result = result.copy()
                result['content'] = self.token_counter.truncate_tool_result(content)
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return str(result)
    
    def _compress_context(self):
        """Compress conversation history"""
        # Build must-keep information
        must_keep = f"""
Active files: {', '.join(self.active_files)}
Project structure: {self.project_root}
"""
        
        # Build compressible content
        compressible = f"{len(self.conversation_history)} messages"
        
        # Get current and target tokens
        current_tokens = self.token_counter.count_messages(self.conversation_history)
        target_tokens = self.token_counter.get_compression_target()
        
        try:
            # Call LLM to compress
            compression_result = self.client.compress_context(
                self.conversation_history,
                target_tokens,
                must_keep,
                compressible
            )
            
            # Apply compression
            keep_indices = compression_result.get('keep_message_indices', [])
            compressed_summary = compression_result.get('compressed_summary', '')
            
            # Build new history
            new_history = []
            
            # Add compressed summary
            if compressed_summary:
                new_history.append({
                    'role': 'system',
                    'content': f"[Compressed History]\n{compressed_summary}"
                })
            
            # Add kept messages
            for idx in keep_indices:
                if 0 <= idx < len(self.conversation_history):
                    new_history.append(self.conversation_history[idx])
            
            # Update history
            self.conversation_history = new_history
            
            # Update token count
            self.token_counter.update_usage(
                'compressed_history',
                self.token_counter.count_messages(new_history)
            )
            
            # Update last compression time
            self.token_counter.last_compression_time = time.time()
            
        except Exception as e:
            print(f"Warning: Context compression failed: {e}")
    
    def get_usage_report(self) -> str:
        """Get token usage report"""
        return self.token_counter.get_usage_report()
    
    def save_session(self, session_file: str):
        """Save current session to file"""
        import json
        from datetime import datetime
        
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'project_root': self.project_root,
            'active_files': self.active_files,
            'last_error': self.conversation_history[-1].get('content', '') if self.conversation_history else '',
            'attempted_fixes': [
                {
                    'tool': call['function']['name'],
                    'arguments': call['function'].get('arguments', {})
                }
                for call in self.tool_calls[-5:]  # Last 5 tool calls
            ],
            'compressed_context': self._get_context_summary(),
            'next_steps': self._suggest_next_steps()
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def _get_context_summary(self) -> str:
        """Get summary of current context"""
        summary_parts = [
            f"Files modified: {len(self.active_files)}",
            f"Tool calls: {len(self.tool_calls)}",
            f"Messages: {len(self.conversation_history)}"
        ]
        return '; '.join(summary_parts)
    
    def _suggest_next_steps(self) -> List[str]:
        """Suggest next steps based on current state"""
        suggestions = []
        
        # Check if there were compilation errors
        if any('error' in str(call).lower() for call in self.tool_calls[-3:]):
            suggestions.append("Review compilation errors manually")
            suggestions.append("Check if dependencies are properly configured")
        
        # Check if files were modified
        if self.active_files:
            suggestions.append(f"Review changes in: {', '.join(self.active_files[:3])}")
        
        # Default suggestion
        if not suggestions:
            suggestions.append("Verify the changes and test manually")
        
        return suggestions
