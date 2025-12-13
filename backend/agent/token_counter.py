# -*- coding: utf-8 -*-
"""
Token counter using character-based estimation
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml
import re


def _parse_modelfile_num_ctx(modelfile_path: Path) -> Optional[int]:
    """
    Parse num_ctx from modelfile

    Args:
        modelfile_path: Path to the modelfile

    Returns:
        num_ctx value if found, None otherwise
    """
    try:
        if not modelfile_path.exists():
            return None

        with open(modelfile_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match: PARAMETER num_ctx <number>
        match = re.search(r'PARAMETER\s+num_ctx\s+(\d+)', content)
        if match:
            return int(match.group(1))
        return None
    except Exception:
        return None


class TokenCounter:
    """Token counter for managing context window budget"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize token counter with budget configuration

        Args:
            config_path: Path to token_budget.yaml
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "token_budget.yaml"

        config_path = Path(config_path).resolve()

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            # Use default config
            config = {
                'token_management': {
                    'max_tokens': 128000,
                    'budgets': {
                        'active_files': 0.25,
                        'processed_files': 0.15,
                        'project_structure': 0.05,
                        'compressed_history': 0.30,
                        'recent_messages': 0.25
                    },
                    'compression': {
                        'trigger_threshold': 0.85,
                        'min_interval': 300,
                        'max_retries': 2
                    },
                    'limits': {
                        'max_file_size': 10000,
                        'max_compile_output': 2000,
                        'max_tool_result': 5000
                    }
                }
            }

        self.config = config['token_management']
        self.budgets = self.config['budgets']
        self.compression_config = self.config['compression']
        self.limits = self.config['limits']

        # Try to get max_tokens from modelfile first (single source of truth)
        self.max_tokens = self._get_max_tokens_from_modelfile()
        if self.max_tokens is None:
            # Fallback to config
            self.max_tokens = self.config['max_tokens']

        # Track token usage by category
        self.usage = {
            'active_files': 0,
            'processed_files': 0,
            'project_structure': 0,
            'compressed_history': 0,
            'recent_messages': 0,
            'total': 0
        }

        self.last_compression_time = 0

    def _get_max_tokens_from_modelfile(self) -> Optional[int]:
        """
        Get max_tokens from modelfile's num_ctx parameter

        Returns:
            num_ctx value if found, None otherwise
        """
        try:
            # Load llm.yaml to find modelfile path
            config_dir = Path(__file__).parent.parent.parent / "config"
            llm_config_path = config_dir / "llm.yaml"

            if not llm_config_path.exists():
                return None

            with open(llm_config_path, 'r', encoding='utf-8') as f:
                llm_config = yaml.safe_load(f)

            # Get modelfile path from model_management section
            model_mgmt = llm_config.get('model_management', {})
            models = model_mgmt.get('models', [])

            if not models:
                return None

            # Use the first enabled model's modelfile
            for model in models:
                if model.get('enabled', True):
                    modelfile_rel = model.get('modelfile', '')
                    if modelfile_rel:
                        modelfile_path = config_dir / modelfile_rel
                        num_ctx = _parse_modelfile_num_ctx(modelfile_path)
                        if num_ctx:
                            return num_ctx

            return None
        except Exception:
            return None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using character-based estimation

        Args:
            text: Input text

        Returns:
            Estimated token count (~3 chars per token for mixed content)
        """
        return len(text) // 3
    
    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in message list
        
        Args:
            messages: List of message dicts
            
        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            # Count role
            total += 4  # Role overhead
            
            # Count content
            content = msg.get('content', '')
            total += self.count_tokens(content)
            
            # Tool calls overhead
            if 'tool_calls' in msg:
                total += len(str(msg['tool_calls'])) // 4
        
        return total
    
    def update_usage(self, category: str, tokens: int):
        """
        Update token usage for a category
        
        Args:
            category: Category name
            tokens: Token count to add
        """
        if category in self.usage:
            self.usage[category] = tokens
            self.usage['total'] = sum(
                v for k, v in self.usage.items() if k != 'total'
            )
    
    def get_usage_percentage(self) -> float:
        """
        Get current token usage percentage
        
        Returns:
            Usage as percentage (0-1)
        """
        return self.usage['total'] / self.max_tokens
    
    def should_compress(self, current_time: float) -> bool:
        """
        Check if compression should be triggered
        
        Args:
            current_time: Current timestamp
            
        Returns:
            True if compression needed
        """
        # Check usage threshold
        usage_pct = self.get_usage_percentage()
        threshold = self.compression_config['trigger_threshold']
        
        if usage_pct < threshold:
            return False
        
        # Check minimum interval
        min_interval = self.compression_config['min_interval']
        time_since_last = current_time - self.last_compression_time
        
        if time_since_last < min_interval:
            return False
        
        return True
    
    def get_budget_for_category(self, category: str) -> int:
        """
        Get token budget for a category
        
        Args:
            category: Category name
            
        Returns:
            Token budget
        """
        if category not in self.budgets:
            return 0
        
        ratio = self.budgets[category]
        return int(self.max_tokens * ratio)
    
    def is_category_over_budget(self, category: str) -> bool:
        """
        Check if category exceeds its budget
        
        Args:
            category: Category name
            
        Returns:
            True if over budget
        """
        budget = self.get_budget_for_category(category)
        current = self.usage.get(category, 0)
        return current > budget
    
    def get_compression_target(self) -> int:
        """
        Get target token count after compression
        
        Returns:
            Target token count
        """
        target_ratio = self.compression_config['target_after_compress']
        return int(self.max_tokens * target_ratio)
    
    def categorize_messages(self, messages: List[Dict[str, str]], 
                           active_files: List[str]) -> Dict[str, List[int]]:
        """
        Categorize messages by type for selective compression
        
        Args:
            messages: Message list
            active_files: List of currently active file paths
            
        Returns:
            Dict mapping category to message indices
        """
        categories = {
            'recent': [],      # Last N messages (uncompressed)
            'active_file': [], # Messages about active files
            'tool_output': [], # Tool execution results
            'decision': [],    # Key decision points
            'redundant': []    # Redundant/compressible
        }
        
        # Keep last 5 messages as recent
        recent_count = 5
        for i in range(max(0, len(messages) - recent_count), len(messages)):
            categories['recent'].append(i)
        
        # Categorize older messages
        for i, msg in enumerate(messages[:-recent_count]):
            content = msg.get('content', '').lower()
            
            # Check if about active files
            if any(f in content for f in active_files):
                categories['active_file'].append(i)
                continue
            
            # Check if tool output
            if msg.get('role') == 'tool':
                categories['tool_output'].append(i)
                continue
            
            # Check if decision point
            decision_keywords = ['decide', 'plan', 'strategy', 'approach']
            if any(kw in content for kw in decision_keywords):
                categories['decision'].append(i)
                continue
            
            # Otherwise mark as redundant
            categories['redundant'].append(i)
        
        return categories
    
    def estimate_compression_savings(self, messages: List[Dict[str, str]], 
                                    keep_indices: List[int]) -> int:
        """
        Estimate tokens saved by compression
        
        Args:
            messages: Full message list
            keep_indices: Indices to keep uncompressed
            
        Returns:
            Estimated tokens saved
        """
        total_tokens = self.count_messages(messages)
        keep_tokens = self.count_messages([messages[i] for i in keep_indices])
        
        # Assume compressed summary is 20% of removed content
        removed_tokens = total_tokens - keep_tokens
        summary_tokens = int(removed_tokens * 0.2)
        
        return removed_tokens - summary_tokens
    
    def get_usage_report(self) -> str:
        """
        Generate human-readable usage report
        
        Returns:
            Formatted usage report
        """
        lines = ["Token Usage Report", "=" * 40]
        
        for category, tokens in self.usage.items():
            if category == 'total':
                continue
            
            budget = self.get_budget_for_category(category)
            percentage = (tokens / budget * 100) if budget > 0 else 0
            status = "✓" if tokens <= budget else "⚠"
            
            lines.append(
                f"{status} {category:20s}: {tokens:6d} / {budget:6d} ({percentage:.1f}%)"
            )
        
        lines.append("=" * 40)
        total_pct = self.get_usage_percentage() * 100
        lines.append(f"Total: {self.usage['total']:6d} / {self.max_tokens:6d} ({total_pct:.1f}%)")
        
        return "\n".join(lines)
    
    def truncate_file_content(self, content: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate file content if exceeds limit
        
        Args:
            content: File content
            max_tokens: Max tokens (default from config)
            
        Returns:
            Truncated content with indicator
        """
        if max_tokens is None:
            max_tokens = self.limits['max_file_size']
        
        tokens = self.count_tokens(content)
        
        if tokens <= max_tokens:
            return content
        
        # Binary search for cutoff point
        lines = content.split('\n')
        left, right = 0, len(lines)
        
        while left < right:
            mid = (left + right + 1) // 2
            partial = '\n'.join(lines[:mid])
            
            if self.count_tokens(partial) <= max_tokens - 100:  # Reserve 100 for indicator
                left = mid
            else:
                right = mid - 1
        
        truncated = '\n'.join(lines[:left])
        truncated += f"\n\n[... truncated {len(lines) - left} lines, {tokens - max_tokens} tokens ...]"
        
        return truncated
    
    def truncate_tool_result(self, result: str, max_tokens: Optional[int] = None) -> str:
        """
        Truncate tool result if exceeds limit
        
        Args:
            result: Tool result string
            max_tokens: Max tokens (default from config)
            
        Returns:
            Truncated result
        """
        if max_tokens is None:
            max_tokens = self.limits['max_tool_result']
        
        tokens = self.count_tokens(result)
        
        if tokens <= max_tokens:
            return result
        
        # Keep beginning and end
        keep_ratio = max_tokens / tokens
        lines = result.split('\n')
        keep_lines = int(len(lines) * keep_ratio)
        
        head_lines = keep_lines // 2
        tail_lines = keep_lines - head_lines
        
        head = '\n'.join(lines[:head_lines])
        tail = '\n'.join(lines[-tail_lines:])
        
        return f"{head}\n\n[... truncated {len(lines) - keep_lines} lines ...]\n\n{tail}"
