#!/bin/bash
# Uninstall Claude-Qwen extension

set -e

echo "Uninstalling Claude-Qwen extension..."

code --uninstall-extension claude-qwen.claude-qwen 2>/dev/null || true

echo "✓ Extension uninstalled"
echo ""
echo "Note: You may need to reload VSCode for changes to take effect"
echo "Run: Ctrl+Shift+P → 'Developer: Reload Window'"
