# 双层确认机制测试覆盖

本文档说明双层确认集成的测试覆盖情况。

## 测试文件

- **tests/unit/test_edit_file_confirmation.py** - 双层确认集成测试（新增）
- **tests/unit/test_confirmation.py** - ToolConfirmation 单独测试（已有）
- **tests/unit/test_tool_executor.py** - ToolExecutor 接口测试（已有）

## 双层确认流程

```
用户请求编辑文件
    ↓
Layer 1: ToolConfirmation (Agent 执行权限层)
    ├─ 首次使用 → 需要确认 (allow_once / allow_always / deny)
    ├─ allow_always → 添加到 allowed_tools
    └─ 已在 allowed_tools → 自动允许
    ↓
RegistryToolExecutor (智能适配层)
    ├─ 检查 tool_name 是否在 allowed_tools
    ├─ 如果在 → 自动设置 confirm=False
    └─ 如果不在 → 使用默认 confirm=True
    ↓
Layer 2: edit_file confirm 参数 (具体操作审批层)
    ├─ confirm=True → 显示 diff，等待确认
    └─ confirm=False → 直接修改，无交互
```

## 测试用例详解

### Test 1: 首次使用 edit_file（双层确认）

**场景**: Agent 第一次尝试编辑文件

**预期行为**:
- Layer 1: ToolConfirmation 需要用户确认
- Layer 2: edit_file 使用默认 confirm=True

**测试验证**:
```python
needs_confirm = confirmation.needs_confirmation('edit_file', {...})
assert needs_confirm is True  # 首次使用需要确认
```

**实际流程**: 用户会看到两次确认请求：
1. "允许 Agent 使用 edit_file 工具吗？" (ToolConfirmation)
2. "应用以下编辑吗？[diff preview]" (edit_file confirm)

---

### Test 2: 用户选择 "始终允许" 后（零确认）

**场景**: 用户在第一次使用时选择了 "allow_always"

**预期行为**:
- Layer 1: ToolConfirmation 自动允许（edit_file 在 allowed_tools 中）
- RegistryToolExecutor 智能适配：自动设置 confirm=False
- Layer 2: edit_file 直接修改，无交互

**测试验证**:
```python
# 用户选择 allow_always
confirmation.confirm_tool_execution('edit_file', {...})
assert 'edit_file' in confirmation.allowed_tools

# 后续编辑自动应用
result = executor.execute_tool('edit_file', {...})
assert result['success'] is True
# 文件已修改，无需任何确认
```

**实际流程**: 用户完全无感，Agent 直接编辑文件

---

### Test 3: 智能参数适配

**场景**: 测试 RegistryToolExecutor 的智能逻辑

**测试用例**:

**Case 1**: edit_file 在 allowed_tools 中
```python
confirmation.allowed_tools.add('edit_file')
executor = RegistryToolExecutor(project_root, confirmation_manager=confirmation)

# 用户未指定 confirm 参数
result = executor.execute_tool('edit_file', {
    'path': 'test.txt',
    'old_str': 'old',
    'new_str': 'new'
    # 注意：没有 confirm 参数
})

# RegistryToolExecutor 自动添加 confirm=False
assert result['success'] is True  # 直接应用
```

**Case 2**: 不同工具（不在 allowed_tools 中）
```python
needs_confirm = confirmation.needs_confirmation('view_file', {...})
assert needs_confirm is True  # 仍需确认
```

**关键逻辑** (backend/agent/tool_executor.py:88-106):
```python
def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
    # Smart handling for edit_file
    if tool_name == 'edit_file' and self.confirmation:
        if tool_name in self.confirmation.allowed_tools:
            # User trusts this tool, skip tool-level confirmation
            arguments = dict(arguments)
            arguments['confirm'] = False
    return self.registry.execute(tool_name, arguments)
```

---

### Test 4: 向后兼容性

**场景**: 不使用 ToolConfirmation（老代码）

**预期行为**: 系统仍然正常工作，无智能适配

**测试验证**:
```python
# 不传 confirmation_manager
executor = RegistryToolExecutor(project_root, confirmation_manager=None)

# 需要手动指定 confirm 参数
result = executor.execute_tool('edit_file', {
    'path': 'test.txt',
    'old_str': 'old',
    'new_str': 'new',
    'confirm': False  # 必须显式指定
})

assert result['success'] is True
```

**意义**: 确保现有代码不受影响，渐进式迁移

---

### Test 5: 多文件编辑工作流（信任演进）

**场景**: 真实世界的 Agent 批量编辑任务

**工作流**:
```
文件 1 编辑
  ↓ 用户确认 + allow_always
文件 2 编辑
  ↓ 自动应用（无确认）
文件 3 编辑
  ↓ 自动应用（无确认）
```

**测试验证**:
```python
# 第 1 次编辑：需要确认
assert confirmation.needs_confirmation('edit_file', {...}) is True

# 用户选择 allow_always
confirmation.confirm_tool_execution('edit_file', {...})

# 第 2、3 次编辑：自动应用
executor.execute_tool('edit_file', {...})  # file2 - 直接成功
executor.execute_tool('edit_file', {...})  # file3 - 直接成功
```

**实际体验**: "审查一次，信任全程"

---

### Test 6: 确认设置持久化

**场景**: Agent 重启后，用户的信任设置应保留

**测试验证**:
```python
# Session 1: 用户设置 allow_always
confirmation1 = ToolConfirmation(confirmation_file=conf_path)
confirmation1.confirm_tool_execution('edit_file', {...})
# 保存到 ~/.claude_qwen_confirmations.json

# Session 2: 新的 Agent 实例
confirmation2 = ToolConfirmation(confirmation_file=conf_path)
assert 'edit_file' in confirmation2.allowed_tools  # 自动加载

executor2 = RegistryToolExecutor(project_root, confirmation2)
result = executor2.execute_tool('edit_file', {...})
# 仍然自动应用，无需重新确认
```

**文件格式** (~/.claude_qwen_confirmations.json):
```json
{
  "allowed_tools": ["edit_file"],
  "allowed_bash_commands": ["ls", "pwd"],
  "denied_tools": []
}
```

---

## 测试覆盖矩阵

| 测试场景 | Layer 1 (ToolConfirmation) | Layer 2 (edit_file) | 用户体验 |
|----------|----------------------------|---------------------|----------|
| 首次使用 | 需要确认 | confirm=True (默认) | 2 次确认 |
| allow_always 后 | 自动允许 | confirm=False (智能设置) | 0 次确认 |
| 无 confirmation_manager | N/A | confirm=明确指定 | 取决于参数 |
| 不同工具 | 需要确认 | N/A | 1 次确认 |

## 运行测试

### 单独运行双层确认测试

```bash
python3 tests/unit/test_edit_file_confirmation.py
```

### 作为单元测试套件的一部分运行

```bash
python3 tests/run_unit_tests.py
```

### 预期输出

```
======================================================================
Testing Two-Layer Confirmation Integration
======================================================================

Test 1: First-time edit_file (2-layer confirmation)
✓ Layer 1 (ToolConfirmation) needs confirmation: True
✓ First-time edit_file requires both confirmation layers
✅ Test 1 PASSED

Test 2: edit_file after 'always allow' (0 confirmations)
✓ User set 'always allow' for edit_file
✓ edit_file added to allowed_tools: {'edit_file'}
✓ Layer 1 (ToolConfirmation) needs confirmation: False
✓ Layer 2 (edit_file): auto-set confirm=False, edit applied directly
✓ Smart adaptation: 0 confirmations needed
✅ Test 2 PASSED

Test 3: Smart parameter adaptation in RegistryToolExecutor
✓ Pre-configured allowed_tools: {'edit_file'}
  ✓ Smart adaptation: confirm=False was auto-set
  ✓ Edit applied directly without confirmation
✅ Test 3 PASSED

Test 4: RegistryToolExecutor without confirmation manager
✓ Executor works without confirmation_manager
✓ Backward compatibility maintained
✅ Test 4 PASSED

Test 5: Multiple edits workflow (trust evolution)
  ✓ Workflow: 1st edit (confirmed) → 2nd/3rd edits (auto-approved)
✅ Test 5 PASSED

Test 6: Confirmation persistence across executor instances
  ✓ Loaded allowed_tools: {'edit_file'}
  ✓ Second edit auto-approved (persistence works)
✅ Test 6 PASSED

======================================================================
✅ ALL TESTS PASSED - Two-layer confirmation working correctly!
======================================================================

Summary:
  ✓ Layer 1 (ToolConfirmation): Agent execution permission
  ✓ Layer 2 (edit_file confirm): Specific operation approval
  ✓ Smart adaptation: auto confirm=False when tool in allowed_tools
  ✓ Backward compatibility: works without confirmation_manager
  ✓ Persistence: confirmations survive executor restarts
```

## 相关文件

### 实现文件

- `backend/agent/tool_confirmation.py` - ToolConfirmation 类
- `backend/agent/tool_executor.py` - RegistryToolExecutor 智能适配逻辑
- `backend/agent/loop.py` - AgentLoop 初始化集成
- `backend/agent/tools.py` - edit_file 工具注册
- `backend/tools/filesystem.py` - edit_file 实现

### 测试文件

- `tests/unit/test_edit_file_confirmation.py` - 双层确认集成测试（本测试）
- `tests/unit/test_confirmation.py` - ToolConfirmation 单独测试
- `tests/unit/test_tool_executor.py` - ToolExecutor 接口测试

### 文档文件

- `docs/EDIT_FILE_USAGE.md` - edit_file 使用指南
- `docs/VSCODE_INTEGRATION_BEST_PRACTICES.md` - VSCode 集成最佳实践
- `docs/TWO_LAYER_CONFIRMATION_TESTS.md` - 本文档

## 设计原则

1. **最小惊讶原则**: 首次使用需要确认，建立信任后自动化
2. **用户控制**: 用户明确选择 "allow_always" 后才启用自动化
3. **智能适配**: 系统根据用户信任级别自动调整行为
4. **向后兼容**: 不强制使用新机制，老代码仍可工作
5. **持久化**: 用户的选择跨会话保存

## 未来扩展

- [ ] 支持按文件路径模式的细粒度控制（如 "允许编辑 tests/ 下所有文件"）
- [ ] 支持按修改范围的自动决策（如 "小于 10 行的修改自动应用"）
- [ ] 集成到 VSCode 扩展的 GUI 确认对话框
- [ ] 添加确认统计和审计日志
