# Tab 键补全功能

Claude-Qwen CLI 支持智能 tab 键补全，可以帮助您快速输入命令和参数。

## 功能概述

按 **Tab** 键可以：
- 自动补全斜杠命令（如 `/help`, `/cmd`, `/model`）
- 补全命令的子命令和参数
- 提供命令说明提示
- 补全常用 shell 命令
- 补全文件路径（用于 `/root` 命令）
- **补全项目中的文件名**（支持模糊搜索）

## 使用方法

### 1. 补全斜杠命令

输入 `/` 然后按 **Tab** 键，会列出所有可用命令：

```
> /[Tab]
/help          - Display help message
/clear         - Clear conversation history
/compact       - Manually trigger context compression
/usage         - Show token usage
/model         - Manage Ollama models
/cmd           - Execute local terminal command
/cmdremote     - Execute remote terminal command (SSH)
...
```

### 2. 部分匹配补全

输入命令的前几个字母，按 **Tab** 键补全：

```
> /h[Tab]
> /help        # 自动补全为 /help

> /m[Tab]
> /model       # 自动补全为 /model
```

### 3. 子命令补全

对于支持子命令的命令（如 `/model`），可以继续补全：

```
> /model [Tab]
list    - List all Ollama models
create  - Create claude-qwen model
show    - Show model details
delete  - Delete a model
pull    - Pull a model from registry
health  - Check Ollama server health

> /model l[Tab]
> /model list   # 自动补全为 list
```

### 4. Shell 命令补全

对于 `/cmd` 和 `/cmdremote`，会提示常用 shell 命令：

```
> /cmd [Tab]
ls       - Shell command
cd       - Shell command
pwd      - Shell command
git      - Shell command
docker   - Shell command
ollama   - Shell command
...

> /cmd l[Tab]
ls       - Shell command
less     - Shell command

> /cmdremote o[Tab]
> /cmdremote ollama   # 自动补全为 ollama
```

### 5. 文件路径补全

对于 `/root` 命令，支持目录路径补全：

```
> /root /home/[Tab]
/home/user/         - Directory
/home/guest/        - Directory

> /root ~/[Tab]
~/Documents/        - Directory
~/Downloads/        - Directory
~/projects/         - Directory
```

### 6. 文件名补全（新功能）

在自然语言输入中，可以自动补全项目中的文件名：

```
> 请修改 net[Tab]
backend/remotectl/client.py           - File (.py)
src/network_handler.cpp               - File (.cpp)
src/network_handler.h                 - File (.h)
tests/test_network.cpp                - File (.cpp)

> 请修改 src/net[Tab]
src/network_handler.cpp               - File (.cpp)
src/network_handler.h                 - File (.h)

> 查看 README[Tab]
README.md                             - File (.md)
docs/README.md                        - File (.md)
```

**特性**：
- 智能模糊匹配（输入部分文件名即可）
- 优先显示常用文件类型（.cpp, .h, .py, .md 等）
- 按匹配度排序（路径匹配 > 文件名匹配 > 内容包含）
- 自动缓存文件列表（60 秒），提高性能
- 自动跳过无关目录（.git, node_modules, __pycache__ 等）
- 最多显示 30 个结果

## 支持的命令

### 主命令补全

所有斜杠命令都支持补全：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/clear` | 清除对话历史 |
| `/compact` | 手动压缩上下文 |
| `/usage` | 显示 Token 使用情况 |
| `/root` | 查看或设置项目根目录 |
| `/reset-confirmations` | 重置工具执行确认 |
| `/exit`, `/quit` | 退出程序 |
| `/model` | 管理 Ollama 模型 |
| `/cmd` | 执行本地终端命令 |
| `/cmdremote` | 执行远程终端命令 |
| `/expand` | 展开最后一个折叠的输出 |
| `/collapse` | 折叠最后一个展开的输出 |
| `/toggle` | 切换最后一个输出状态 |
| `/vscode` | 在 VSCode 中打开项目 |
| `/testvs` | 测试 VSCode 集成 |

### /model 子命令补全

| 子命令 | 说明 |
|--------|------|
| `list` | 列出所有模型 |
| `create` | 创建 claude-qwen 模型 |
| `show` | 显示模型详情 |
| `delete` | 删除模型 |
| `pull` | 拉取模型 |
| `health` | 检查服务器健康状态 |

### Shell 命令建议

对于 `/cmd` 和 `/cmdremote`，提供常用命令建议：

**文件操作**: `ls`, `cd`, `pwd`, `cat`, `grep`, `find`, `tree`, `mkdir`, `rm`, `cp`, `mv`, `touch`

**进程管理**: `ps`, `top`, `htop`, `kill`

**系统信息**: `df`, `du`, `netstat`, `ping`, `which`

**开发工具**: `git`, `docker`, `npm`, `pip`, `python`, `vim`, `nano`

**远程管理**: `systemctl`, `nvidia-smi`, `ollama`

**网络工具**: `curl`, `wget`, `ssh`, `scp`

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Tab` | 触发补全 |
| `↑` | 上一条历史命令 |
| `↓` | 下一条历史命令 |
| `Ctrl+C` | 取消当前输入 |
| `Ctrl+D` | 退出 CLI |

## 技术实现

Tab 补全功能使用 `prompt_toolkit` 库实现：

### ClaudeQwenCompleter
- 主命令补全器
- 识别斜杠命令
- 提供子命令建议
- Shell 命令建议

### PathCompleter
- 文件路径补全
- 支持 `~` 扩展
- 仅显示目录（用于 `/root`）
- 最多显示 50 个结果

### FileNameCompleter（新）
- 项目文件名补全
- 智能模糊匹配算法
- 文件列表缓存（60 秒）
- 按匹配度评分排序
- 跳过 .git, node_modules 等目录
- 限制扫描深度（最多 5 层）
- 优先显示源代码文件
- 最多显示 30 个结果

### CombinedCompleter
- 组合多个补全器
- 按优先级提供补全建议

## 配置选项

补全行为在 `backend/cli.py` 中配置：

```python
self.session = PromptSession(
    history=FileHistory(str(history_file)),
    auto_suggest=AutoSuggestFromHistory(),
    completer=combined_completer,
    complete_while_typing=False,  # 仅在按 Tab 时补全
)
```

### 可选配置

- `complete_while_typing=True`: 输入时自动显示补全建议（可能会影响性能）
- `complete_while_typing=False`: 仅在按 Tab 时显示补全（默认，推荐）

## 示例会话

```bash
$ claude-qwen

> /[Tab]
# 显示所有命令

> /m[Tab]
> /model [Tab]
# 显示 model 子命令

> /model li[Tab]
> /model list
# 自动补全并执行

> /cmd l[Tab]
ls       - Shell command
less     - Shell command

> /cmd ls[Enter]
# 执行 ls 命令

> /cmdremote o[Tab]
> /cmdremote ollama list[Enter]
# 在远程服务器列出模型
```

## 性能优化

补全器针对性能进行了优化：

1. **延迟加载**: 仅在需要时生成补全列表
2. **结果限制**: 路径补全最多显示 50 个结果
3. **简单匹配**: 使用高效的字符串前缀匹配
4. **无网络调用**: 所有补全都是本地的，不需要网络请求

## 故障排除

### 问题 1: Tab 补全不工作

**可能原因**:
- `prompt_toolkit` 未安装

**解决方案**:
```bash
pip install prompt-toolkit
```

### 问题 2: 补全列表太长

**解决方案**:
- 输入更多字符缩小范围
- 路径补全已限制为 50 个结果

### 问题 3: 没有看到补全建议

**检查**:
- 确保输入了 `/` 开头
- 按 Tab 键触发补全
- 检查是否有匹配的命令

## 扩展补全功能

如需添加新的补全支持，修改 `backend/cli_completer.py`：

```python
# 添加新命令
self.commands = {
    '/mycommand': 'My custom command description',
    # ...
}

# 添加子命令
self.mycommand_subcommands = {
    'subcommand1': 'Description',
    'subcommand2': 'Description',
}

# 在 get_completions() 中处理
if main_cmd == '/mycommand' and len(words) <= 2:
    partial = words[1] if len(words) == 2 else ''
    for subcmd, desc in self.mycommand_subcommands.items():
        if subcmd.startswith(partial):
            yield Completion(...)
```

## 相关文档

- [命令透传功能](CMD_PASSTHROUGH.md)
- [CLI 使用指南](../README.md)
- [prompt_toolkit 文档](https://python-prompt-toolkit.readthedocs.io/)
