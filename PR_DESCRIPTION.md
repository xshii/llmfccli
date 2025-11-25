# Add remotectl module with config-driven model management

This PR introduces a complete remote Ollama management system with centralized configuration for model definitions and automated sync. All configurations follow the **Single Source of Truth** principle to eliminate duplication.

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

### 3. Modelfile Organization & Configuration Unification

- Moved Modelfile to `config/modelfiles/claude-qwen.modelfile`
- **Eliminated config duplication**: All model parameters (temperature, top_p, stop tokens, etc.) defined ONLY in Modelfile
- Abstracted tool definitions to categories (not specific tools)
- Inherits qwen3:latest template to preserve tool calling capability

**Single Source of Truth Design:**
- ✅ Model parameters → Modelfile PARAMETER
- ✅ Stop tokens → Modelfile PARAMETER stop
- ✅ System prompt → Modelfile SYSTEM
- ✅ Runtime config → ollama.yaml (base_url, timeout, etc.)
- ❌ No duplication between files

### 4. Automated Workflow

```bash
# One-command setup: pulls base models + syncs custom models
python backend/remotectl/sync_models.py
```

## 🏗️ Architecture Highlights

### Design Principles

1. **Single Source of Truth**: Each config item defined in exactly one place
2. **Template Inheritance**: No TEMPLATE override → preserves qwen3's tool calling
3. **Abstract Tool Categories**: Modelfile describes capabilities, not specific tools
4. **Dual Mode Support**: Works with both SSH remote and local Ollama
5. **Standalone Script**: Simple batch operations without CLI complexity
6. **Centralized Config**: All model definitions in one YAML file

### Configuration Hierarchy

```
Modelfile (固化配置)
├─ SYSTEM prompt
├─ PARAMETER temperature, top_p, etc.
└─ PARAMETER stop tokens
    ↓
ollama.yaml (运行时配置)
├─ base_url, timeout
├─ model selection
└─ SSH config
    ↓
Code kwargs (临时覆盖)
└─ Optional runtime overrides
```

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
- `docs/CONFIG_ARCHITECTURE.md` - Complete config architecture guide
- `tests/unit/test_confirmation.py` - Tool confirmation system tests

### Modified Files
- `config/ollama.yaml` - Added model_management, removed duplicate generation params
- `backend/agent/loop.py` - Removed dynamic system prompt injection
- `backend/llm/client.py` - Support optional generation params, removed hardcoded stop tokens
- `tests/run_unit_tests.py` - Added test_confirmation.py

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

# 2. Sync all models (auto-pulls base models + creates custom models)
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

### Configuration Management
- ✅ **Single Source of Truth**: Each parameter defined in exactly one place
- ✅ **No Duplication**: Eliminated repeated configs between Modelfile and ollama.yaml
- ✅ **Clear Separation**: Modelfile=固化配置, YAML=运行时配置
- ✅ **Version Control Friendly**: All model definitions tracked in Git

### Stop Tokens
- ✅ **Unified Definition**: Stop tokens only in Modelfile
- ✅ **Correct Tokens**: Fixed incorrect `<|im_start|>`, added complete set
- ✅ **Clear Documentation**: Explained API stop vs client detection

### Model Management
- ✅ **Multi-Model Support**: Easy to add/manage multiple custom models
- ✅ **Automated Pulling**: Base models auto-pulled if configured
- ✅ **Organized Storage**: Modelfiles in dedicated directory
- ✅ **No Hardcoding**: All paths resolved from config

## 🔧 Configuration Details

### Before: Duplication Issues

**Problem 1: Generation Parameters**
```yaml
# ollama.yaml (duplicated)
generation:
  temperature: 0.7
  top_p: 0.9
  ...

# Modelfile (duplicated)
PARAMETER temperature 0.7
PARAMETER top_p 0.9
```

**Problem 2: Stop Tokens**
```python
# client.py (hardcoded)
'stop': ['<|endoftext|>', '<|im_end|>', 'Human:', '\nHuman:']

# Modelfile (incomplete & incorrect)
PARAMETER stop "<|im_start|>"  # Wrong: this is a start marker!
PARAMETER stop "<|im_end|>"
```

### After: Single Source of Truth

**Solution 1: Parameters Only in Modelfile**
```dockerfile
# Modelfile (single definition)
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 131072
...

# ollama.yaml (removed generation section)
# Uses Modelfile parameters by default
```

**Solution 2: Stop Tokens Only in Modelfile**
```dockerfile
# Modelfile (complete & correct)
PARAMETER stop "<|im_end|>"       # Qwen3 message end
PARAMETER stop "<|endoftext|>"    # Generic text end
PARAMETER stop "Human:"           # Prevent user responses
PARAMETER stop "\nHuman:"         # Prevent user responses (with newline)

# client.py (no hardcoded stop parameter)
# Uses Modelfile stop tokens automatically
```

## 🧪 Testing

```bash
# Test configuration loading
python3 -c "from backend.llm.client import OllamaClient; c = OllamaClient(); print(f'Params: {c.generation_params}')"
# Output: Params: {}  # Empty dict means using Modelfile params

# Test sync script
python backend/remotectl/sync_models.py

# Test CLI commands
python -m backend.remotectl.cli list
python -m backend.remotectl.cli health

# Run unit tests (including new test_confirmation.py)
python tests/run_unit_tests.py
```

## 📚 Documentation

- Complete module documentation in `backend/remotectl/README.md`
- Modelfile explanation in `docs/MODELFILE.md`
- **Configuration architecture guide** in `docs/CONFIG_ARCHITECTURE.md`
  - Single source of truth principle
  - Stop tokens configuration
  - Parameter override mechanism
  - Migration guide

## 📊 Statistics

- **Total Lines Added**: ~1,750
- **New Files**: 10
- **Modified Files**: 4
- **New Module**: `backend/remotectl/` (5 files, ~1000 lines)
- **Documentation**: 3 comprehensive docs

## 🔄 Commits Summary

1. `feat: Add remotectl module with config-driven model management` - Core module implementation
2. `docs: Add PR description file` - PR documentation
3. `test: Move test_confirmation.py to tests/unit/` - Test organization
4. `refactor: Eliminate config duplication between Modelfile and ollama.yaml` - Remove generation params duplication
5. `refactor: Unify stop tokens in Modelfile, eliminate duplication` - Single source for stop tokens

## 🎓 Design Documentation

See `docs/CONFIG_ARCHITECTURE.md` for complete explanation of:
- Configuration layering (Modelfile vs YAML vs Code)
- Stop tokens: API parameter vs client detection
- Parameter override mechanism
- Migration guide from duplicated configs
- Real-world usage scenarios

---

**Key Takeaway**: All configurations now follow **Single Source of Truth** principle - no duplication, clear separation of concerns, version control friendly, and easy to maintain.
