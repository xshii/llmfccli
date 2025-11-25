# Modelfile 使用指南

## 概述

`claude-qwen:latest` 是基于 `qwen3:latest` 的自定义模型，固化了 system prompt 和参数配置。

## 为什么使用 Modelfile？

### ✅ 优势

1. **配置集中**：System prompt 和参数固化在模型中
2. **节省 tokens**：无需每次请求都传递 system message
3. **团队统一**：所有人使用相同的模型配置
4. **继承能力**：完全继承 qwen3 的 tool calling 能力

### 🎯 设计原则

- **不覆盖 TEMPLATE**：继承 qwen3 的 tool calling template
- **固化配置**：SYSTEM + PARAMETER 在 Modelfile 中
- **简化代码**：代码中不需要传递 system message

## 文件结构

```
llmfccli/
├── Modelfile.claude-qwen      # 自定义模型定义
├── config/ollama.yaml          # 运行时配置（可覆盖）
└── backend/
    ├── llm/prompts.py          # 其他 prompt 模板（保留备用）
    └── agent/loop.py           # 简化后的代码
```

## Modelfile 内容

```dockerfile
FROM qwen3:latest

# 固化 System Prompt（不再需要代码传入）
SYSTEM """
[C++ 编程助手的详细说明]
"""

# 固化参数
PARAMETER temperature 0.7
PARAMETER num_ctx 131072
...

# 不添加 TEMPLATE - 继承 qwen3 的 tool calling template
```

**关键**：没有 `TEMPLATE` 指令 → 自动继承 qwen3 的完整 template（包括 `{{ .Tools }}`）

## 创建自定义模型

### 首次创建

```bash
# 在项目根目录
ollama create claude-qwen:latest -f Modelfile.claude-qwen
```

### 验证创建

```bash
# 查看模型列表
ollama list | grep claude-qwen

# 查看模型配置
ollama show claude-qwen:latest --modelfile
```

输出应该包含：
- `FROM qwen3:latest`
- `SYSTEM "..."`
- `PARAMETER ...`
- **没有** `TEMPLATE` 指令（继承自 qwen3）

## 更新模型

当修改了 `Modelfile.claude-qwen` 后：

```bash
# 重新创建模型（会覆盖旧版本）
ollama create claude-qwen:latest -f Modelfile.claude-qwen

# 或者创建新版本
ollama create claude-qwen:v2 -f Modelfile.claude-qwen
```

## 配置文件

### config/ollama.yaml

```yaml
ollama:
  model: "claude-qwen:latest"  # 使用自定义模型

  # 以下参数已在 Modelfile 中固化
  # 但可以在运行时覆盖
  generation:
    temperature: 0.7      # 默认值
    num_ctx: 131072       # 默认值
```

## 代码简化

### 修改前（动态传 system）

```python
# backend/agent/loop.py
from ..llm.prompts import get_system_prompt

messages = [
    {'role': 'system', 'content': get_system_prompt()},  # 每次都传
    *self.conversation_history
]
```

### 修改后（Modelfile 固化）

```python
# backend/agent/loop.py
# System prompt 已在 Modelfile 中固化
messages = list(self.conversation_history)  # 不需要传 system
```

**简化了**：
- ❌ 删除 `get_system_prompt()` 调用
- ❌ 删除 system message 构建
- ✅ 直接使用对话历史

## Tool Calling 工作流程

```
用户请求
    ↓
构建 messages（只包含对话历史）
    ↓
调用 Ollama API
    ↓
Ollama 自动添加 Modelfile 中的 SYSTEM
    ↓
使用继承的 qwen3 TEMPLATE 处理 tools
    ↓
模型生成 tool_calls
```

## 常见问题

### Q1: 修改 system prompt 需要重新创建模型吗？

**是的**。修改 `Modelfile.claude-qwen` 后需要运行：

```bash
ollama create claude-qwen:latest -f Modelfile.claude-qwen
```

### Q2: 会破坏 tool calling 功能吗？

**不会**。因为我们：
- ✅ 没有添加 `TEMPLATE` 指令
- ✅ 完全继承 qwen3 的 template（包括 `{{ .Tools }}`）
- ✅ Tool calling 功能完整保留

### Q3: 可以临时覆盖参数吗？

**可以**。在代码中传递参数会覆盖 Modelfile 的默认值：

```python
response = client.chat(
    messages=messages,
    tools=tools,
    temperature=0.3  # 临时覆盖 Modelfile 中的 0.7
)
```

### Q4: 为什么不把 prompts.py 删除？

**保留备用**。虽然 system prompt 已在 Modelfile 中，但其他 prompt 模板（如压缩、错误恢复）仍然有用。

### Q5: 团队其他成员怎么使用？

**两种方式**：

**方式 1**：分发 Modelfile
```bash
# 其他成员克隆代码后
ollama create claude-qwen:latest -f Modelfile.claude-qwen
```

**方式 2**：导出模型（推荐）
```bash
# 创建者导出
ollama push your-org/claude-qwen:latest

# 其他成员拉取
ollama pull your-org/claude-qwen:latest
```

## 最佳实践

### 1. 版本控制

```bash
# 开发版
ollama create claude-qwen:dev -f Modelfile.claude-qwen

# 稳定版
ollama create claude-qwen:latest -f Modelfile.claude-qwen

# 实验版
ollama create claude-qwen:experimental -f Modelfile.claude-qwen
```

### 2. 参数调优

在 Modelfile 中固化**稳定**的参数：
```dockerfile
PARAMETER temperature 0.7      # 稳定
PARAMETER num_ctx 131072       # 稳定
```

在代码中传递**实验性**参数：
```python
response = client.chat(..., temperature=0.9)  # 临时测试
```

### 3. System Prompt 维护

```
Modelfile.claude-qwen          # 当前版本
Modelfile.claude-qwen.backup   # 备份
```

修改前先备份：
```bash
cp Modelfile.claude-qwen Modelfile.claude-qwen.backup
```

## 迁移指南

### 从 qwen3:latest 迁移

1. 创建 `Modelfile.claude-qwen`
2. 复制 `backend/llm/prompts.py` 中的 `SYSTEM_PROMPT`
3. 复制 `config/ollama.yaml` 中的参数
4. 创建模型：`ollama create claude-qwen:latest -f Modelfile.claude-qwen`
5. 修改配置：`model: "claude-qwen:latest"`
6. 简化代码：删除 `get_system_prompt()` 调用
7. 测试功能：确保 tool calling 正常

### 回滚到 qwen3:latest

```yaml
# config/ollama.yaml
ollama:
  model: "qwen3:latest"  # 改回官方模型
```

然后恢复代码中的 system message 传递。

## 总结

- ✅ **用 Modelfile**：固化 SYSTEM 和 PARAMETER
- ✅ **不加 TEMPLATE**：继承 qwen3 的 tool calling 能力
- ✅ **简化代码**：无需动态传 system message
- ✅ **团队统一**：所有人使用相同配置
