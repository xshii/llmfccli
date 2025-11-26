#!/bin/bash
# Launch Claude-Qwen in VSCode integrated mode
#
# This script:
# 1. Opens VSCode in the current directory
# 2. Automatically starts the Claude-Qwen extension
# 3. Falls back to CLI if VSCode is not available

set -e

PROJECT_ROOT="${1:-.}"

echo "======================================"
echo "Claude-Qwen Launcher"
echo "======================================"
echo ""

# Check if VSCode is installed
if ! command -v code &> /dev/null; then
    echo "❌ VSCode 'code' command not found"
    echo ""
    echo "Install it via:"
    echo "  VSCode → Command Palette → 'Shell Command: Install code command in PATH'"
    echo ""
    echo "Falling back to CLI mode..."
    echo ""
    python3 -m backend.cli --root "$PROJECT_ROOT"
    exit 0
fi

# Check if Claude-Qwen extension is installed
EXTENSION_ID="claude-qwen.claude-qwen"
if code --list-extensions 2>/dev/null | grep -q "$EXTENSION_ID"; then
    echo "✓ Claude-Qwen extension detected"
    EXTENSION_INSTALLED=true
else
    echo "⚠ Claude-Qwen extension not installed"
    EXTENSION_INSTALLED=false
fi

echo ""
echo "Project: $PROJECT_ROOT"
echo ""

# Offer installation if extension not found
if [ "$EXTENSION_INSTALLED" = false ]; then
    echo "Would you like to:"
    echo "  1) Install extension and open VSCode"
    echo "  2) Open VSCode without extension"
    echo "  3) Use CLI mode"
    echo ""
    read -p "Choice (1-3): " choice

    case $choice in
        1)
            echo ""
            echo "Installing extension..."
            VSIX_FILE="vscode-extension/claude-qwen-0.1.0.vsix"

            if [ ! -f "$VSIX_FILE" ]; then
                echo "Building extension..."
                cd vscode-extension
                npm install
                npm run compile
                npm run package
                cd ..
            fi

            code --install-extension "$VSIX_FILE"
            echo "✓ Extension installed"
            ;;
        2)
            echo "Opening VSCode without extension..."
            ;;
        3)
            echo "Starting CLI mode..."
            python3 -m backend.cli --root "$PROJECT_ROOT"
            exit 0
            ;;
        *)
            echo "Invalid choice, exiting..."
            exit 1
            ;;
    esac
fi

# Open VSCode
echo ""
echo "Opening VSCode..."
code "$PROJECT_ROOT"

# Show next steps
echo ""
echo "======================================"
echo "✓ VSCode opened"
echo "======================================"
echo ""

if [ "$EXTENSION_INSTALLED" = true ]; then
    echo "Next steps:"
    echo "  1. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)"
    echo "  2. Type: 'Claude-Qwen: Start'"
    echo "  3. Start coding with AI assistance!"
else
    echo "Extension installed. Please:"
    echo "  1. Reload VSCode: Ctrl+Shift+P → 'Developer: Reload Window'"
    echo "  2. Then: Ctrl+Shift+P → 'Claude-Qwen: Start'"
fi

echo ""
