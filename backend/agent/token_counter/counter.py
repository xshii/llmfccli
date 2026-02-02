# -*- coding: utf-8 -*-
"""
Main TokenCounter class
"""

from pathlib import Path
from typing import Dict, List, Optional

from .budget import TokenBudget
from .compression import CompressionStrategy
from .config_loader import get_max_tokens_from_modelfile, load_token_budget_config
from .truncation import TruncationManager


class TokenCounter:
    """Token counter for managing context window budget"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize token counter with budget configuration

        Args:
            config_path: Path to token_budget.yaml
        """
        # Determine config paths
        if config_path is None:
            config_dir = Path(__file__).parent.parent.parent.parent / "config"
            config_path = config_dir / "token_budget.yaml"
        else:
            config_path = Path(config_path).resolve()
            config_dir = config_path.parent

        # Load configuration
        config = load_token_budget_config(config_path if config_path.exists() else None)
        self.config = config['token_management']

        # Get max_tokens from modelfile
        self.max_tokens = get_max_tokens_from_modelfile(config_dir) or 128000

        # Initialize components
        self._budget = TokenBudget(self.max_tokens, self.config['budgets'])
        self._compression = CompressionStrategy(
            self.config['compression'],
            self._budget.get_usage_percentage
        )
        self._truncation = TruncationManager(self.config['limits'], self.count_tokens)

        # Expose limits for backward compatibility
        self.limits = self.config['limits']
        self.compression_config = self.config['compression']
        self.budgets = self.config['budgets']

    # Token counting methods
    def count_tokens(self, text: str) -> int:
        """Count tokens using character-based estimation (~3 chars per token)"""
        return len(text) // 3

    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in message list"""
        total = 0
        for msg in messages:
            total += 4  # Role overhead
            content = msg.get('content', '')
            total += self.count_tokens(content)

            if 'tool_calls' in msg:
                total += len(str(msg['tool_calls'])) // 4

        return total

    # Budget delegation
    @property
    def usage(self) -> Dict[str, int]:
        return self._budget.usage

    def update_usage(self, category: str, tokens: int):
        self._budget.update_usage(category, tokens)

    def get_usage_percentage(self) -> float:
        return self._budget.get_usage_percentage()

    def get_budget_for_category(self, category: str) -> int:
        return self._budget.get_budget_for_category(category)

    def is_category_over_budget(self, category: str) -> bool:
        return self._budget.is_category_over_budget(category)

    def get_usage_report(self) -> str:
        return self._budget.get_usage_report()

    # Compression delegation
    @property
    def last_compression_time(self) -> float:
        return self._compression.last_compression_time

    @last_compression_time.setter
    def last_compression_time(self, value: float):
        self._compression.last_compression_time = value

    def should_compress(self, current_time: float) -> bool:
        return self._compression.should_compress(current_time)

    def get_compression_target(self) -> int:
        return self._compression.get_compression_target(self.max_tokens)

    def categorize_messages(self, messages: List[Dict[str, str]],
                           active_files: List[str]) -> Dict[str, List[int]]:
        return self._compression.categorize_messages(messages, active_files)

    def estimate_compression_savings(self, messages: List[Dict[str, str]],
                                    keep_indices: List[int]) -> int:
        return self._compression.estimate_compression_savings(
            messages, keep_indices, self.count_messages
        )

    # Truncation delegation
    def truncate_file_content(self, content: str, max_tokens: Optional[int] = None) -> str:
        return self._truncation.truncate_file_content(content, max_tokens)

    def truncate_tool_result(self, result: str, max_tokens: Optional[int] = None) -> str:
        return self._truncation.truncate_tool_result(result, max_tokens)
