# 命令透传功能

Claude-Qwen 提供了命令透传功能，允许您直接从 CLI 执行本地或远程终端命令。

## 功能概述

### `/cmd` - 本地命令透传（持久化会话）
在本地机器上执行终端命令，使用**持久化 shell 会话**，保留工作目录和环境变量状态。

**核心特性**：
- ✅ **工作目录持久化**：`cd` 命令的效果会保留到下次 `/cmd` 调用
- ✅ **环境变量持久化**：`export` 设置的变量会在会话中保留
- ✅ **Shell 状态保留**：别名、函数定义等都会保持
- ✅ **实时输出**：命令输出立即显示

### `/cmdpwd` - 查看当前目录
显示持久化 shell 的当前工作目录。

### `/cmdclear` - 重置会话
将持久化 shell 会话重置到初始状态（项目根目录）。

### `/cmdremote` - 远程命令透传
通过 SSH 在远程服务器上执行命令（需要配置 SSH）。

## 使用方法

### 基本用法

```bash
# 本地命令（持久化会话）
/cmd <command>

# 查看当前目录
/cmdpwd

# 重置会话
/cmdclear

# 远程命令
/cmdremote <command>
```

### 持久化会话示例

#### 工作目录持久化

```bash
# 查看初始目录
/cmd pwd
# 输出：/home/user/llmfccli

# 切换到子目录
/cmd cd backend
# ✓ 命令执行成功

# 再次查看目录 - 仍在 backend 目录！
/cmd pwd
# 输出：/home/user/llmfccli/backend

# 或使用快捷命令
/cmdpwd
# 输出：当前工作目录: /home/user/llmfccli/backend

# 列出当前目录文件（在 backend 目录下）
/cmd ls -la
# 显示 backend 目录的内容

# 重置到初始目录
/cmdclear
# ✓ Shell 会话已重置到初始目录: /home/user/llmfccli

/cmdpwd
# 输出：当前工作目录: /home/user/llmfccli
```

#### 环境变量持久化

```bash
# 设置环境变量
/cmd export MY_VAR="hello world"

# 在后续命令中使用
/cmd echo $MY_VAR
# 输出：hello world

# 变量在整个会话中保持
/cmd cd /tmp
/cmd echo $MY_VAR
# 仍然输出：hello world
```

#### 本地命令示例

```bash
# 查看磁盘使用情况
/cmd df -h

# 使用管道
/cmd ps aux | grep python

# 查看 Git 状态
/cmd git status

# 查看系统信息
/cmd uname -a
```

#### 远程命令示例

```bash
# 列出远程 Ollama 模型
/cmdremote ollama list

# 查看远程 GPU 状态
/cmdremote nvidia-smi

# 查看远程进程
/cmdremote ps aux | grep ollama

# 检查远程服务状态
/cmdremote systemctl status ollama

# 查看远程磁盘使用
/cmdremote df -h

# 查看远程 Docker 容器
/cmdremote docker ps
```

## 配置

### 远程命令配置

远程命令需要在 `config/ollama.yaml` 中配置 SSH：

```yaml
ssh:
  enabled: true               # 启用 SSH 远程管理
  host: "ciserver"            # SSH 配置名称（~/.ssh/config 中定义）
  # user: "username"          # 可选：SSH 用户名（如果不在 config 中）
```

### SSH 配置文件

在 `~/.ssh/config` 中添加配置：

```
Host ciserver
    HostName your-server.com
    User your-username
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

或者使用 SSH 隧道配置：

```
Host ollama-tunnel
    HostName ciserver
    User root
    LocalForward 11434 localhost:11434
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

## 功能特性

### 1. 持久化会话（核心特性）

`/cmd` 使用持久化 shell 进程，**不同于传统的独立命令执行**：

#### 传统方式（其他工具）
```bash
/cmd cd backend    # 切换目录
/cmd pwd           # 输出：/home/user/llmfccli（回到原目录！）
```

#### Claude-Qwen 持久化会话
```bash
/cmd cd backend    # 切换目录
/cmd pwd           # 输出：/home/user/llmfccli/backend（保留状态！）
```

**技术实现**：
- 启动一个持久化的 bash 进程
- 所有 `/cmd` 命令都发送到同一个进程
- 进程在 CLI 整个生命周期中保持运行
- 自动处理命令完成检测和输出收集

### 2. 支持管道和重定向

命令支持所有 bash 功能，包括：
- 管道：`/cmd ls | grep .py`
- 重定向：`/cmd echo "test" > /tmp/test.txt`
- 多命令：`/cmd command1 && command2`

### 3. 实时输出

命令输出会实时显示在 CLI 中，包括：
- 标准输出 (stdout)
- 标准错误 (stderr)
- 颜色标记（成功=绿色，错误=红色）

### 4. 错误处理

- 命令执行失败会显示错误信息
- 返回码非 0 时会标记为失败
- 超时设置为 30 秒
- Shell 进程意外终止会自动重启

### 5. 会话管理

- `/cmdpwd`：快速查看当前目录
- `/cmdclear`：重置会话到初始状态
- 会话在 CLI 退出时自动清理

### 6. 自动回退

如果 SSH 未配置或不可用，`/cmdremote` 会自动回退到本地执行，并显示警告。

## 安全注意事项

### ⚠️ 命令执行风险

1. **本地命令**：
   - 可以执行任何本地 shell 命令
   - 具有当前用户的所有权限
   - 请谨慎使用删除、修改等危险命令

2. **远程命令**：
   - 通过 SSH 在远程服务器执行
   - 具有 SSH 用户的所有权限
   - 建议使用受限权限的 SSH 用户

### 🔒 最佳实践

1. **避免危险命令**：
   ```bash
   # ❌ 危险 - 不要执行
   /cmd rm -rf /
   /cmdremote shutdown -h now
   ```

2. **先验证后执行**：
   ```bash
   # ✓ 先查看
   /cmd ls /tmp/to-delete
   # 确认后再删除
   /cmd rm -rf /tmp/to-delete
   ```

3. **使用只读命令**：
   ```bash
   # ✓ 安全 - 只读操作
   /cmd ls -la
   /cmd cat /etc/hosts
   /cmdremote ollama list
   /cmdremote nvidia-smi
   ```

## 常见用例

### 1. 多步骤项目操作（利用持久化会话）

```bash
# 切换到源码目录
/cmd cd backend

# 查看当前位置
/cmdpwd
# 输出：/home/user/llmfccli/backend

# 在源码目录运行测试
/cmd python -m pytest tests/ -v

# 查看测试覆盖率（仍在 backend 目录）
/cmd coverage report

# 回到项目根目录
/cmd cd ..
/cmdpwd
# 输出：/home/user/llmfccli
```

### 2. 环境配置工作流

```bash
# 设置环境变量
/cmd export PYTHONPATH=/home/user/llmfccli
/cmd export DEBUG=1

# 使用环境变量运行程序
/cmd python -c "import os; print(os.getenv('DEBUG'))"
# 输出：1

# 环境变量在整个会话中保持
/cmd cd tests
/cmd echo $PYTHONPATH
# 输出：/home/user/llmfccli
```

### 3. 构建和测试流程

```bash
# 切换到构建目录
/cmd cd build

# 配置 CMake
/cmd cmake ..

# 编译（在 build 目录下）
/cmd make -j4

# 运行测试（仍在 build 目录）
/cmd ctest -V

# 如果需要重新开始
/cmdclear
/cmdpwd
# 输出：回到项目根目录
```

### 4. Git 工作流

```bash
# 查看项目结构
/cmd tree -L 2

# Git 操作
/cmd git log --oneline -10
/cmd git diff HEAD~1

# 查看依赖
/cmd pip list | grep ollama
```

### 2. 系统监控

```bash
# CPU 和内存
/cmd top -bn1 | head -20

# 网络连接
/cmd netstat -tuln

# 进程监控
/cmd ps aux | grep python
```

### 3. 远程 Ollama 管理

```bash
# 列出模型
/cmdremote ollama list

# 查看模型详情
/cmdremote ollama show qwen3:latest

# 删除模型
/cmdremote ollama rm old-model:latest

# 检查服务状态
/cmdremote systemctl status ollama
```

### 4. 开发调试

```bash
# 运行测试
/cmd pytest tests/unit -v

# 代码检查
/cmd ruff check backend/

# 构建项目
/cmd python setup.py build
```

## 故障排除

### 问题 1: 命令未找到

```
Error: command not found
```

**解决方案**：
- 确保命令在 PATH 中
- 使用绝对路径：`/cmd /usr/bin/python3 --version`

### 问题 2: SSH 连接失败

```
Error: SSH command not found
```

**解决方案**：
- 安装 SSH 客户端：`apt-get install openssh-client`
- 检查 SSH 配置：`ssh -T ciserver`

### 问题 3: 权限拒绝

```
Error: Permission denied
```

**解决方案**：
- 检查文件/目录权限
- 使用 sudo（如果适当）：`/cmd sudo systemctl restart ollama`

### 问题 4: 超时

```
SSH command timeout after 60s
```

**解决方案**：
- 检查网络连接
- 检查远程服务器负载
- 对于长时间运行的命令，考虑使用后台任务

## 与其他功能的集成

### 与 Agent 结合使用

虽然 `/cmd` 和 `/cmdremote` 是独立命令，但您也可以让 Agent 使用工具系统执行命令：

```
# 直接命令
/cmd ls -la

# 通过 Agent（会使用 bash_run 工具）
请列出当前目录的文件
```

### 与模型管理结合

```bash
# 查看模型
/model list

# 使用远程命令检查详情
/cmdremote ollama show claude-qwen:latest

# 拉取模型
/model pull qwen3:latest
```

## 限制

### 本地命令（持久化会话）

1. **超时限制**：默认 30 秒超时
2. **交互命令**：不支持需要交互输入的命令（如 vim、nano、top）
3. **后台进程**：不支持后台任务（`&`），命令必须前台完成
4. **输出大小**：非常大的输出可能导致显示问题
5. **会话隔离**：每个 CLI 实例有独立的 shell 会话

### 远程命令

1. **环境变量**：远程命令使用登录 shell，但可能与交互式 shell 不同
2. **持久化**：`/cmdremote` 不支持持久化会话（每次都是独立命令）
3. **SSH 配置**：需要正确配置 SSH 密钥认证

## 未来增强

计划中的功能：
- [x] ✅ 持久化会话支持（已实现）
- [x] ✅ 工作目录保持（已实现）
- [x] ✅ 环境变量保持（已实现）
- [ ] 可配置超时时间
- [ ] 命令历史记录和回溯
- [ ] 命令别名支持
- [ ] 多会话管理（命名会话）
- [ ] 远程命令持久化会话
- [ ] 命令输出保存到文件
- [ ] 交互式命令支持（通过 pty）

## 相关文档

- [远程 Ollama 配置](../CLAUDE.md#远程-Ollama-配置)
- [工具系统](../docs/EDIT_FILE_USAGE.md)
- [配置架构](../docs/CONFIG_ARCHITECTURE.md)
