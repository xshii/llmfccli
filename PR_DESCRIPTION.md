# Add remotectl module with config-driven model management

This PR introduces a complete remote Ollama management system with centralized configuration for model definitions and automated sync.

## 🎯 Features

### 1. Remote Ollama Management Module (`backend/remotectl/`)

- **RemoteOllamaClient**: SSH-based remote command execution with automatic local fallback
- **ModelManager**: High-level API for model lifecycle management
- **CLI**: Command-line interface for individual model operations
- **sync_models.py**: Standalone script for batch model synchronization

### 2. Config-Driven Model Management

New `model_management` section in `config/ollama.yaml`:

```yaml
model_management:
  # Custom model definitions
  models:
    - name: "claude-qwen:latest"
      base_model: "qwen3:latest"
      modelfile: "modelfiles/claude-qwen.modelfile"
      description: "C++ 编程助手"
      enabled: true

  # Base model download configuration
  base_models:
    - registry_name: "qwen3:latest"
      local_name: "qwen3:latest"
      auto_pull: true

  default_model: "claude-qwen:latest"
```

### 3. Modelfile Organization

- Moved Modelfile to `config/modelfiles/claude-qwen.modelfile`
- Abstracted tool definitions to categories (not specific tools)
- Inherits qwen3:latest template to preserve tool calling capability

### 4. Automated Workflow

```bash
# One-command setup: pulls base models + syncs custom models
python backend/remotectl/sync_models.py
```

## 🏗️ Architecture Highlights

### Design Decisions

1. **Template Inheritance**: No TEMPLATE override → preserves qwen3's tool calling
2. **Abstract Tool Categories**: Modelfile describes capabilities, not specific tools
3. **Dual Mode Support**: Works with both SSH remote and local Ollama
4. **Standalone Script**: Simple batch operations without CLI complexity
5. **Centralized Config**: All model definitions in one YAML file

### Workflow Separation

- **Script** (`sync_models.py`): Batch operations, initial setup
- **CLI** (`remotectl.cli`): Individual model management

## 📁 Files Changed

### New Files
- `backend/remotectl/__init__.py` - Package initialization
- `backend/remotectl/client.py` (330 lines) - SSH remote client
- `backend/remotectl/model_manager.py` (300 lines) - Model manager
- `backend/remotectl/cli.py` (280 lines) - CLI interface
- `backend/remotectl/sync_models.py` (80 lines) - Sync script
- `backend/remotectl/README.md` (320 lines) - Documentation
- `config/modelfiles/claude-qwen.modelfile` - Moved from root
- `docs/MODELFILE.md` - Modelfile documentation

### Modified Files
- `config/ollama.yaml` - Added model_management section
- `backend/agent/loop.py` - Removed dynamic system prompt injection

## 🚀 Usage

### First-time Setup

```bash
# 1. Configure SSH (if using remote Ollama)
cat >> ~/.ssh/config << 'EOF'
Host ollama-tunnel
    HostName 192.168.3.41
    User gakki
    LocalForward 11434 localhost:11434
EOF

# 2. Sync all models
python backend/remotectl/sync_models.py
```

### Daily Operations

```bash
# List models
python -m backend.remotectl.cli list

# Update models after Modelfile changes
python backend/remotectl/sync_models.py

# Individual model operations
python -m backend.remotectl.cli create
python -m backend.remotectl.cli show claude-qwen:latest
```

## ✅ Benefits

- ✅ **Centralized Configuration**: All model definitions in one place
- ✅ **Multi-Model Support**: Easy to add/manage multiple custom models
- ✅ **Automated Pulling**: Base models auto-pulled if configured
- ✅ **Organized Storage**: Modelfiles in dedicated directory
- ✅ **No Hardcoding**: All paths resolved from config
- ✅ **Clear Separation**: Script for batch, CLI for individual ops

## 🧪 Testing

```bash
# Test sync script (will fail without Ollama, but shows workflow)
python backend/remotectl/sync_models.py

# Test CLI commands
python -m backend.remotectl.cli list
python -m backend.remotectl.cli health
```

## 📚 Documentation

- Complete module documentation in `backend/remotectl/README.md`
- Modelfile explanation in `docs/MODELFILE.md`
- Configuration examples in updated `config/ollama.yaml`

## 📊 Statistics

- **Total Lines Added**: ~1,547
- **New Files**: 8
- **Modified Files**: 2
- **New Module**: `backend/remotectl/` (5 files, ~1000 lines)
