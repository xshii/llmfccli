# Change Log

All notable changes to the Claude-Qwen extension will be documented in this file.

## [0.1.0] - 2024-11-26

### Added
- Initial release
- VSCode extension with JSON-RPC communication
- CLI process management
- Core commands:
  - Start/Stop assistant
  - Fix compile errors
  - Generate unit tests
  - Explain code
  - Test integration
- Keyboard shortcuts for common operations
- Context menu integration for C/C++ files
- Configuration options for Python path, CLI path, auto-start, etc.
- Output channel for debugging
- Comprehensive README and documentation

### Features
- IPC communication via stdin/stdout
- Real-time bidirectional communication with CLI
- Support for all 6 VSCode integration methods:
  - getActiveFile
  - getSelection
  - showDiff
  - applyChanges
  - openFile
  - getWorkspaceFolder

### Technical
- TypeScript implementation
- ESLint configuration
- VSCode API 1.80.0 compatibility
- VSIX packaging support
