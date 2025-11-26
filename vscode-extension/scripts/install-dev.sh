#!/bin/bash
# Install extension in development mode

set -e

echo "======================================"
echo "Claude-Qwen Extension - Dev Install"
echo "======================================"

# Check if in correct directory
if [ ! -f "package.json" ]; then
    echo "Error: Must run from vscode-extension directory"
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
npm install

# Compile TypeScript
echo ""
echo "Compiling TypeScript..."
npm run compile

# Package extension
echo ""
echo "Packaging extension..."
npm run package

# Find the .vsix file
VSIX_FILE=$(ls -t *.vsix 2>/dev/null | head -1)

if [ -z "$VSIX_FILE" ]; then
    echo "Error: No .vsix file found"
    exit 1
fi

echo ""
echo "Installing extension: $VSIX_FILE"
code --install-extension "$VSIX_FILE" --force

echo ""
echo "======================================"
echo "✓ Installation complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Reload VSCode: Ctrl+Shift+P → 'Developer: Reload Window'"
echo "2. Start Claude-Qwen: Ctrl+Shift+P → 'Claude-Qwen: Start'"
echo "3. Test integration: Ctrl+Shift+P → 'Claude-Qwen: Test VSCode Integration'"
echo ""
