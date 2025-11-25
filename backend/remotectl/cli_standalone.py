#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Control CLI for Ollama Management (Standalone Version)

This is a standalone version that can be run directly as a script.

Usage:
    python backend/remotectl/cli_standalone.py list
    python backend/remotectl/cli_standalone.py create
    python backend/remotectl/cli_standalone.py health
"""

import sys
from pathlib import Path

# Add project root to Python path for standalone execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the main CLI
from backend.remotectl.cli import main

if __name__ == '__main__':
    sys.exit(main())
