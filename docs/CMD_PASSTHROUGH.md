# 命令透传功能

Claude-Qwen 提供了两个命令透传功能，允许您直接从 CLI 执行本地或远程终端命令。

## 功能概述

### `/cmd` - 本地命令透传
在本地机器上执行终端命令，结果直接显示在 CLI 中。

### `/cmdremote` - 远程命令透传
通过 SSH 在远程服务器上执行命令（需要配置 SSH）。

## 使用方法

### 基本用法

```bash
# 本地命令
/cmd <command>

# 远程命令
/cmdremote <command>
```

### 示例

#### 本地命令示例

```bash
# 查看当前目录
/cmd pwd

# 列出文件
/cmd ls -la

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

### 1. 支持管道和重定向

命令支持所有 bash 功能，包括：
- 管道：`/cmd ls | grep .py`
- 重定向：`/cmd echo "test" > /tmp/test.txt`
- 多命令：`/cmd cd /tmp && ls -la`

### 2. 实时输出

命令输出会实时显示在 CLI 中，包括：
- 标准输出 (stdout)
- 标准错误 (stderr)

### 3. 错误处理

- 命令执行失败会显示错误信息
- 返回码非 0 时会标记为失败
- 超时设置为 60 秒

### 4. 自动回退

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

### 1. 项目管理

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

1. **超时限制**：默认 60 秒超时
2. **交互命令**：不支持需要交互输入的命令（如 vim、nano）
3. **环境变量**：远程命令使用登录 shell，但可能与交互式 shell 不同
4. **输出大小**：非常大的输出可能导致显示问题

## 未来增强

计划中的功能：
- [ ] 可配置超时时间
- [ ] 命令历史记录
- [ ] 命令别名支持
- [ ] 并行执行多个命令
- [ ] 命令输出保存到文件
- [ ] 交互式命令支持

## 相关文档

- [远程 Ollama 配置](../CLAUDE.md#远程-Ollama-配置)
- [工具系统](../docs/EDIT_FILE_USAGE.md)
- [配置架构](../docs/CONFIG_ARCHITECTURE.md)
