# Claude-Qwen AI Assistant

AI-powered C/C++ programming assistant for VSCode, powered by local Qwen3 model via Ollama.

## Features

- 🤖 **AI-Powered Code Assistance**: Intelligent code completion, refactoring, and analysis
- 🔧 **Compile Error Fixing**: Automatically detect and fix compilation errors
- ✅ **Test Generation**: Generate unit tests and integration tests
- 📝 **Code Explanation**: Explain selected code in natural language
- 🔒 **Privacy First**: Runs completely locally using Ollama - no data sent to external servers
- ⚡ **Fast**: Direct integration with VSCode for minimal latency

## Requirements

- VSCode 1.80.0 or higher
- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Qwen3 model pulled: `ollama pull qwen3`
- Claude-Qwen CLI installed: `pip install -e .` (from project root)

## Installation

### From VSIX

1. Download the latest `.vsix` file from releases
2. In VSCode, run: `Extensions: Install from VSIX...`
3. Select the downloaded `.vsix` file

### From Source

```bash
# Navigate to extension directory
cd vscode-extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package as VSIX
npm run package

# Install the generated .vsix file
code --install-extension claude-qwen-0.1.0.vsix
```

## Configuration

Open VSCode settings and configure:

- `claude-qwen.pythonPath`: Path to Python interpreter (default: `python3`)
- `claude-qwen.cliPath`: Path to claude-qwen CLI (default: `claude-qwen`)
- `claude-qwen.communicationMode`: Communication mode (`ipc` or `socket`, default: `socket`)
- `claude-qwen.socketPath`: Socket path or address (see platform-specific notes below)
- `claude-qwen.autoStart`: Auto-start CLI when opening C/C++ files (default: `false`)
- `claude-qwen.logLevel`: Log level for extension (default: `info`)

### Platform-Specific Configuration

#### Windows

**Important:** Windows users must use TCP socket mode.

Add to `.vscode/settings.json`:

```json
{
  "claude-qwen.communicationMode": "socket",
  "claude-qwen.socketPath": "tcp://localhost:11435"
}
```

Supported formats:
- `tcp://localhost:11435` - Full format
- `localhost:11435` - Simplified format
- `11435` - Port only (defaults to localhost)

#### Linux/macOS

Unix socket is the default and recommended:

```json
{
  "claude-qwen.communicationMode": "socket",
  "claude-qwen.socketPath": "/tmp/claude-qwen.sock"
}
```

Alternatively, you can use TCP socket on Linux/macOS as well.

## Usage

### Commands

Access commands via Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

- **Start Claude-Qwen Assistant** - Start the AI assistant
- **Stop Claude-Qwen Assistant** - Stop the AI assistant
- **Test VSCode Integration** - Test extension integration
- **Fix Compile Errors** - Automatically fix compilation errors
- **Generate Unit Tests** - Generate tests for current file
- **Explain Selected Code** - Explain selected code (also: `Ctrl+Shift+E`)

### Keyboard Shortcuts

- `Ctrl+Shift+E` (`Cmd+Shift+E` on Mac) - Explain selected code
- `Ctrl+Shift+T` (`Cmd+Shift+T` on Mac) - Generate tests

### Context Menu

Right-click in C/C++ files to access:
- Explain Selected Code
- Generate Unit Tests

## How It Works

1. **Extension** starts a Claude-Qwen CLI process as a subprocess
2. **CLI** runs the Qwen3 model via Ollama for AI inference
3. **JSON-RPC** protocol handles bidirectional communication:
   - VSCode → CLI: User commands and requests
   - CLI → VSCode: File operations, diff display, etc.

```
┌─────────────┐  JSON-RPC   ┌──────────┐  API  ┌─────────┐
│   VSCode    │◄───────────►│   CLI    │◄─────►│ Ollama  │
│  Extension  │ stdin/stdout│  Python  │       │  Qwen3  │
└─────────────┘             └──────────┘       └─────────┘
```

## Development

### Setup

```bash
cd vscode-extension
npm install
npm run compile
```

### Watch Mode

```bash
npm run watch
```

### Testing

Press `F5` in VSCode to launch Extension Development Host.

### Packaging

```bash
# Create .vsix package
npm run package

# Publish to marketplace (requires publisher account)
npm run publish
```

## Troubleshooting

### CLI fails to start

- Check Python path in settings
- Verify claude-qwen is installed: `pip list | grep claude-qwen`
- Check Output panel: `View → Output → Claude-Qwen`

### Ollama connection errors

- Verify Ollama is running: `ollama list`
- Check model is pulled: `ollama pull qwen3`
- For remote Ollama, ensure SSH tunnel is active

### Extension not responding

- Check Output panel for errors
- Restart extension: `Developer: Reload Window`
- Check CLI logs in Output panel

## Architecture

See [VSCODE_INTEGRATION.md](../docs/VSCODE_INTEGRATION.md) for detailed architecture documentation.

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.

## Support

- GitHub Issues: https://github.com/xshii/llmfccli/issues
- Documentation: [docs/](../docs/)
