# 模型参数调优指南

## 问题现象

如果模型在执行任务时表现出以下行为：
- 读取文件后询问"您希望对这个文件做什么？"（尽管任务已经很明确）
- 过度使用 `propose_options` 工具
- 在任务明确的情况下仍然要求用户输入
- **用纯文本询问"下一步建议"或"还需要什么帮助吗"**（而不是使用工具）
- 任务完成后不停止，继续主动询问用户

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
4. **禁止纯文本提问** - 绝不用纯文本询问"下一步建议"或"还需要什么"
5. **任务完成即停止** - 完成任务后直接结束，不要主动询问是否需要其他帮助
```

### 4. 模型习惯性输出"下一步建议"

**问题：** 模型在完成任务后用纯文本输出类似内容：
- "接下来我可以帮您..."
- "您还需要什么帮助吗？"
- "下一步建议：..."

**原因：** 许多对话模型训练时包含"helpful assistant"模式，习惯性询问用户需求。

**修复：** 在 System Prompt 中明确禁止：
- 绝不用纯文本提问
- 如需询问，必须使用 `propose_options` 工具
- 任务完成后直接停止，不要主动提供额外帮助

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

### Q: 模型用纯文本询问"下一步建议"或"还需要什么"？

A: 这是最常见的问题。修复步骤：

1. **检查 Modelfile 是否包含禁止规则**：
```bash
grep -A 2 "禁止纯文本提问" config/modelfiles/claude-qwen.modelfile
```
应该看到：
```
4. **禁止纯文本提问** - 绝不用纯文本询问"下一步建议"或"还需要什么"
5. **任务完成即停止** - 完成用户请求的任务后直接结束
```

2. **重新加载模型**：
```bash
bash scripts/reload_model.sh
```

3. **验证修复**：
   - ✅ 正确：任务完成后直接停止，或调用 `propose_options` 工具
   - ❌ 错误：输出纯文本"接下来我可以帮您..."

4. **如果仍有问题**：
   - 降低 temperature 到 0.3-0.4（更严格）
   - 检查是否在调用工具后立即输出文本（应该等待工具结果）
   - 查看日志确认模型版本是否正确加载

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

### 验证无纯文本提问

**测试场景：** 任务完成后模型是否会用纯文本询问"下一步"

创建简单任务：
```python
user_input = "查看 main.cpp 文件的第 10-20 行"
```

**期望行为：**
1. 调用 `view_file` 读取指定行
2. **直接结束**，不输出任何额外文本
3. ✅ 正确结束标志：无额外输出，或只有简短的任务完成说明

**不期望行为（❌ 错误）：**
- ❌ "接下来我可以帮您..."
- ❌ "您还需要什么帮助吗？"
- ❌ "下一步建议：..."
- ❌ "我已经完成了查看，现在您想..."

**调试技巧：**
如果模型仍然输出纯文本提问：

1. 检查响应中是否包含关键词：
```python
response = agent.run(user_input)
forbidden_phrases = ["下一步", "接下来", "还需要", "您想", "帮您"]
has_forbidden = any(phrase in response for phrase in forbidden_phrases)
assert not has_forbidden, f"模型仍在用纯文本提问: {response}"
```

2. 查看工具调用记录：
```python
# 确认模型没有在完成任务后调用 propose_options
tool_names = [call.get('function', {}).get('name') for call in agent.tool_calls]
propose_calls = [name for name in tool_names if name == 'propose_options']
print(f"propose_options 调用次数: {len(propose_calls)}")
```

3. 如果仍有问题，尝试更严格的 temperature：
```bash
# 临时测试
ollama run claude-qwen:latest --temperature 0.3 "查看 main.cpp 的第 10-20 行"
```

## 相关文件

- `config/modelfiles/claude-qwen.modelfile` - 模型参数定义
- `backend/tools/agent_tools/propose_options.py` - 询问工具定义
- `scripts/reload_model.sh` - 模型重载脚本
- `tests/e2e/test_case_1.py` - 端到端测试用例
