# Quick Start

快速配置开发环境指南。

## 1. 本地：安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .[dev]
```

## 2. 配置远程 Ollama (可选)

如果 Ollama 部署在远程服务器 (ciserver)，需要配置 SSH 隧道。

### 2.1 本地：生成 SSH 密钥

```bash
# 如果没有密钥，生成一个
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

### 2.2 本地：配置 SSH Config

编辑 `~/.ssh/config`，添加：

```
Host ciserver
    HostName 192.168.3.45
    User root
    LocalForward 11434 localhost:11434
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 2.3 本地：复制公钥到远程服务器

```bash
ssh-copy-id root@192.168.3.45
```

### 2.4 远端：确认 Ollama 运行中

```bash
# SSH 登录远端
ssh ciserver

# 检查 Ollama 状态
systemctl status ollama

# 检查模型
ollama list
```

### 2.5 本地：启动隧道

```bash
# 启动后台隧道
ssh -fN ciserver

# 验证隧道（本地访问远端 Ollama）
curl http://localhost:11434/api/tags
```

### 2.6 本地：停止隧道

```bash
pkill -f "ssh.*ciserver"
```

## 3. 本地：验证安装

### 3.1 运行单元测试（不需要 LLM）

```bash
python3 tests/run_unit_tests.py
```

预期输出：
```
✓ test_tools_only.py passed
✓ test_basic.py passed
...
All tests passed!
```

### 3.2 测试 Ollama 连接

```bash
python3 tests/unit/test_ollama_hello.py
```

预期输出：
```
Testing Ollama connection...
✓ Model responded successfully
```

### 3.3 启动交互式 CLI

```bash
# 在当前目录启动
claude-qwen

# 或指定项目目录
claude-qwen --root /path/to/your/project
```

### 3.4 运行 Benchmark 测试

```bash
# 使用默认模型 (glm-4.7-flash)
claude-qwen --test

# 指定模型
claude-qwen --test -m qwen3:latest

# 运行单个用例
python3 tests/benchmark/run_single.py simple_edit
python3 tests/benchmark/run_single.py write_test
```

## 4. 常用命令

| 命令 | 环境 | 说明 |
|------|------|------|
| `claude-qwen` | 本地 | 启动交互式 CLI |
| `python3 tests/run_unit_tests.py` | 本地 | 运行单元测试 |
| `python3 tests/benchmark/run_single.py write_test` | 本地 | 运行单个 benchmark |
| `ssh -fN ciserver` | 本地 | 启动 SSH 隧道 |
| `pkill -f "ssh.*ciserver"` | 本地 | 停止 SSH 隧道 |
| `ollama list` | 远端 | 查看已安装模型 |

---

## 附录 A：通过 Supervisord 启动 Ollama

在服务器上使用 Supervisord 管理 Ollama 进程。

### A.1 安装 Supervisord

```bash
# Ubuntu/Debian
apt install supervisor

# CentOS/RHEL
yum install supervisor
```

### A.2 创建配置文件

创建 `/etc/supervisor/conf.d/ollama.conf`：

```ini
[program:ollama]
command=/usr/local/bin/ollama serve
directory=/root
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ollama.log
environment=OLLAMA_HOST="0.0.0.0:11434",OLLAMA_ORIGINS="*"
```

### A.3 启动服务

```bash
# 重新加载配置
supervisorctl reread
supervisorctl update

# 管理服务
supervisorctl start ollama
supervisorctl status ollama
supervisorctl restart ollama
```

---

## 附录 B：手动安装 GGUF 模型

如果无法通过 `ollama pull` 下载模型，可以手动下载 GGUF 文件并创建模型。

### B.1 下载 GGUF 文件

从国内镜像站下载 GLM-4.7-flash GGUF：

```bash
# 创建模型目录
mkdir -p ~/models/glm-4.7-flash
cd ~/models/glm-4.7-flash

# 从 ModelScope 镜像下载（tar.zst 格式）
wget https://modelscope.cn/models/THUDM/glm-4.7-flash-GGUF/resolve/master/glm-4.7-flash.Q4_K_M.tar.zst

# 安装解压工具
apt install zstd  # 或 brew install zstd (macOS)

# 解压 tar.zst 文件
zstd -d glm-4.7-flash.Q4_K_M.tar.zst
tar -xvf glm-4.7-flash.Q4_K_M.tar

# 解压后得到 gguf 文件
ls -lh *.gguf
```

### B.2 创建 Modelfile

创建 `~/models/glm-4.7-flash/Modelfile`：

```dockerfile
FROM ./glm-4.7-flash.Q4_K_M.gguf

TEMPLATE """{{- if .System }}
<|system|>
{{ .System }}
{{- end }}
<|user|>
{{ .Prompt }}
<|assistant|>
{{ .Response }}"""

PARAMETER stop "<|endoftext|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|observation|>"
PARAMETER num_ctx 32768
PARAMETER temperature 0.7
PARAMETER top_p 0.9
```

### B.3 创建模型

```bash
cd ~/models/glm-4.7-flash
ollama create glm-4.7-flash -f Modelfile
```

### B.4 验证模型

```bash
# 查看模型列表
ollama list

# 测试模型
ollama run glm-4.7-flash "你好"
```

### B.5 配置 claude-qwen 使用该模型

编辑 `config/llm.yaml`：

```yaml
ollama:
  model: "glm-4.7-flash:latest"
  think: true
```
