# 交互式 CLI 使用指南

## 🎯 三种运行模式

现在 remotectl 支持三种运行方式：

### 1️⃣ 命令行模式（适合脚本和自动化）
```bash
python -m backend.remotectl.cli list
python -m backend.remotectl.cli health
```

### 2️⃣ 独立脚本模式（方便快捷）
```bash
python backend/remotectl/cli_standalone.py list
./backend/remotectl/cli_standalone.py health
```

### 3️⃣ 交互式模式（新增，适合探索和调试）✨
```bash
python -m backend.remotectl.cli_interactive
# 或
python backend/remotectl/cli_interactive.py
```

## 🖥️ 交互式模式特性

### 启动界面
```
╔════════════════════════════════════════════════════════════════╗
║           Ollama Remote Control - Interactive Mode            ║
╚════════════════════════════════════════════════════════════════╝

Type 'help' or '?' to list commands.
Type 'exit' or 'quit' to exit.

(ollama)
```

### 可用命令

#### 📦 模型管理
- `list` - 列出所有模型
- `create` - 创建 claude-qwen 模型
- `ensure [model]` - 确保模型存在
- `show <model>` - 查看模型详情
- `delete <model> [-y]` - 删除模型
- `pull <model>` - 拉取模型
- `sync` - 运行模型同步脚本

#### 🔧 服务器
- `health` - 检查服务器健康状态

#### 💡 实用工具
- `clear` - 清屏
- `help [command]` - 查看帮助
- `exit` / `quit` - 退出

### 特性亮点

✅ **自动补全**
- TAB 键自动补全命令
- 模型名称自动补全（show, delete, ensure）

✅ **交互式体验**
- 无需重复输入 `python -m ...`
- 停留在同一个会话中
- 更快的操作流程

✅ **丰富的帮助系统**
- `help` - 显示所有命令
- `help <command>` - 显示特定命令帮助

✅ **友好的输出**
- Rich 格式化输出
- 彩色表格和面板
- Markdown 格式帮助

## 📝 使用示例

### 示例 1：检查和创建模型

```bash
$ python backend/remotectl/cli_interactive.py

(ollama) health
╭──────────────────────────── Ollama Server Health ────────────────────────────╮
│                                                                              │
│ **Status**: Healthy                                                          │
│                                                                              │
│ **Details**:                                                                 │
│ - Process Running: ✓                                                         │
│ - API Accessible: ✓                                                          │
│ - Models Available: 3                                                        │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

(ollama) list
           Ollama Models (3 total)
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Model Name         ┃ Details            ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ qwen3:latest       │ ...                │
│ claude-qwen:latest │ ...                │
│ llama3:8b          │ ...                │
└────────────────────┴────────────────────┘

(ollama) show claude-qwen:latest
╭───────────────── Model: claude-qwen:latest ─────────────────╮
│ FROM qwen3:latest                                           │
│                                                             │
│ SYSTEM """你是一个专业的 C/C++ 编程助手..."""               │
│                                                             │
│ PARAMETER temperature 0.7                                   │
│ PARAMETER top_p 0.9                                         │
│ ...                                                         │
╰─────────────────────────────────────────────────────────────╯

(ollama) exit

Goodbye! 👋
```

### 示例 2：模型同步流程

```bash
(ollama) health
[检查服务器状态...]

(ollama) sync
Running sync_models.py...
This will sync all enabled models from config
[同步进度...]
✓ Sync completed successfully

(ollama) list
[查看同步后的模型列表...]

(ollama) quit
```

### 示例 3：使用自动补全

```bash
(ollama) show cl[TAB]
(ollama) show claude-qwen:latest

(ollama) delete test[TAB]
(ollama) delete test-model:latest
```

## 🆚 模式对比

| 特性 | 命令行模式 | 独立脚本 | 交互式模式 |
|------|-----------|---------|-----------|
| 执行速度 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ (启动一次) |
| 适合自动化 | ✅ | ✅ | ❌ |
| 适合探索 | ❌ | ❌ | ✅ |
| 自动补全 | ❌ | ❌ | ✅ |
| 停留会话 | ❌ | ❌ | ✅ |
| 学习曲线 | 低 | 低 | 中 |

## 💡 推荐使用场景

### 使用命令行模式
- CI/CD 管道
- Shell 脚本
- 一次性命令
- 快速检查

### 使用独立脚本
- 开发调试
- 快速执行
- 不想记 `-m` 参数

### 使用交互式模式 ✨
- 探索可用功能
- 调试问题
- 学习命令
- 连续操作多个模型
- 不想重复输入命令

## 🔧 高级特性

### Ctrl+D 快速退出
```bash
(ollama) [Ctrl+D]
Goodbye! 👋
```

### 清屏保持整洁
```bash
(ollama) clear
[屏幕清空]
```

### 命令历史
- 上下箭头键浏览历史命令
- 自动保存命令历史

### 错误处理
```bash
(ollama) unknown_command
Unknown command: unknown_command
Type 'help' to see available commands

(ollama) show
Error: Model name required
Usage: show <model_name>
```

## 🔧 代码复用 - InteractiveShellBase

### 设计理念

为了避免代码重复，`cli_interactive.py` 使用了 `backend/interactive_base.py` 中的可复用基类。

### 基类特性

`InteractiveShellBase` 提供：

✅ **通用命令**
- `clear` - 清屏
- `exit` / `quit` - 退出
- `help` - 帮助系统
- Ctrl+D 支持

✅ **Rich 格式化辅助方法**
- `print_success(message)` - 成功消息（绿色 ✓）
- `print_error(message)` - 错误消息（红色 ✗）
- `print_warning(message)` - 警告消息（黄色 ⚠）
- `print_info(message)` - 信息消息（青色 ℹ）
- `print_table(title, columns, rows)` - 表格输出
- `print_panel(content, title, style)` - 面板输出
- `print_markdown(text)` - Markdown 格式化

✅ **实用工具**
- `parse_args(arg)` - 参数解析
- `confirm(prompt, default)` - 用户确认
- `console` - Rich Console 实例

### 使用示例

```python
from backend.interactive_base import InteractiveShellBase

class MyShell(InteractiveShellBase):
    intro = "Welcome to My Shell"
    prompt = '(myshell) '

    def __init__(self):
        super().__init__()
        # 初始化你的组件

    def do_mycommand(self, arg):
        """我的自定义命令"""
        self.print_info("正在执行命令...")
        # 使用 self.console 访问 Rich Console
        # 使用辅助方法：self.print_success(), self.print_error() 等

    def do_help(self, arg):
        """覆盖帮助系统"""
        if arg:
            super().do_help(arg)
        else:
            help_text = """
## 我的命令列表
...
"""
            self.print_markdown(help_text)

# 使用
shell = MyShell()
shell.cmdloop()
```

### 在主 CLI 中使用

`backend/cli.py`（主 Agent CLI）也可以使用这个基类的辅助方法：

```python
from backend.interactive_base import InteractiveShellBase

class AgentCLI(InteractiveShellBase):
    # 可以保留现有的 prompt_toolkit 集成
    # 同时使用基类的 Rich 格式化方法

    def run_agent(self):
        self.print_info("启动 Agent...")
        # 使用 self.print_success(), self.print_error() 等
```

### 优势

1. **避免重复** - 通用功能只写一次
2. **一致体验** - 所有交互式 CLI 使用相同的格式和风格
3. **易于维护** - 修改基类即可影响所有子类
4. **灵活扩展** - 子类可以覆盖或扩展任何功能

## 📚 扩展阅读

- 基础用法：`backend/remotectl/README.md`
- 配置说明：`docs/CONFIG_ARCHITECTURE.md`
- API 参考：查看 `README.md` 中的 API 章节
- 基类实现：`backend/interactive_base.py`

## 🚀 快速开始

```bash
# 1. 启动交互式 CLI
python backend/remotectl/cli_interactive.py

# 2. 检查服务器
(ollama) health

# 3. 列出模型
(ollama) list

# 4. 查看帮助
(ollama) help

# 5. 退出
(ollama) exit
```

---

**提示**：第一次使用时，建议先运行 `help` 命令熟悉所有可用功能！
