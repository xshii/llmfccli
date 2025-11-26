#!/bin/bash
# Quick launcher - detects environment and starts appropriate mode

PROJECT_ROOT="${1:-.}"

# Check if running inside VSCode terminal
if [ -n "$VSCODE_PID" ] || [ -n "$TERM_PROGRAM" ] && [ "$TERM_PROGRAM" = "vscode" ]; then
    echo "✓ Detected VSCode environment"
    echo "Starting CLI in VSCode integration mode..."
    export VSCODE_INTEGRATION=true
    python3 -m backend.cli --root "$PROJECT_ROOT"
else
    # Not in VSCode, offer to open it
    if command -v code &> /dev/null; then
        echo "VSCode available. Launch mode:"
        echo "  1) VSCode + Extension (recommended)"
        echo "  2) CLI only"
        read -p "Choice (1-2) [1]: " choice
        choice=${choice:-1}

        if [ "$choice" = "1" ]; then
            ./scripts/launch-vscode.sh "$PROJECT_ROOT"
        else
            python3 -m backend.cli --root "$PROJECT_ROOT"
        fi
    else
        # No VSCode, use CLI
        python3 -m backend.cli --root "$PROJECT_ROOT"
    fi
fi
