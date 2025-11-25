# Remote Control Module for Ollama

远程 Ollama 管理工具集，用于管理远端 Ollama 服务器。

## 功能特性

- ✅ 远程模型管理（列表、创建、删除）
- ✅ 模型同步（从 Modelfile 创建自定义模型）
- ✅ 服务器健康检查
- ✅ 模型拉取（从 Ollama Registry）
- ✅ SSH 和本地模式支持

## 配置

### SSH 配置（推荐）

在 `~/.ssh/config` 中配置：

```bash
Host ollama-tunnel
    HostName 192.168.3.41
    User gakki
    LocalForward 11434 localhost:11434
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

在 `config/ollama.yaml` 中启用：

```yaml
ssh:
  enabled: true
  host: "ollama-tunnel"
  user: "gakki"  # 可选，如果在 .ssh/config 中已定义
```

### 本地模式

如果 Ollama 运行在本地，设置：

```yaml
ssh:
  enabled: false
```

### 模型管理配置

在 `config/ollama.yaml` 中配置模型定义和基础模型：

```yaml
model_management:
  # 自定义模型定义列表
  models:
    - name: "claude-qwen:latest"          # 创建后的模型名
      base_model: "qwen3:latest"          # 基础模型（用于 FROM 指令）
      modelfile: "modelfiles/claude-qwen.modelfile"  # Modelfile 相对路径（相对于 config/）
      description: "C++ 编程助手，基于 Qwen3"
      enabled: true                       # 是否启用此模型配置

  # 基础模型下载配置
  base_models:
    - registry_name: "qwen3:latest"       # Ollama registry 中的名称
      local_name: "qwen3:latest"          # 本地存储名称
      auto_pull: true                     # 启动时自动拉取（如果不存在）

  # 默认使用的模型
  default_model: "claude-qwen:latest"
```

Modelfile 文件存放在 `config/modelfiles/` 目录下。

## 使用方式

### 模型同步脚本（推荐）

```bash
# 同步所有模型（基础模型 + 自定义模型）
python backend/remotectl/sync_models.py
```

这个独立脚本会按顺序执行：
1. 检查并拉取配置中的基础模型（如果启用 auto_pull）
2. 同步所有启用的自定义模型
3. 显示详细的执行结果

### CLI 命令

```bash
# 列出所有模型
python -m backend.remotectl.cli list

# 创建 claude-qwen 自定义模型
python -m backend.remotectl.cli create

# 确保模型存在（不存在则创建）
python -m backend.remotectl.cli ensure

# 查看模型详情
python -m backend.remotectl.cli show claude-qwen:latest

# 检查服务器健康状态
python -m backend.remotectl.cli health

# 拉取模型
python -m backend.remotectl.cli pull qwen3:latest

# 删除模型
python -m backend.remotectl.cli delete old-model:latest
python -m backend.remotectl.cli delete old-model:latest -y  # 跳过确认
```

### Python API

```python
from backend.remotectl import RemoteOllamaClient, ModelManager

# 基础客户端
client = RemoteOllamaClient()

# 列出模型
success, models = client.list_models()
for model in models:
    print(model['name'])

# 检查健康状态
health = client.check_health()
if health['healthy']:
    print("Ollama server is healthy")

# 模型管理
manager = ModelManager()

# 同步 claude-qwen 模型
manager.sync_claude_qwen_model()

# 同步所有启用的模型（从配置）
results = manager.sync_all_models()
for model_name, success in results.items():
    print(f"{model_name}: {'✓' if success else '✗'}")

# 确保基础模型存在
base_results = manager.ensure_base_models()

# 确保模型存在
manager.ensure_model_exists("claude-qwen:latest")

# 查看模型信息
info = manager.show_model_info("claude-qwen:latest")
print(info['modelfile'])
```

## 典型工作流

### 首次设置

```bash
# 1. 配置 SSH（如果使用远程服务器）
cat >> ~/.ssh/config << 'EOF'
Host ollama-tunnel
    HostName 192.168.3.41
    User gakki
    LocalForward 11434 localhost:11434
EOF

# 2. 复制 SSH 密钥
ssh-copy-id gakki@192.168.3.41

# 3. 测试连接
ssh ollama-tunnel "ollama list"

# 4. 检查健康状态
python -m backend.remotectl.cli health

# 5. 同步所有模型（基础模型 + 自定义模型）
python backend/remotectl/sync_models.py
```

### 日常使用

```bash
# 查看可用模型
python -m backend.remotectl.cli list

# 更新模型（修改 Modelfile 后）
python backend/remotectl/sync_models.py  # 同步所有模型

# 或只更新单个模型
python -m backend.remotectl.cli create  # 只创建 claude-qwen

# 启动前确保模型存在
python -m backend.remotectl.cli ensure
```

### 集成到 CLI 启动

在 `backend/cli.py` 中添加：

```python
from .remotectl import ModelManager

class CLI:
    def __init__(self, ...):
        # 确保自定义模型存在
        if not skip_precheck:
            self._ensure_custom_model()

    def _ensure_custom_model(self):
        """Ensure claude-qwen model exists"""
        manager = ModelManager()
        manager.ensure_model_exists("claude-qwen:latest")
```

## 模块结构

```
backend/remotectl/
├── __init__.py           # 包初始化
├── client.py             # SSH 远程客户端
├── model_manager.py      # 模型管理器
├── cli.py                # 命令行工具
├── sync_models.py        # 模型同步脚本
└── README.md             # 本文档
```

## API 参考

### RemoteOllamaClient

```python
class RemoteOllamaClient:
    def __init__(config_path: Optional[str] = None)
    def list_models() -> Tuple[bool, list]
    def show_model(model_name: str) -> Tuple[bool, str]
    def create_model(model_name: str, modelfile_content: str) -> Tuple[bool, str]
    def delete_model(model_name: str) -> Tuple[bool, str]
    def pull_model(model_name: str) -> Tuple[bool, str]
    def check_health() -> Dict[str, Any]
```

### ModelManager

```python
class ModelManager:
    def __init__(client: Optional[RemoteOllamaClient] = None)
    def sync_claude_qwen_model() -> bool
    def sync_all_models() -> Dict[str, bool]
    def ensure_base_models() -> Dict[str, bool]
    def ensure_model_exists(model_name: str = "claude-qwen:latest") -> bool
    def list_models() -> Dict[str, Any]
    def show_model_info(model_name: str) -> Dict[str, Any]
    def delete_model(model_name: str, confirm: bool = False) -> bool
```

## 故障排除

### SSH 连接失败

```bash
# 检查 SSH 配置
ssh ollama-tunnel "echo 'SSH works'"

# 检查隧道
ssh -fN ollama-tunnel
curl http://localhost:11434/api/tags
```

### 模型创建失败

```bash
# 检查 Modelfile 是否存在
ls -la Modelfile.claude-qwen

# 检查 Modelfile 语法
cat Modelfile.claude-qwen

# 手动创建测试
ssh ollama-tunnel "ollama create test:latest -f - << 'EOF'
FROM qwen3:latest
SYSTEM \"Test model\"
EOF"
```

### 权限问题

```bash
# 确保远程用户有权限
ssh ollama-tunnel "which ollama"
ssh ollama-tunnel "ollama list"
```

## 最佳实践

1. **版本管理**：创建模型时使用标签区分版本
   ```bash
   python -m backend.remotectl.cli create  # claude-qwen:latest
   ```

2. **定期同步**：修改 Modelfile 后及时同步
   ```bash
   git pull
   python -m backend.remotectl.cli create
   ```

3. **健康检查**：启动前检查服务器状态
   ```bash
   python -m backend.remotectl.cli health
   ```

4. **清理旧模型**：定期删除不用的模型
   ```bash
   python -m backend.remotectl.cli delete old-model:v1 -y
   ```

## 未来扩展

- [ ] 模型版本管理
- [ ] 批量操作
- [ ] 模型导出/导入
- [ ] 资源监控（CPU、GPU、内存）
- [ ] 自动故障恢复
