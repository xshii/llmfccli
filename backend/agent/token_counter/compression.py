# -*- coding: utf-8 -*-
"""
Compression strategy and message categorization
"""

from typing import Callable, Dict, List


class CompressionStrategy:
    """Manages compression decisions and message categorization"""

    def __init__(self, config: dict, get_usage_percentage: Callable[[], float]):
        """
        Initialize compression strategy

        Args:
            config: Compression config with trigger_threshold, min_interval, etc.
            get_usage_percentage: Function to get current usage percentage
        """
        self.config = config
        self.get_usage_percentage = get_usage_percentage
        self.last_compression_time = 0

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
        threshold = self.config['trigger_threshold']

        if usage_pct < threshold:
            return False

        # Check minimum interval
        min_interval = self.config['min_interval']
        time_since_last = current_time - self.last_compression_time

        if time_since_last < min_interval:
            return False

        return True

    def get_compression_target(self, max_tokens: int) -> int:
        """
        Get target token count after compression

        Args:
            max_tokens: Maximum total tokens

        Returns:
            Target token count
        """
        target_ratio = self.config.get('target_after_compress', 0.6)
        return int(max_tokens * target_ratio)

    def categorize_messages(
        self,
        messages: List[Dict[str, str]],
        active_files: List[str]
    ) -> Dict[str, List[int]]:
        """
        Categorize messages by type for selective compression

        Args:
            messages: Message list
            active_files: List of currently active file paths

        Returns:
            Dict mapping category to message indices
        """
        categories = {
            'recent': [],
            'active_file': [],
            'tool_output': [],
            'decision': [],
            'redundant': []
        }

        # Keep last 5 messages as recent
        recent_count = 5
        for i in range(max(0, len(messages) - recent_count), len(messages)):
            categories['recent'].append(i)

        # Categorize older messages
        for i, msg in enumerate(messages[:-recent_count] if len(messages) > recent_count else []):
            content = msg.get('content', '').lower()

            if any(f in content for f in active_files):
                categories['active_file'].append(i)
                continue

            if msg.get('role') == 'tool':
                categories['tool_output'].append(i)
                continue

            decision_keywords = ['decide', 'plan', 'strategy', 'approach']
            if any(kw in content for kw in decision_keywords):
                categories['decision'].append(i)
                continue

            categories['redundant'].append(i)

        return categories

    def estimate_compression_savings(
        self,
        messages: List[Dict[str, str]],
        keep_indices: List[int],
        count_messages: Callable[[List[Dict]], int]
    ) -> int:
        """
        Estimate tokens saved by compression

        Args:
            messages: Full message list
            keep_indices: Indices to keep uncompressed
            count_messages: Function to count tokens in messages

        Returns:
            Estimated tokens saved
        """
        total_tokens = count_messages(messages)
        keep_tokens = count_messages([messages[i] for i in keep_indices if i < len(messages)])

        # Assume compressed summary is 20% of removed content
        removed_tokens = total_tokens - keep_tokens
        summary_tokens = int(removed_tokens * 0.2)

        return removed_tokens - summary_tokens
