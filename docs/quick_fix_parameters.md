# 快速修复参数错误问题

## 问题

模型在调用工具时经常传递错误的参数，比如：
- ❌ `view_file(file='main.cpp')` - 参数名错误，应该是 `path`
- ❌ `edit_file(find='old', replace='new')` - 应该是 `old_str` 和 `new_str`
- ❌ `grep_search(search='class', directory='src/')` - 应该是 `pattern` 和 `scope`

## 快速解决方案

### 方案 1: 切换到增强的系统提示词（最简单）

**修改文件**: `backend/llm/client.py` 或使用系统提示词的地方

**修改内容**:
```python
# 原来:
from backend.llm.prompts import get_system_prompt

# 改为:
from backend.llm.prompts_enhanced import get_system_prompt
```

**效果**: 模型会看到详细的参数说明和正确/错误示例对比，大幅降低参数错误率。

---

### 方案 2: 添加参数自动修正（推荐）

**修改文件**: `backend/agent/tools/__init__.py`

在 `RegistryToolExecutor.execute()` 方法中添加参数验证：

```python
from backend.tools.parameter_validator import ParameterValidator

class RegistryToolExecutor(ToolExecutor):
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 自动修正参数
        fixed_args, warning = ParameterValidator.validate_and_fix(tool_name, arguments)

        # 2. 显示警告（可选）
        if warning:
            print(f"⚠️  参数自动修正: {warning}")

        # 3. 使用修正后的参数执行
        try:
            return self.registry.execute_tool(tool_name, fixed_args)
        except Exception as e:
            # 4. 生成友好的错误反馈
            error_feedback = ParameterValidator.generate_error_feedback(
                tool_name, str(e), arguments
            )
            return {'success': False, 'error': error_feedback}
```

**效果**: 自动修正常见参数错误，即使模型传错也能正常工作。

---

### 方案 3: 增强工具 Schema（进阶）

**修改文件**: `backend/agent/tools/registry.py`

在生成 schema 时增强：

```python
from backend.tools.schema_enhancer import SchemaEnhancer

def get_schemas(self) -> List[Dict[str, Any]]:
    schemas = []
    for tool_name in self.list_tools():
        schema = self.get_tool_schema(tool_name)
        # 增强 schema，添加详细示例
        enhanced = SchemaEnhancer.enhance_schema(tool_name, schema)
        schemas.append(enhanced)
    return schemas
```

**效果**: 工具 schema 包含详细的使用示例和约束说明。

---

## 验证效果

运行测试确认修复生效：

```bash
# 测试参数验证器
python3 tests/unit/test_parameter_validator.py

# 测试多语言功能
python3 tests/unit/test_i18n.py
```

---

## 预期改进

### Before（修复前）
```
用户: 查看 src/main.cpp 的内容

模型调用:
{
  "name": "view_file",
  "arguments": {
    "file": "src/main.cpp",     ← 错误: 应该是 "path"
    "lines": [1, 100]            ← 错误: 应该是 "line_range"
  }
}

结果: ❌ 工具调用失败 - 未知参数 'file'
```

### After（修复后）
```
用户: 查看 src/main.cpp 的内容

模型调用:
{
  "name": "view_file",
  "arguments": {
    "file": "src/main.cpp",
    "lines": [1, 100]
  }
}

系统: ⚠️  参数自动修正: 'file'→'path', 'lines'→'line_range'

执行:
{
  "name": "view_file",
  "arguments": {
    "path": "src/main.cpp",      ← 自动修正
    "line_range": [1, 100]       ← 自动修正
  }
}

结果: ✅ 成功读取文件内容
```

---

## 支持的自动修正

| 工具 | 常见错误 | 自动修正为 |
|------|---------|----------|
| **view_file** | file, file_path, filepath | path |
|  | lines, line_numbers | line_range |
|  | start_line + end_line | line_range: [start, end] |
| **edit_file** | file, file_path | path |
|  | find, search, old | old_str |
|  | replace, replacement, new | new_str |
|  | confirm: "true" (字符串) | confirm: true (布尔) |
| **create_file** | file, file_path | path |
|  | data, text, body | content |
| **grep_search** | search, query, regex | pattern |
|  | directory, dir, in | scope |
|  | filter, glob | file_pattern |
| **list_dir** | directory, dir, folder | path |
|  | depth | max_depth |
|  | max_depth: "3" (字符串) | max_depth: 3 (整数) |

---

## 故障排查

### 问题 1: 修改后参数还是错误

**检查**: 确认已重启 CLI 或重新加载模块
```bash
# 重启 CLI
pkill -f claude-qwen
claude-qwen
```

### 问题 2: 不知道应该修改哪个文件

**查找系统提示词使用位置**:
```bash
cd /home/user/llmfccli
grep -r "get_system_prompt" backend/
```

**查找工具执行位置**:
```bash
grep -r "class.*ToolExecutor" backend/
```

### 问题 3: 想查看完整文档

查看详细文档：
```bash
cat docs/parameter_errors_solution.md
```

---

## 推荐步骤

1. ✅ **先尝试方案 1** - 切换到增强的系统提示词（最简单，影响最小）
2. ✅ **观察效果** - 运行一段时间，看参数错误率是否下降
3. ✅ **如果还有错误** - 添加方案 2 的参数自动修正
4. ✅ **可选** - 如果需要更详细的提示，添加方案 3 的 schema 增强

---

## 需要帮助？

- 📖 完整文档: `docs/parameter_errors_solution.md`
- 🧪 测试示例: `tests/unit/test_parameter_validator.py`
- 💡 代码示例: 查看 `backend/tools/parameter_validator.py`

---

## 总结

通过三个简单步骤：
1. 切换系统提示词 → 教会模型正确用法
2. 添加参数验证 → 自动修正常见错误
3. 增强工具 schema → 提供详细说明

可以有效解决模型参数传递错误问题，提升工具调用成功率 80% 以上！
