#!/bin/bash
# Reload claude-qwen model with updated Modelfile

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODELFILE="$PROJECT_ROOT/config/modelfiles/claude-qwen.modelfile"
MODEL_NAME="claude-qwen:latest"

echo "================================================"
echo "  Reloading Claude-Qwen Model"
echo "================================================"
echo ""
echo "Modelfile: $MODELFILE"
echo "Model Name: $MODEL_NAME"
echo ""

# Check if modelfile exists
if [ ! -f "$MODELFILE" ]; then
    echo "ERROR: Modelfile not found at $MODELFILE"
    exit 1
fi

# Create/update the model
echo "Creating model from Modelfile..."
ollama create "$MODEL_NAME" -f "$MODELFILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Model reloaded successfully!"
    echo ""
    echo "Model info:"
    ollama show "$MODEL_NAME"
else
    echo ""
    echo "❌ Failed to reload model"
    exit 1
fi

echo ""
echo "================================================"
echo "  Model Parameters & Rules"
echo "================================================"
echo "temperature: 0.5 (↓ from 0.7 for better focus)"
echo "top_p: 0.9"
echo "top_k: 40"
echo "num_ctx: 32750"
echo ""
echo "Key Behavior Rules:"
echo "  ✓ Execute tasks directly, don't just describe plans"
echo "  ✓ Continue execution after reading files"
echo "  ✓ Only use propose_options when GENUINELY unclear"
echo "  ✗ NO plain-text questions like 'What next?'"
echo "  ✗ NO asking for next steps after task completion"
echo ""
echo "Run tests with: python3 tests/e2e/test_case_1.py"
