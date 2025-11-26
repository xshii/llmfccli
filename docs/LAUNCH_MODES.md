# Claude-Qwen 启动模式

Claude-Qwen 支持多种启动方式，可以根据你的工作环境选择最合适的模式。

## 启动方式总览

| 方式 | 命令 | 适用场景 |
|------|------|----------|
| **智能启动** | `./scripts/launch.sh` | 自动检测环境，推荐 |
| **VSCode 模式** | `./scripts/launch-vscode.sh` | 使用 VSCode UI 和图形界面 |
| **CLI 模式** | `claude-qwen` 或 `python3 -m backend.cli` | 纯命令行操作 |
| **从 CLI 打开 VSCode** | 在 CLI 中输入 `/vscode` | 已在 CLI 中，想切换到 VSCode |
| **从 VSCode 启动** | `Ctrl+Shift+P` → "Claude-Qwen: Start" | 已在 VSCode 中 |

## 详细说明

### 1. 智能启动 (推荐)

自动检测当前环境，选择最佳启动方式。

```bash
./scripts/launch.sh [project-path]
```

**行为：**
- 如果在 VSCode 终端中：自动启动 CLI 的 VSCode 集成模式
- 如果 VSCode 可用：提示选择 VSCode 或 CLI 模式
- 如果没有 VSCode：使用纯 CLI 模式

**示例：**
```bash
# 在当前目录启动
./scripts/launch.sh

# 在指定目录启动
./scripts/launch.sh /path/to/cpp/project
```

### 2. VSCode 集成模式

在 VSCode 中打开项目，使用图形界面操作。

```bash
./scripts/launch-vscode.sh [project-path]
```

**功能：**
- 检查 VSCode 是否安装
- 检查 Claude-Qwen extension 是否安装
- 自动打开 VSCode
- 提供安装扩展的选项

**启动后操作：**
1. 按 `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`)
2. 输入 "Claude-Qwen: Start"
3. 开始使用 AI 助手

**可用命令：**
- 修复编译错误：`Ctrl+Shift+P` → "Fix Compile Errors"
- 生成测试：`Ctrl+Shift+T`
- 解释代码：选中代码后按 `Ctrl+Shift+E`

### 3. 纯 CLI 模式

适合远程 SSH、服务器环境、或喜欢命令行的用户。

```bash
# 方式 1: 使用安装的命令
claude-qwen --root /path/to/project

# 方式 2: 直接运行 Python 模块
python3 -m backend.cli --root /path/to/project

# 方式 3: 使用别名
alias cq='python3 -m backend.cli'
cq --root /path/to/project
```

**可用命令：**
```bash
# 在 CLI 中输入：
/help              # 查看帮助
/vscode            # 打开 VSCode (如果可用)
/testvs            # 测试 VSCode 集成
/model list        # 列出模型
编译项目并修复错误  # 直接输入自然语言任务
```

### 4. 从 CLI 切换到 VSCode

如果你已经在 CLI 中，可以随时打开 VSCode：

```bash
# 在 CLI 提示符下输入
> /vscode
```

**效果：**
- 自动检测 VSCode 是否安装
- 检查 Claude-Qwen extension 是否安装
- 打开当前项目在 VSCode 中
- 提供启动扩展的提示

### 5. 从 VSCode 启动 CLI

在 VSCode 中使用命令面板启动：

```
Ctrl+Shift+P → "Claude-Qwen: Start"
```

这会：
1. 启动 CLI 进程作为后台服务
2. 建立 JSON-RPC 通信
3. 启用所有 VSCode 集成功能

## 环境变量

### VSCODE_INTEGRATION

CLI 通过此环境变量检测是否运行在 VSCode 集成模式：

```bash
# VSCode extension 启动 CLI 时会设置
export VSCODE_INTEGRATION=true
python3 -m backend.cli
```

**效果：**
- 启用 JSON-RPC 通信
- VSCode 工具函数使用实际 API 而非 mock
- 输出格式针对 VSCode 优化

### 手动设置 (用于测试)

```bash
# 模拟 VSCode 环境
export VSCODE_INTEGRATION=true
export VSCODE_PID=12345
python3 -m backend.cli
```

## 工作流示例

### 场景 1：新项目开发

```bash
# 1. Clone 项目
git clone https://github.com/your/cpp-project
cd cpp-project

# 2. 智能启动
/path/to/llmfccli/scripts/launch.sh .

# 3. 根据提示选择 VSCode 或 CLI
```

### 场景 2：远程服务器

```bash
# SSH 到服务器
ssh user@server

# 使用纯 CLI 模式 (没有 GUI)
cd /path/to/project
claude-qwen

# 使用 AI 助手
> 编译项目并修复所有错误
> 为 network_handler.cpp 生成单元测试
```

### 场景 3：本地开发 (VSCode)

```bash
# 1. 打开 VSCode
code /path/to/project

# 2. 启动扩展
Ctrl+Shift+P → "Claude-Qwen: Start"

# 3. 使用快捷键
Ctrl+Shift+T  # 生成测试
Ctrl+Shift+E  # 解释选中代码
```

### 场景 4：CLI 与 VSCode 切换

```bash
# 在 CLI 中工作
> 编译项目并修复错误
✓ 修复完成

# 需要查看 diff，切换到 VSCode
> /vscode
✓ VSCode 已打开

# 在 VSCode 中：
Ctrl+Shift+P → "Claude-Qwen: Start"
# 现在可以使用图形化的 diff 工具
```

## 配置

### VSCode Extension 配置

在 VSCode 设置 (`settings.json`) 中：

```json
{
  "claude-qwen.pythonPath": "python3",
  "claude-qwen.autoStart": true,
  "claude-qwen.logLevel": "info"
}
```

### CLI 配置

配置文件位于：
- `config/ollama.yaml` - Ollama 连接配置
- `config/token_budget.yaml` - Token 预算配置
- `config/tools.yaml` - 工具白名单配置

## 故障排除

### VSCode 无法启动 CLI

**症状：**
```
Failed to start Claude-Qwen CLI
```

**解决：**
1. 检查 Python 路径：
   ```bash
   which python3
   # 更新 VSCode 设置中的 pythonPath
   ```

2. 检查 CLI 是否安装：
   ```bash
   python3 -m backend.cli --help
   ```

3. 查看输出日志：
   ```
   View → Output → 选择 "Claude-Qwen"
   ```

### CLI 无法连接 Ollama

**症状：**
```
❌ Ollama 连接测试 - FAILED
```

**解决：**
1. 检查 Ollama 服务：
   ```bash
   ollama list
   ```

2. 检查模型：
   ```bash
   ollama pull qwen3
   ```

3. 远程 Ollama - 启动隧道：
   ```bash
   ssh -fN ollama-tunnel
   ```

### /vscode 命令无效

**症状：**
```
错误: 未找到 'code' 命令
```

**解决：**
1. 安装 code 命令：
   - 打开 VSCode
   - 按 `Ctrl+Shift+P`
   - 输入 "Shell Command: Install 'code' command in PATH"
   - 回车

2. 验证安装：
   ```bash
   which code
   code --version
   ```

## 最佳实践

1. **开发环境**：使用 VSCode 模式，享受图形化界面
2. **CI/CD**：使用纯 CLI 模式，易于自动化
3. **远程工作**：使用 CLI 模式，通过 SSH 使用
4. **快速任务**：使用 CLI 模式，启动快速
5. **复杂调试**：使用 VSCode 模式，方便查看 diff

## 参考

- [VSCode Extension 文档](../vscode-extension/README.md)
- [CLI 使用指南](../CLAUDE.md)
- [VSCode 集成架构](./VSCODE_INTEGRATION.md)
