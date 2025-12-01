# 模型参数调优指南

## 问题现象

如果模型在执行任务时表现出以下行为：
- 读取文件后询问"您希望对这个文件做什么？"（尽管任务已经很明确）
- 过度使用 `propose_options` 工具
- 在任务明确的情况下仍然要求用户输入

这通常是由以下原因导致的：

## 原因分析

### 1. `propose_options` 工具描述过于宽泛

**原始描述：**
```
"(3) Context file is provided but no specific task is requested."
```

这导致模型误认为"只要读取了文件而没有立即行动，就需要询问用户"。

**修复后：**
```
"ONLY USE when user intent is GENUINELY UNCLEAR."
"DO NOT USE if user has specified a clear task."
"If you've read a file and user task is clear, CONTINUE execution - don't ask."
```

### 2. temperature 参数过高

- **过高 (0.7-1.0)**: 模型更"有创造性"，倾向于探索性询问
- **适中 (0.5-0.6)**: 平衡创造性和专注度 ✅
- **过低 (0.1-0.3)**: 模型过于保守，可能缺乏变通能力

**修改：**
```diff
- PARAMETER temperature 0.7
+ PARAMETER temperature 0.5
```

### 3. System Prompt 缺少明确指导

增加了以下原则：
```
2. **用户任务通常是明确的** - 读取文件后继续执行任务，不要询问"希望做什么"
3. **仅在真正不明确时询问** - 只有当用户完全没提供任务或任务极其模糊时才使用 propose_options
```

## 应用修复

### 步骤 1：重新加载模型

修改 Modelfile 后需要重新创建模型：

```bash
# 方法 1：使用脚本（推荐）
bash scripts/reload_model.sh

# 方法 2：手动创建
ollama create claude-qwen:latest -f config/modelfiles/claude-qwen.modelfile
```

### 步骤 2：验证参数

检查模型参数是否生效：

```bash
ollama show claude-qwen:latest
```

应该看到：
```
Parameters:
  temperature: 0.5
  top_p: 0.9
  top_k: 40
  ...
```

### 步骤 3：测试行为

运行测试用例验证：

```bash
# 测试用例 1: 文件定位与功能添加
python3 tests/e2e/test_case_1.py

# 期望：模型应该直接执行任务，不再询问用户
```

## 参数调优建议

### Temperature 参数调整

| 场景 | 推荐值 | 说明 |
|-----|-------|------|
| 代码修改任务 | 0.3-0.5 | 需要精确执行，减少随机性 |
| 测试生成 | 0.5-0.7 | 需要一定创造性，覆盖边界情况 |
| 代码解释 | 0.6-0.8 | 允许更灵活的表达方式 |
| Bug 修复 | 0.3-0.5 | 需要精确定位和修复 |

### 其他参数说明

```yaml
PARAMETER top_p 0.9           # 核采样：保留累积概率 90% 的 tokens
PARAMETER top_k 40            # 只考虑概率最高的 40 个 tokens
PARAMETER num_ctx 32750       # 上下文窗口大小（32K）
PARAMETER repeat_penalty 1.1  # 重复惩罚系数
PARAMETER num_predict 4096    # 最大生成 token 数
```

## 运行时覆盖参数

如果需要临时调整参数（不修改 Modelfile）：

```python
from backend.llm.client import OllamaClient

# 创建客户端时覆盖参数
client = OllamaClient(
    temperature=0.3,  # 覆盖 Modelfile 中的 0.5
    top_p=0.85
)

# 或在调用时传递
response = client.call(
    messages=[...],
    temperature=0.4
)
```

## 常见问题排查

### Q: 修改 Modelfile 后没有生效？

A: 需要重新创建模型：
```bash
ollama create claude-qwen:latest -f config/modelfiles/claude-qwen.modelfile
```

### Q: 模型仍然询问用户？

A: 检查以下几点：
1. 确认模型已重新加载（`ollama show claude-qwen:latest`）
2. 检查用户输入是否真的明确（避免模糊表述）
3. 查看 `backend/tools/agent_tools/propose_options.py` 是否已更新
4. 尝试进一步降低 temperature（0.3-0.4）

### Q: temperature 降低后模型变得"死板"？

A: 根据任务类型调整：
- 结构化任务（代码修改、Bug 修复）：0.3-0.5
- 创造性任务（测试生成、代码解释）：0.6-0.8

可以为不同任务类型使用不同的模型配置：
```yaml
# config/ollama.yaml
models:
  main: "claude-qwen:latest"      # temperature 0.5 (通用)
  precise: "claude-qwen:precise"  # temperature 0.3 (精确任务)
  creative: "claude-qwen:creative" # temperature 0.7 (创造性任务)
```

## 测试验证

### 验证任务自主执行

创建测试输入：
```python
user_input = """
在 network_handler.cpp 的 connect() 函数中添加连接超时和重试机制。

要求：
- 超时时间 5 秒
- 最多重试 3 次
- 每次重试间隔 1 秒
"""
```

**期望行为：**
1. 使用 `grep_search` 或直接定位文件
2. 使用 `view_file` 读取文件
3. 使用 `edit_file` 修改代码
4. ❌ **不应该** 调用 `propose_options` 询问用户

**不期望行为：**
- ❌ 读取文件后调用 `propose_options` 询问"您希望对这个文件做什么？"
- ❌ 输出文本："让我先了解一下您的需求..."

### 验证适当询问

创建模糊输入：
```python
user_input = "帮我看看这个文件"
# 或
user_input = "分析一下这段代码"
```

**期望行为：**
- ✅ 调用 `propose_options` 提供选项：
  - A: 查看 - 阅读并解释文件内容
  - B: 编辑 - 修改特定部分
  - C: 修复 - 查找并修复 bug
  - D: 解释 - 解释其工作原理

## 相关文件

- `config/modelfiles/claude-qwen.modelfile` - 模型参数定义
- `backend/tools/agent_tools/propose_options.py` - 询问工具定义
- `scripts/reload_model.sh` - 模型重载脚本
- `tests/e2e/test_case_1.py` - 端到端测试用例
