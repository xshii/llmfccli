# -*- coding: utf-8 -*-
"""
Context management with compression support
"""

import time
from typing import List, Dict, Any, Optional
from .token_counter import TokenCounter


class ContextManager:
    """Manage conversation context with intelligent compression"""
    
    def __init__(self, token_counter: TokenCounter):
        """
        Initialize context manager
        
        Args:
            token_counter: TokenCounter instance
        """
        self.token_counter = token_counter
        self.messages: List[Dict[str, str]] = []
        self.active_files: List[str] = []
        self.project_structure: str = ""
        self.module_map: Dict[str, Any] = {}
        
    def add_message(self, message: Dict[str, str]):
        """
        Add message and update token count
        
        Args:
            message: Message dict with 'role' and 'content'
        """
        self.messages.append(message)
        
        # Update token usage
        total_tokens = self.token_counter.count_messages(self.messages)
        self.token_counter.update_usage('recent_messages', total_tokens)
    
    def add_active_file(self, file_path: str, content: str):
        """
        Track active file
        
        Args:
            file_path: File path
            content: File content
        """
        if file_path not in self.active_files:
            self.active_files.append(file_path)
        
        # Update active files token count
        file_tokens = self.token_counter.count_tokens(content)
        current = self.token_counter.usage.get('active_files', 0)
        self.token_counter.update_usage('active_files', current + file_tokens)
    
    def set_project_structure(self, structure: str):
        """
        Set project directory structure
        
        Args:
            structure: Directory tree string
        """
        self.project_structure = structure
        tokens = self.token_counter.count_tokens(structure)
        self.token_counter.update_usage('project_structure', tokens)
    
    def should_compress(self, current_time: float) -> bool:
        """Check if compression should be triggered"""
        return self.token_counter.should_compress(current_time)
    
    def compress(self, llm_client, must_keep_info: str = "") -> Dict[str, Any]:
        """
        Compress context using LLM
        
        Args:
            llm_client: OllamaClient instance
            must_keep_info: Additional must-keep information
            
        Returns:
            Compression result
        """
        # Build must-keep description
        must_keep = f"""
Active Files:
{chr(10).join(f"  - {f}" for f in self.active_files)}

Project Structure:
{self.project_structure}

{must_keep_info}
"""
        
        # Build compressible description
        compressible = f"""
Conversation history: {len(self.messages)} messages
Total tokens: {self.token_counter.usage['total']}
"""
        
        # Get target tokens
        target_tokens = self.token_counter.get_compression_target()
        current_tokens = self.token_counter.usage['total']
        
        # Call LLM to compress
        result = llm_client.compress_context(
            self.messages,
            target_tokens,
            must_keep,
            compressible
        )
        
        return result
    
    def apply_compression(self, compression_result: Dict[str, Any]):
        """
        Apply compression result to context
        
        Args:
            compression_result: Result from compress()
        """
        keep_indices = compression_result.get('keep_message_indices', [])
        compressed_summary = compression_result.get('compressed_summary', '')
        processed_files = compression_result.get('processed_files_summary', {})
        
        # Build new message list
        new_messages = []
        
        # Add compressed summary as system message
        if compressed_summary:
            new_messages.append({
                'role': 'system',
                'content': f"[Compressed Context]\n{compressed_summary}"
            })
        
        # Add kept messages
        for idx in sorted(keep_indices):
            if 0 <= idx < len(self.messages):
                new_messages.append(self.messages[idx])
        
        # Update messages
        self.messages = new_messages
        
        # Update token counts
        recent_tokens = self.token_counter.count_messages(new_messages)
        self.token_counter.update_usage('recent_messages', recent_tokens)
        
        # Update processed files summary
        if processed_files:
            summary_text = '\n'.join(
                f"{file}: {summary}" 
                for file, summary in processed_files.items()
            )
            summary_tokens = self.token_counter.count_tokens(summary_text)
            self.token_counter.update_usage('processed_files', summary_tokens)
        
        # Update compression time
        self.token_counter.last_compression_time = time.time()
    
    def get_context_for_llm(self, system_prompt: str) -> List[Dict[str, str]]:
        """
        Get full context for LLM call
        
        Args:
            system_prompt: System prompt to prepend
            
        Returns:
            List of messages including system prompt
        """
        return [
            {'role': 'system', 'content': system_prompt},
            *self.messages
        ]
    
    def categorize_for_compression(self) -> Dict[str, List[int]]:
        """
        Categorize messages for selective compression
        
        Returns:
            Dict mapping category to message indices
        """
        return self.token_counter.categorize_messages(
            self.messages,
            self.active_files
        )
    
    def get_summary(self) -> str:
        """Get context summary"""
        return f"""
Context Summary:
- Messages: {len(self.messages)}
- Active files: {len(self.active_files)}
- Total tokens: {self.token_counter.usage['total']} / {self.token_counter.max_tokens}
- Usage: {self.token_counter.get_usage_percentage():.1%}
"""
    
    def clear_history(self, keep_files: bool = True):
        """
        Clear conversation history
        
        Args:
            keep_files: Keep active files tracking
        """
        self.messages = []
        self.token_counter.update_usage('recent_messages', 0)
        
        if not keep_files:
            self.active_files = []
            self.token_counter.update_usage('active_files', 0)
