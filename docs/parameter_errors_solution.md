# 解决模型参数传递错误问题

## 问题背景

模型在调用工具时经常出现参数传递错误，常见问题包括：
1. 使用错误的参数名（如 `file` 而不是 `path`）
2. 参数类型错误（如字符串 `"true"` 而不是布尔值 `true`）
3. 参数格式错误（如 `line_range` 应该是数组但传了字符串）
4. 参数拼写错误或大小写错误

## 解决方案

我提供了一套完整的解决方案：

### 1. 增强的系统提示词

文件: `backend/llm/prompts_enhanced.py`

**改进内容**：
- ✅ 为每个工具添加详细的参数说明
- ✅ 提供正确和错误示例对比
- ✅ 明确参数类型要求
- ✅ 列出常见错误和修正方法

**使用方法**：
```python
from backend.llm.prompts_enhanced import get_system_prompt

# 使用增强的系统提示词
system_prompt = get_system_prompt()
```

### 2. 参数验证和自动修正

文件: `backend/tools/parameter_validator.py`

**功能**：
- ✅ 检测常见的参数名错误并自动修正
- ✅ 自动转换参数类型
- ✅ 生成友好的错误反馈
- ✅ 提供参数使用提示

**使用示例**：
```python
from backend.tools.parameter_validator import ParameterValidator

# 验证和修正参数
fixed_args, warning = ParameterValidator.validate_and_fix(
    'view_file',
    {'file': 'main.cpp', 'lines': [10, 20]}  # 错误参数
)

# 结果:
# fixed_args = {'path': 'main.cpp', 'line_range': [10, 20]}
# warning = "参数 'file' 已自动修正为 'path'; 参数 'lines' 已自动修正为 'line_range'"
```

**支持的自动修正**：

| 工具 | 错误参数 | 自动修正为 |
|------|---------|----------|
| view_file | file, file_path, filepath | path |
| view_file | lines, line_numbers | line_range |
| view_file | start_line + end_line | line_range: [start, end] |
| edit_file | file, file_path | path |
| edit_file | find, search, old | old_str |
| edit_file | replace, replacement, new | new_str |
| create_file | file, file_path | path |
| create_file | data, text, body | content |
| grep_search | search, query, regex | pattern |
| grep_search | directory, dir, in | scope |
| list_dir | directory, dir, folder | path |
| list_dir | depth | max_depth |

### 3. Schema 增强器

文件: `backend/tools/schema_enhancer.py`

**功能**：
- ✅ 为工具 schema 添加详细的使用示例
- ✅ 添加参数约束说明
- ✅ 生成工具使用指南

**使用示例**：
```python
from backend.tools.schema_enhancer import SchemaEnhancer

# 增强 schema
enhanced_schema = SchemaEnhancer.enhance_schema('view_file', original_schema)

# 获取使用指南
guide = SchemaEnhancer.get_tool_usage_guide('view_file')
print(guide)
```

## 集成步骤

### 步骤 1: 切换到增强的系统提示词

修改 `backend/agent/loop.py` 或 LLM 客户端，使用增强的提示词：

```python
# 原来:
from backend.llm.prompts import get_system_prompt

# 改为:
from backend.llm.prompts_enhanced import get_system_prompt
```

### 步骤 2: 集成参数验证器

修改 `backend/agent/tools/__init__.py` 中的工具执行逻辑：

```python
from backend.tools.parameter_validator import ParameterValidator

class RegistryToolExecutor(ToolExecutor):
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 验证和修正参数
        fixed_args, warning = ParameterValidator.validate_and_fix(tool_name, arguments)

        # 2. 如果有警告，记录日志
        if warning:
            print(f"⚠️  参数自动修正: {warning}")

        # 3. 使用修正后的参数执行工具
        try:
            result = self.registry.execute_tool(tool_name, fixed_args)
            return result
        except Exception as e:
            # 4. 生成友好的错误反馈
            error_feedback = ParameterValidator.generate_error_feedback(
                tool_name, str(e), arguments
            )
            return {
                'success': False,
                'error': error_feedback
            }
```

### 步骤 3: 增强工具 Schema

修改工具注册时的 schema 生成：

```python
from backend.tools.schema_enhancer import SchemaEnhancer

# 在生成 schema 时增强
schemas = []
for tool_name in registry.list_tools():
    schema = registry.get_tool_schema(tool_name)
    enhanced_schema = SchemaEnhancer.enhance_schema(tool_name, schema)
    schemas.append(enhanced_schema)
```

## 测试

创建测试文件 `tests/unit/test_parameter_validator.py`：

```python
import pytest
from backend.tools.parameter_validator import ParameterValidator

def test_view_file_parameter_fix():
    """测试 view_file 参数修正"""
    # 错误参数
    args = {'file': 'main.cpp', 'lines': [10, 20]}

    # 修正
    fixed, warning = ParameterValidator.validate_and_fix('view_file', args)

    # 验证
    assert fixed == {'path': 'main.cpp', 'line_range': [10, 20]}
    assert warning is not None

def test_edit_file_parameter_fix():
    """测试 edit_file 参数修正"""
    args = {'file': 'test.cpp', 'find': 'old', 'replace': 'new'}

    fixed, warning = ParameterValidator.validate_and_fix('edit_file', args)

    assert fixed == {'path': 'test.cpp', 'old_str': 'old', 'new_str': 'new'}

def test_grep_search_parameter_fix():
    """测试 grep_search 参数修正"""
    args = {'search': 'class', 'directory': 'src/'}

    fixed, warning = ParameterValidator.validate_and_fix('grep_search', args)

    assert fixed == {'pattern': 'class', 'scope': 'src/'}

def test_type_conversion():
    """测试类型转换"""
    # 字符串转布尔
    args = {'path': 'test.cpp', 'old_str': 'a', 'new_str': 'b', 'confirm': 'true'}

    fixed, _ = ParameterValidator.validate_and_fix('edit_file', args)

    assert fixed['confirm'] == True
    assert isinstance(fixed['confirm'], bool)
```

运行测试：
```bash
python3 tests/unit/test_parameter_validator.py
```

## 预期效果

### Before（修复前）
```
模型调用: view_file(file='main.cpp', lines=[10, 20])
错误: 未知参数 'file'
❌ 工具调用失败
```

### After（修复后）
```
模型调用: view_file(file='main.cpp', lines=[10, 20])
⚠️  参数自动修正: 参数 'file' 已自动修正为 'path'; 参数 'lines' 已自动修正为 'line_range'
✅ 工具调用成功: {'content': '...', 'path': '/path/to/main.cpp', ...}
```

## 高级配置

### 1. 自定义参数映射

如果需要添加新的参数映射规则：

```python
# 在 parameter_validator.py 中
PARAMETER_MAPPING['my_tool'] = {
    'wrong_name': 'correct_name',
    'another_wrong': 'correct_name2',
}
```

### 2. 添加自定义类型转换

```python
@classmethod
def _fix_types(cls, tool_name: str, arguments: Dict[str, Any]):
    # 添加自定义类型转换逻辑
    if tool_name == 'my_tool' and 'my_param' in arguments:
        # 自定义转换
        pass
```

### 3. 配置错误重试

在 LLM 客户端中，当遇到参数错误时自动重试：

```python
def call_tool_with_retry(tool_name, arguments, max_retries=3):
    for i in range(max_retries):
        try:
            fixed_args, warning = ParameterValidator.validate_and_fix(
                tool_name, arguments
            )
            result = execute_tool(tool_name, fixed_args)
            return result
        except Exception as e:
            if i == max_retries - 1:
                # 最后一次尝试，返回详细错误
                return ParameterValidator.generate_error_feedback(
                    tool_name, str(e), arguments
                )
            # 重试
            continue
```

## 常见问题

### Q1: 参数修正后模型还是传错怎么办？
A: 检查系统提示词是否已切换到增强版本，确保模型能看到详细的参数说明和示例。

### Q2: 如何禁用自动修正？
A: 在调用 `validate_and_fix` 之前检查配置：
```python
if not config.get('auto_fix_parameters', True):
    # 不使用自动修正
    result = execute_tool(tool_name, arguments)
```

### Q3: 参数修正覆盖不全？
A: 在 `PARAMETER_MAPPING` 中添加新的映射规则，或在错误日志中分析常见错误模式。

## 监控和优化

### 1. 记录参数错误统计

```python
from collections import Counter

parameter_errors = Counter()

def track_parameter_fix(tool_name, warning):
    if warning:
        parameter_errors[tool_name] += 1

# 定期检查
print(parameter_errors.most_common(10))
```

### 2. 生成错误报告

```python
def generate_error_report():
    report = "参数错误统计:\n"
    for tool, count in parameter_errors.most_common():
        report += f"{tool}: {count} 次修正\n"
    return report
```

## 总结

通过以上三个模块的配合：
1. **增强的系统提示词** - 教会模型正确使用工具
2. **参数验证器** - 自动修正常见错误
3. **Schema 增强器** - 提供详细的使用说明

可以有效解决模型参数传递错误的问题，提升工具调用成功率。

建议先从切换系统提示词开始，观察效果后再逐步集成参数验证器。
