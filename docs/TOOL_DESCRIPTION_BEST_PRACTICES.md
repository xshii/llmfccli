# 工具描述最佳实践

## 问题：信息重复

许多工具的 `description` 和 `parameters` 中包含大量重复信息，导致：
- ❌ 增加 token 消耗（每次工具调用都传给 LLM）
- ❌ 维护困难（需要同步更新多处）
- ❌ 信息混乱（LLM 不知道该看哪个）

## 原则：职责分层

### description（决策层）

**职责：** 帮助 LLM 决定**何时**使用这个工具

**应该包含：**
- ✅ 工具的核心用途（1句话）
- ✅ 使用条件（ONLY if / Use when）
- ✅ 禁用条件（DO NOT use if）
- ✅ 返回值类型（Returns...）

**不应该包含：**
- ❌ 参数的详细格式说明
- ❌ 具体的使用示例
- ❌ 实现细节

**长度：** 2-4 句话（约 50-100 tokens）

### parameters（执行层）

**职责：** 帮助 LLM **如何**正确填写参数

**应该包含：**
- ✅ 参数的类型和格式要求
- ✅ 简短的格式示例
- ✅ 取值范围或约束

**不应该包含：**
- ❌ 重复工具的使用场景
- ❌ 重复何时使用这个工具
- ❌ 冗长的解释

**长度：** 每个参数 1-2 句话（约 15-30 tokens）

---

## 示例对比

### ❌ 不好的设计（重复信息）

```python
@property
def description_i18n(self) -> Dict[str, str]:
    return {
        'en': (
            "Present options to user for decision making. "
            "ONLY USE when user intent is GENUINELY UNCLEAR. "
            "Use cases: "
            "(1) User asks 'what can you do' or provides NO specific task; "
            "(2) Task has multiple EQUALLY valid approaches requiring user choice; "
            "(3) User provides ambiguous request like 'help me with this file' without details. "
            "DO NOT USE if user has specified a clear task. "
            "Always includes 'Other' option for custom input. Returns selected option ID."
        )
    }

def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
    return {
        'question': {
            'en': "Question to ask the user, e.g. 'What would you like me to do with this file?'"
            # ❌ 这个示例又暗示了使用场景
        },
        'options': {
            'en': (
                "List of options in format ['A: Title - Description', 'B: Title - Description']. "
                "2-5 options. Example: "
                "['A: View - Read and explain the file', "
                "'B: Edit - Modify specific parts', ...]"
                # ❌ 太长，包含了详细示例
            )
        }
    }
```

**问题：**
- description 长度 180+ tokens
- parameters 又有 100+ tokens
- 总共 280+ tokens，而实际只需要表达一个概念

### ✅ 好的设计（职责分层）

```python
@property
def description_i18n(self) -> Dict[str, str]:
    return {
        'en': (
            "Ask user for decision when intent is GENUINELY UNCLEAR. "
            "Use ONLY if: (1) No specific task provided; "
            "(2) Multiple equally valid approaches need user choice; "
            "(3) Ambiguous request without details. "
            "DO NOT use if task is clear (e.g., 'add timeout', 'fix bug'). "
            "Returns selected option ID (A/B/C/D or X for custom)."
        )
    }

def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
    return {
        'question': {
            'en': "The question to ask (clear and concise)"
            # ✅ 只说明参数用途，不重复使用场景
        },
        'options': {
            'en': (
                "List of 2-5 options in format: ['A: Action - Brief description', ...]. "
                "Example: ['A: View - Read file content', 'B: Edit - Modify code']"
                # ✅ 简短的格式说明和示例
            )
        }
    }
```

**优势：**
- description 约 80 tokens（减少 55%）
- parameters 约 40 tokens（减少 60%）
- 总共 120 tokens（减少 57%）
- 信息清晰，无重复

---

## 通用模板

### 文件系统工具

```python
@property
def description_i18n(self) -> Dict[str, str]:
    return {
        'en': (
            "Read file contents from project. "
            "Use for: viewing code, analyzing structure, before editing. "
            "Returns file content with line numbers."
        )
    }

def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
    return {
        'path': {
            'en': "File path relative to project root"
        },
        'line_range': {
            'en': "Optional [start, end] to read specific lines. Example: [10, 50]"
        }
    }
```

### 构建工具

```python
@property
def description_i18n(self) -> Dict[str, str]:
    return {
        'en': (
            "Execute CMake build. "
            "Use when: need to compile C++ project, verify code changes. "
            "DO NOT use for simple syntax checks. "
            "Returns build output and error messages."
        )
    }

def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
    return {
        'build_type': {
            'en': "Build configuration: 'Debug', 'Release', or 'RelWithDebInfo'"
        },
        'target': {
            'en': "Optional specific target to build. Default: all"
        }
    }
```

### 搜索工具

```python
@property
def description_i18n(self) -> Dict[str, str]:
    return {
        'en': (
            "Search for code patterns using grep. "
            "Use when: need to find function definitions, locate files, search keywords. "
            "Returns list of matching files and line numbers."
        )
    }

def get_parameters_i18n(self) -> Dict[str, Dict[str, str]]:
    return {
        'pattern': {
            'en': "Regex pattern to search. Example: 'class.*Handler'"
        },
        'scope': {
            'en': "Directory to search in. Default: entire project"
        }
    }
```

---

## Token 消耗对比

假设一个工具在任务执行中被调用 10 次：

| 设计方式 | 单次 Token | 10 次调用 | 节省 |
|---------|-----------|-----------|------|
| ❌ 重复信息 | 280 | 2800 | - |
| ✅ 职责分层 | 120 | 1200 | **57%** |

在一个包含 20 个工具的系统中，优化所有工具描述可以：
- 减少每次工具 schema 传递的 token 消耗
- 加快 LLM 响应速度
- 降低 API 成本

---

## 检查清单

审查工具描述时，问自己：

**Description:**
- [ ] 是否用 2-4 句话说清楚了工具用途？
- [ ] 是否明确了使用条件和禁用条件？
- [ ] 是否避免了参数格式的详细说明？
- [ ] 是否避免了冗长的示例？

**Parameters:**
- [ ] 是否只说明了参数的格式要求？
- [ ] 是否避免了重复工具的使用场景？
- [ ] 示例是否足够简短（一行内）？
- [ ] 是否每个参数都独立描述，不相互重复？

**整体:**
- [ ] Description + Parameters 总长度是否 < 150 tokens？
- [ ] 是否可以在不看 parameters 的情况下决定是否使用工具？
- [ ] 是否可以在不看 description 的情况下正确填写参数？

---

## 重构指南

如果发现工具描述有重复信息：

1. **提取决策信息到 description**
   - 何时使用
   - 何时不使用
   - 返回值类型

2. **提取格式信息到 parameters**
   - 参数类型
   - 格式要求
   - 简短示例

3. **删除重复**
   - 相同的使用场景说明
   - 相同的示例
   - 冗余的解释

4. **验证长度**
   - Description: 50-100 tokens
   - Each parameter: 15-30 tokens
   - Total: < 150 tokens

5. **测试理解**
   - 让同事读 description，问"何时用这个工具"
   - 让同事读 parameters，问"如何填写参数"
   - 两者应该独立回答，不需要对方信息

---

## 维护建议

- 修改工具时，同时检查 description 和 parameters 是否仍然分层清晰
- 定期审查所有工具，确保没有信息蔓延
- 新增工具时，使用本文档的模板作为起点
- Code review 时，检查工具描述的 token 消耗

---

## 相关文件

- `backend/tools/base.py` - 工具基类定义
- `backend/tools/agent_tools/propose_options.py` - 优化后的示例
- `backend/agent/tools.py` - 工具注册和 schema 生成
