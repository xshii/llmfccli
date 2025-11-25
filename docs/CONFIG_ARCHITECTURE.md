# 配置架构说明

## 设计原则

**单一数据源（Single Source of Truth）**：避免配置重复，每个配置项只在一个地方定义。

## 配置分层

### 1. Modelfile (`config/modelfiles/*.modelfile`)

**用途**：固化模型定义和参数

**包含**：
- `FROM`：基础模型
- `SYSTEM`：系统提示词（固定）
- `PARAMETER`：模型参数（固定）
  - temperature（温度）
  - top_p（核采样）
  - top_k（top-k 采样）
  - num_ctx（上下文窗口大小）
  - repeat_penalty（重复惩罚）
  - num_predict（最大输出 tokens）
  - **stop（停止词）**：告诉模型何时停止生成，避免重复配置

**特点**：
- 这些参数在创建模型时被固化到模型定义中
- 不需要在每次 API 调用时重复传递
- 保证模型行为的一致性

**示例**：
```dockerfile
FROM qwen3:latest

SYSTEM """你是一个专业的 C/C++ 编程助手..."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 131072
```

### 2. ollama.yaml (`config/ollama.yaml`)

**用途**：运行时配置

**包含**：
- `base_url`：Ollama 服务器地址
- `model`：使用的模型名称
- `timeout`：请求超时时间
- `stream`：是否启用流式输出
- `models`：不同用途的模型配置（main, compress, intent）
- `retry`：重试策略
- `ssh`：SSH 远程配置
- `model_management`：模型管理配置

**不包含**：
- ~~generation 参数~~（已在 Modelfile 中固化）

**特点**：
- 运行时可变的配置
- 不同环境可能不同（开发/生产）
- 与模型定义无关的基础设施配置

**示例**：
```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "claude-qwen:latest"  # 使用自定义模型
  timeout: 300
  stream: true

  # 注意：temperature 等参数已在 Modelfile 中固化
  # 如需临时覆盖，可在代码中通过 kwargs 传递
```

## Stop Tokens 配置说明

### Stop Tokens 的作用

Stop tokens 告诉模型何时停止生成，防止：
- 模型继续生成用户对话（如 `Human:`）
- 生成超出预期的内容
- 无限循环生成

### 配置位置：仅在 Modelfile 中

**✅ 正确做法**（Modelfile）：
```dockerfile
PARAMETER stop "<|im_end|>"       # Qwen3 消息结束标记
PARAMETER stop "<|endoftext|>"    # 通用文本结束标记
PARAMETER stop "Human:"           # 防止生成用户回复
PARAMETER stop "\nHuman:"         # 防止生成用户回复（带换行）
```

**❌ 避免做法**（client.py）：
```python
# 不要在 API 调用中硬编码 stop tokens
data = {
    'model': self.model,
    'messages': messages,
    'stop': ['<|endoftext|>', '<|im_end|>']  # ❌ 与 Modelfile 重复
}
```

### 客户端 Stop Token 检测 vs API Stop Parameter

这是两个不同的概念：

1. **API Stop Parameter**（Modelfile PARAMETER stop）
   - 在 **Modelfile 中定义**
   - 告诉 Ollama **何时停止生成**
   - 在服务器端生效

2. **客户端 Stop Token 检测**（client.py 中的 stop_tokens）
   - 在 **流式响应处理**中使用
   - 用于**提前终止客户端接收**
   - 避免处理已知会出现的多余内容
   - 仅影响客户端，不影响服务器生成

**客户端检测示例**（保留）：
```python
# 这是客户端逻辑，与 Modelfile 不冲突
stop_tokens = ['<|endoftext|>', '<|im_end|>']
for line in process.stdout:
    if any(token in content for token in stop_tokens):
        break  # 提前终止接收
```

## 参数覆盖机制

虽然参数已在 Modelfile 中固化，但仍支持临时覆盖：

```python
# 使用 Modelfile 中的默认参数
response = client.chat(messages)

# 临时覆盖参数（用于特殊场景）
response = client.chat(messages, temperature=0.1, top_p=0.95)
```

## 配置优先级

```
代码 kwargs > ollama.yaml generation > Modelfile PARAMETER
```

**推荐做法**：
1. **默认情况**：依赖 Modelfile 中的固化参数
2. **临时调整**：通过代码 kwargs 覆盖（如测试不同参数）
3. **避免**：在 ollama.yaml 中配置 generation 参数

## 为什么这样设计？

### 优点

1. **避免重复**：参数只在 Modelfile 中定义一次
2. **版本控制友好**：Modelfile 随代码一起管理，参数变更可追溯
3. **一致性**：所有环境使用相同的模型参数
4. **简化配置**：ollama.yaml 只关注基础设施配置
5. **清晰分离**：模型定义（Modelfile）vs 运行时配置（YAML）

### 实际场景

#### 场景 1：标准使用
```python
# ollama.yaml: 不包含 generation 参数
# Modelfile: PARAMETER temperature 0.7

client = OllamaClient()
response = client.chat(messages)  # 使用 temperature=0.7
```

#### 场景 2：临时调整
```python
# 需要更保守的输出
response = client.chat(messages, temperature=0.1)

# 需要更有创意的输出
response = client.chat(messages, temperature=0.9)
```

#### 场景 3：不同模型不同参数
```yaml
# config/modelfiles/claude-qwen.modelfile
PARAMETER temperature 0.7

# config/modelfiles/claude-qwen-creative.modelfile
PARAMETER temperature 0.9
```

```yaml
# ollama.yaml
models:
  main: "claude-qwen:latest"        # 标准版本
  creative: "claude-qwen-creative"  # 创意版本
```

## 迁移指南

如果现有配置在 `ollama.yaml` 中包含 `generation` 参数：

### 步骤 1：移除 ollama.yaml 中的 generation
```yaml
# 删除这部分
# generation:
#   temperature: 0.7
#   top_p: 0.9
#   ...
```

### 步骤 2：确保 Modelfile 中已包含参数
```dockerfile
# config/modelfiles/claude-qwen.modelfile
PARAMETER temperature 0.7
PARAMETER top_p 0.9
# ...
```

### 步骤 3：重新创建模型
```bash
python backend/remotectl/sync_models.py
```

### 步骤 4：验证
```python
client = OllamaClient()
print(client.generation_params)  # 应该是 {}
```

## 参考

- [Ollama Modelfile Documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
