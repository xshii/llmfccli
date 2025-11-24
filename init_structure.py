#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize Claude-Qwen project structure
"""

import os
from pathlib import Path


def create_directory_structure():
    """Create necessary directories"""
    
    base = Path(__file__).parent
    
    directories = [
        'backend/llm',
        'backend/agent',
        'backend/tools',
        'config',
        'tests/fixtures/sample-cpp/src/parser',
        'tests/fixtures/sample-cpp/src/network',
        'tests/fixtures/sample-cpp/src/http',
        'tests/fixtures/sample-cpp/tests',
    ]
    
    for directory in directories:
        path = base / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}")


if __name__ == '__main__':
    print("Initializing Claude-Qwen project structure...")
    create_directory_structure()
    print("\nDone! Run 'pip install -e .[dev]' to install dependencies.")
