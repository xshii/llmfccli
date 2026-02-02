# -*- coding: utf-8 -*-
"""
Pre-check result container
"""

from typing import Dict, Optional


class PreCheckResult:
    """Result of a pre-check"""

    def __init__(self, name: str, success: bool, message: str, details: Optional[Dict] = None):
        self.name = name
        self.success = success
        self.message = message
        self.details = details or {}

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.name}: {self.message}"
