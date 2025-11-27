# Tab 补全演示

本文档展示 Claude-Qwen CLI 的 tab 补全功能。

## 快速演示

### 1. 命令发现

当您不确定有哪些命令时，输入 `/` 并按 **Tab**：

```
> /[Tab]

显示所有 14 个可用命令：
  /help                   - Display help message
  /clear                  - Clear conversation history
  /compact                - Manually trigger context compression
  /root                   - View or set project root directory
  /exit                   - Exit the program
  /quit                   - Exit the program
  /model                  - Manage Ollama models
  /cmd                    - Execute local terminal command
  /cmdremote              - Execute remote terminal command (SSH)
  /expand                 - Expand last collapsed tool output
  /collapse               - Collapse last expanded tool output
  /toggle                 - Toggle last tool output state
  /vscode                 - Open current project in VSCode
  /testvs                 - Test VSCode extension integration
```

### 2. 快速输入命令

输入前几个字母，按 **Tab** 自动补全：

```
> /h[Tab]
> /help                   # 自动补全

> /com[Tab]
> /compact                # 自动补全
```

### 3. 子命令补全

探索 `/model` 的子命令：

```
> /model [Tab]

显示所有子命令：
  list    - List all Ollama models
  create  - Create claude-qwen model
  show    - Show model details
  delete  - Delete a model
  pull    - Pull a model from registry
  health  - Check Ollama server health

> /model l[Tab]
> /model list             # 自动补全
```

### 4. Shell 命令建议

获取常用 shell 命令建议：

```
> /cmd [Tab]

显示常用命令：
  ls       - Shell command
  cd       - Shell command
  pwd      - Shell command
  cat      - Shell command
  grep     - Shell command
  find     - Shell command
  ps       - Shell command
  git      - Shell command
  docker   - Shell command
  ollama   - Shell command
  ...

> /cmd l[Tab]

显示以 'l' 开头的命令：
  ls       - Shell command
  less     - Shell command

> /cmd ls[Enter]
# 执行 ls 命令
```

### 5. 远程命令补全

对于远程命令，同样提供建议：

```
> /cmdremote [Tab]

显示常用远程命令：
  ollama      - Shell command
  nvidia-smi  - Shell command
  systemctl   - Shell command
  docker      - Shell command
  ...

> /cmdremote o[Tab]
> /cmdremote ollama[Space]

继续输入：
> /cmdremote ollama list[Enter]
# 在远程服务器执行 ollama list
```

### 6. 路径补全

设置项目根目录时补全路径：

```
> /root /home/[Tab]

显示 /home 下的目录：
  /home/user/     - Directory
  /home/guest/    - Directory

> /root ~/[Tab]

显示用户主目录下的目录：
  ~/Documents/    - Directory
  ~/Downloads/    - Directory
  ~/projects/     - Directory
  ~/Desktop/      - Directory

> /root ~/projects/[Tab]

显示 projects 下的目录：
  ~/projects/claude-qwen/     - Directory
  ~/projects/my-app/          - Directory
  ~/projects/tests/           - Directory
```

## 实际使用场景

### 场景 1: 管理 Ollama 模型

```bash
# 列出模型
> /m[Tab]
> /model [Tab]
> /model list[Enter]

# 拉取新模型
> /model p[Tab]
> /model pull qwen3:latest[Enter]

# 查看模型详情
> /model sh[Tab]
> /model show qwen3:latest[Enter]

# 检查健康状态
> /model h[Tab]
> /model health[Enter]
```

### 场景 2: 执行系统命令

```bash
# 查看进程
> /cmd [Tab]
> /cmd ps aux | grep python[Enter]

# 检查磁盘
> /cmd d[Tab]
> /cmd df -h[Enter]

# Git 操作
> /cmd g[Tab]
> /cmd git status[Enter]

# 远程检查 GPU
> /cmdremote n[Tab]
> /cmdremote nvidia-smi[Enter]
```

### 场景 3: 项目导航

```bash
# 设置项目根目录
> /root [Tab]
> /root ~/projects/[Tab]
> /root ~/projects/my-app/[Enter]

# 查看当前根目录
> /root[Enter]
当前项目根目录: /home/user/projects/my-app
```

## 高级技巧

### 1. 组合使用历史和补全

```bash
# 按上箭头调出历史命令
> ↑
/model list

# 修改命令并使用补全
> /model [Backspace][Backspace][Backspace][Backspace]sh[Tab]
> /model show qwen3:latest
```

### 2. 快速探索功能

```bash
# 不知道有什么命令？按 Tab 浏览
> /[Tab]

# 想看有哪些模型操作？
> /model [Tab]

# 想知道有什么 shell 命令建议？
> /cmd [Tab]
```

### 3. 减少输入错误

```bash
# 不确定子命令名称？
> /model cr[Tab]
> /model create           # 避免错误输入
```

## 性能提示

1. **部分输入**: 输入更多字符可以更快找到目标命令
   ```
   /h[Tab]        vs    /he[Tab]
   3 个结果              1 个结果
   ```

2. **路径限制**: 路径补全最多显示 50 个结果，避免过载

3. **本地补全**: 所有补全都是本地的，不需要网络，速度很快

## 键盘快捷键总结

| 按键 | 功能 |
|------|------|
| **Tab** | 触发补全/选择下一个建议 |
| **Shift+Tab** | 选择上一个建议 |
| **↑** | 上一条历史命令 |
| **↓** | 下一条历史命令 |
| **Ctrl+A** | 移动到行首 |
| **Ctrl+E** | 移动到行尾 |
| **Ctrl+K** | 删除光标到行尾 |
| **Ctrl+U** | 删除整行 |
| **Ctrl+C** | 取消当前输入 |
| **Ctrl+D** | 退出 CLI |

## 常见问题

### Q: 为什么我按 Tab 没有反应？

**A**: 确保：
1. 已输入 `/` 开头
2. `prompt_toolkit` 已安装
3. 在补全上下文中（如命令或路径）

### Q: 补全列表太长怎么办？

**A**: 输入更多字符缩小范围：
```
/[Tab]           # 16 个命令
/c[Tab]          # 5 个命令
/co[Tab]         # 2 个命令
/com[Tab]        # 1 个命令 (/compact)
```

### Q: 如何补全自定义路径？

**A**: 目前仅 `/root` 命令支持路径补全。其他场景可以手动输入完整路径。

## 反馈和改进

如果您有补全功能的改进建议，欢迎：
1. 提交 Issue: https://github.com/xshii/llmfccli/issues
2. 提交 PR 添加新的补全支持
3. 在讨论区分享使用技巧

---

**提示**: 习惯使用 Tab 补全可以显著提高 CLI 使用效率！
