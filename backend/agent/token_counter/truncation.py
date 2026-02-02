# -*- coding: utf-8 -*-
"""
Content truncation utilities
"""

from typing import Callable, Optional


class TruncationManager:
    """Manages content truncation for token limits"""

    def __init__(self, limits: dict, count_tokens: Callable[[str], int]):
        """
        Initialize truncation manager

        Args:
            limits: Dict with max_file_size, max_tool_result, etc.
            count_tokens: Function to count tokens in text
        """
        self.limits = limits
        self.count_tokens = count_tokens

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

            if self.count_tokens(partial) <= max_tokens - 100:
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
