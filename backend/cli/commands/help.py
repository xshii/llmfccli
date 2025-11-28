# -*- coding: utf-8 -*-
"""
Help 命令
"""

from typing import List
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .base import Command


class HelpCommand(Command):
    """显示帮助信息"""

    def __init__(self, console: Console):
        super().__init__(console)

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "显示帮助信息"

    def execute(self, args: List[str]) -> bool:
        """显示帮助消息"""
        help_text = """
## 可用命令

💡 **提示**: 按 **Tab** 键可自动补全所有命令和参数

### Agent 控制
- `/help` - 显示此帮助信息
- `/clear` - 清除对话历史（保留文件访问权限）
- `/compact [ratio|--info]` - 智能压缩上下文
  - `/compact` - 使用默认目标(60%)压缩
  - `/compact 0.5` - 压缩到 50% tokens
  - `/compact --info` - 查看压缩策略而不执行
- `/root [path]` - 查看或设置项目根目录
- `/exit` 或 `/quit` - 退出程序

### VSCode 集成
- `/vscode` - 在 VSCode 中打开当前项目
- `/testvs` - 测试 VSCode extension 集成（Mock 模式）

### 模型管理
- `/model list` - 列出所有 Ollama 模型
- `/model create` - 创建 claude-qwen 模型
- `/model show <name>` - 显示模型详情
- `/model delete <name>` - 删除模型
- `/model pull <name>` - 拉取模型
- `/model health` - 检查 Ollama 服务器状态

### 命令透传（持久化会话）
- `/cmd <command>` - 在本地执行终端命令（持久化 shell 会话，保留工作目录和环境变量）
- `/cmdpwd` - 查看持久化 shell 的当前工作目录
- `/cmdclear` - 重置持久化 shell 会话到初始状态
- `/cmdremote <command>` - 在远程服务器执行终端命令（通过 SSH）

## 示例用法

**文件操作**:
```
找到 network_handler.cpp 并添加超时重试机制
```

**编译修复**:
```
编译项目并修复所有错误
```

**测试生成**:
```
为当前文件生成单元测试
分析 HTTP 模块并生成集成测试
```

**代码分析**:
```
分析项目结构
查找所有网络相关的函数
```

**上下文管理**:
```
/compact --info           # 查看压缩策略
/compact                  # 使用默认策略压缩
/compact 0.5              # 压缩到 50%
```

**命令透传（持久化会话）**:
```
/cmd ls -la                    # 查看本地目录
/cmd cd backend                # 切换目录（状态会保留）
/cmd pwd                       # 仍在 backend 目录下
/cmdpwd                        # 查看当前目录
/cmdclear                      # 重置 shell 会话
/cmd ps aux | grep ollama      # 查看本地进程
/cmdremote ollama list         # 在远程服务器列出模型
/cmdremote nvidia-smi          # 查看远程 GPU 状态
```
"""
        self.console.print(Panel(Markdown(help_text), title="帮助"))
        return True
