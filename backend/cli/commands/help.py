# -*- coding: utf-8 -*-
"""
Help 命令 - 动态生成版
"""

from typing import List, TYPE_CHECKING
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .base import Command

if TYPE_CHECKING:
    from ..command_registry import CommandRegistry


class HelpCommand(Command):
    """显示帮助信息（动态生成）"""

    def __init__(self, console: Console, command_registry: 'CommandRegistry' = None):
        """
        初始化 Help 命令

        Args:
            console: Rich Console 实例
            command_registry: 命令注册器（用于动态生成帮助）
        """
        super().__init__(console)
        self.command_registry = command_registry

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "显示帮助信息"

    @property
    def category(self) -> str:
        return "agent"

    @property
    def usage(self) -> str:
        return "/help"

    def execute(self, args: List[str]) -> bool:
        """显示帮助消息（动态生成）"""
        # 基础部分
        help_text = """
## 可用命令

💡 **提示**: 按 **Tab** 键可自动补全所有命令和参数

"""

        # 如果有 command_registry，动态生成命令列表
        if self.command_registry:
            commands_by_category = self.command_registry.get_commands_by_category()

            # 定义类别顺序和中文名称
            category_order = [
                ('agent', 'Agent 控制'),
                ('vscode', 'VSCode 集成'),
                ('model', '模型管理'),
                ('shell', '命令透传'),
                ('other', '其他'),
            ]

            for category_key, category_name in category_order:
                if category_key not in commands_by_category:
                    continue

                commands = commands_by_category[category_key]
                if not commands:
                    continue

                help_text += f"### {category_name}\n"

                for cmd_meta in sorted(commands, key=lambda x: x.name):
                    # 构建命令行
                    help_text += f"- `{cmd_meta.usage}` - {cmd_meta.description}\n"

                help_text += "\n"

        # 添加内置命令（不在 registry 中）
        help_text += """### 内置命令
- `/clear` - 清除对话历史（保留文件访问权限）
- `/root [path]` - 查看或设置项目根目录
- `/exit` 或 `/quit` - 退出程序
- `/cache` - 查看文件补全缓存信息
- `/cmd <command>` - 在本地执行终端命令（持久化 shell 会话）
- `/cmdpwd` - 查看持久化 shell 的当前工作目录
- `/cmdclear` - 重置持久化 shell 会话到初始状态
- `/cmdremote <command>` - 在远程服务器执行终端命令（通过 SSH）

"""

        # 示例用法（保持静态）
        help_text += """## 示例用法

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
