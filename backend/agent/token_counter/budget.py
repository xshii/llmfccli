# -*- coding: utf-8 -*-
"""
Token budget management
"""

from typing import Dict


class TokenBudget:
    """Manages token budgets by category"""

    def __init__(self, max_tokens: int, budgets: Dict[str, float]):
        """
        Initialize token budget

        Args:
            max_tokens: Maximum total tokens
            budgets: Dict of category -> ratio (0-1)
        """
        self.max_tokens = max_tokens
        self.budgets = budgets

        # Track usage by category
        self.usage: Dict[str, int] = {
            'active_files': 0,
            'processed_files': 0,
            'project_structure': 0,
            'compressed_history': 0,
            'recent_messages': 0,
            'total': 0
        }

    def update_usage(self, category: str, tokens: int):
        """Update token usage for a category"""
        if category in self.usage:
            self.usage[category] = tokens
            self.usage['total'] = sum(
                v for k, v in self.usage.items() if k != 'total'
            )

    def get_usage_percentage(self) -> float:
        """Get current token usage percentage (0-1)"""
        return self.usage['total'] / self.max_tokens

    def get_budget_for_category(self, category: str) -> int:
        """Get token budget for a category"""
        if category not in self.budgets:
            return 0
        ratio = self.budgets[category]
        return int(self.max_tokens * ratio)

    def is_category_over_budget(self, category: str) -> bool:
        """Check if category exceeds its budget"""
        budget = self.get_budget_for_category(category)
        current = self.usage.get(category, 0)
        return current > budget

    def get_usage_report(self) -> str:
        """Generate human-readable usage report"""
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
