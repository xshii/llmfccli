# edit_file 统一接口使用指南

`edit_file` 函数已经整合了 VSCode 集成和参数化控制，通过参数自动适配不同场景。

## 快速开始

```python
from backend.tools.filesystem import edit_file

# 默认模式：显示预览 + 等待确认（推荐）
result = edit_file(
    path="src/main.cpp",
    old_str="old code",
    new_str="new code",
    project_root="/path/to/project"
)
# VSCode 模式：显示 GUI diff → 等待确认 → 通过 API 应用
# CLI 模式：显示文本预览 → 输入 y/n → 直接修改文件

# 自动化模式：直接修改，无交互
result = edit_file(
    path="src/main.cpp",
    old_str="old code",
    new_str="new code",
    project_root="/path/to/project",
    confirm=False  # 关键参数
)
# 直接写入文件，不等待用户输入
```

## 参数说明

### 基础参数

```python
edit_file(
    path: str,           # 文件路径（绝对或相对）
    old_str: str,        # 要替换的字符串（必须唯一）
    new_str: str,        # 新字符串
    project_root: str    # 项目根目录（可选）
)
```

### 控制参数

```python
edit_file(
    ...,
    confirm: bool = True,        # 是否需要确认
    show_preview: bool = True    # 是否显示预览
)
```

## 使用场景

### 场景 1：Agent 交互式编辑（默认）

**需求：** AI Agent 修改代码，需要用户审查和确认

```python
# 使用默认参数
result = edit_file(
    path="src/network.cpp",
    old_str="void connect() {",
    new_str="void connect(const std::string& host) {",
    project_root=project_root
)

# 行为：
# VSCode 环境：
#   1. 打开 diff 视图
#   2. 高亮更改部分
#   3. [TODO] 等待用户点击 "Apply" 或 "Cancel"
#   4. 通过 WorkspaceEdit 应用（支持 undo/redo）
#
# CLI 环境：
#   1. 打印文本 diff
#   2. 等待输入 y/n
#   3. 直接写入文件
```

### 场景 2：批量自动化修改

**需求：** 脚本或工具自动重构，不需要交互

```python
# 批量修改多个文件
files_to_edit = [
    ("src/file1.cpp", "old1", "new1"),
    ("src/file2.cpp", "old2", "new2"),
    ("src/file3.cpp", "old3", "new3"),
]

for path, old, new in files_to_edit:
    result = edit_file(
        path=path,
        old_str=old,
        new_str=new,
        project_root=project_root,
        confirm=False  # 无交互模式
    )
    print(f"✓ {path}: {result['message']}")

# 行为：
# 直接修改所有文件，不等待用户输入
# 适合 CI/CD、代码生成、批量重构等场景
```

### 场景 3：快速确认，无预览

**需求：** 需要确认，但不需要看详细 diff

```python
result = edit_file(
    path="config.ini",
    old_str="debug=false",
    new_str="debug=true",
    project_root=project_root,
    confirm=True,       # 需要确认
    show_preview=False  # 不显示预览
)

# 行为：
# 只提示 "确认编辑 config.ini? (y/n): "
# 不显示具体的修改内容
```

## 返回值

### 成功时

```python
{
    'success': True,
    'path': '/path/to/file.cpp',
    'mode': 'vscode' | 'cli' | 'direct',  # 使用的模式
    'message': 'Applied changes via VSCode API',
    'old_str': 'old code...',  # 截断到 100 字符
    'new_str': 'new code...',
    'changes': 5  # 字符数变化
}
```

### 用户取消时

```python
{
    'success': False,
    'message': 'Edit cancelled by user',
    'mode': 'vscode' | 'cli' | 'simple'
}
```

### 错误时

抛出 `FileSystemError` 异常：

```python
try:
    result = edit_file(...)
except FileSystemError as e:
    print(f"编辑失败: {e}")

# 常见错误：
# - "File not found: ..."
# - "String not found in file: ..."
# - "String appears 3 times (must be unique): ..."
# - "Path ... is outside project root"
```

## 环境检测

函数自动检测运行环境：

```python
from backend.rpc.client import is_vscode_mode

if is_vscode_mode():
    # 在 VSCode 扩展中运行
    # - 使用 GUI diff
    # - 通过 VSCode API 应用更改
    # - 支持 undo/redo
else:
    # 在纯 CLI 中运行
    # - 使用文本 diff
    # - 直接修改文件
```

环境变量：`VSCODE_INTEGRATION=true` 表示 VSCode 模式

## 完整示例

### 示例 1：Agent 修复编译错误

```python
def fix_compile_error(file_path: str, error_line: str, fixed_line: str):
    """AI Agent 修复编译错误"""

    # 默认行为：显示 diff，等待确认
    result = edit_file(
        path=file_path,
        old_str=error_line,
        new_str=fixed_line,
        project_root=get_project_root()
    )

    if result['success']:
        print(f"✓ 已修复: {file_path}")
        # 在 VSCode 中，文件已更新且可以 undo
        # 用户可以继续编辑或撤销
    else:
        print(f"✗ 用户取消了修复")
```

### 示例 2：批量重命名

```python
def batch_rename_function(old_name: str, new_name: str):
    """批量重命名函数（自动化）"""
    import subprocess

    # 1. 查找所有引用
    result = subprocess.run(
        ['grep', '-r', '-l', old_name, 'src/'],
        capture_output=True,
        text=True
    )

    files = result.stdout.strip().split('\n')
    print(f"找到 {len(files)} 个文件包含 '{old_name}'")

    # 2. 批量替换（无交互）
    for file_path in files:
        try:
            result = edit_file(
                path=file_path,
                old_str=old_name,
                new_str=new_name,
                confirm=False  # 自动化模式
            )
            print(f"  ✓ {file_path}")
        except FileSystemError as e:
            print(f"  ✗ {file_path}: {e}")

    print(f"\n完成重命名: {old_name} → {new_name}")
```

### 示例 3：条件编辑

```python
def conditional_edit(path: str, old: str, new: str, auto_apply: bool):
    """根据条件决定是否需要确认"""

    result = edit_file(
        path=path,
        old_str=old,
        new_str=new,
        confirm=not auto_apply  # auto_apply=True 时直接修改
    )

    return result['success']

# 使用
# 重要文件：需要确认
conditional_edit("src/main.cpp", old, new, auto_apply=False)

# 测试文件：自动应用
conditional_edit("tests/test_main.cpp", old, new, auto_apply=True)
```

## 与 Agent 系统集成

在 Agent 工具注册中使用：

```python
# backend/agent/tools.py

TOOL_DEFINITIONS = [
    {
        "name": "edit_file",
        "description": "Edit file with str_replace pattern",
        "parameters": {
            "path": {"type": "string", "description": "File path"},
            "old_str": {"type": "string", "description": "String to replace"},
            "new_str": {"type": "string", "description": "New string"},
            "confirm": {
                "type": "boolean",
                "description": "Require user confirmation (default: true)",
                "default": True
            }
        },
        "function": edit_file,
        "category": "write",  # 需要确认的写入操作
        "requires_confirmation": True  # Agent 应该默认请求确认
    }
]
```

Agent 使用时：

```python
# Agent 决策
if user_wants_auto_fix:
    # 用户明确要求自动修复，无需确认
    confirm_flag = False
else:
    # 默认需要用户审查
    confirm_flag = True

result = edit_file(
    path=target_file,
    old_str=detected_error,
    new_str=generated_fix,
    confirm=confirm_flag
)
```

## 最佳实践

### ✅ 推荐

1. **默认确认** - 修改代码时使用默认参数，让用户审查
2. **自动化脚本** - 工具/脚本使用 `confirm=False`
3. **错误处理** - 总是捕获 `FileSystemError`
4. **批量操作** - 考虑先预览所有更改，再批量应用

### ❌ 避免

1. **盲目自动化** - 不要对用户代码使用 `confirm=False`，除非用户明确要求
2. **忽略错误** - 不要忽略 `success=False` 的情况
3. **大字符串** - `old_str` 和 `new_str` 太长会影响预览体验

## 性能

- **VSCode 模式** - 首次调用 ~100ms（RPC 初始化）
- **后续调用** - ~20-50ms（本地 RPC）
- **CLI 模式** - ~1-5ms（直接文件 I/O）
- **用户确认** - 取决于用户操作时间

## 调试

```python
# 查看执行模式
result = edit_file(...)
print(f"Mode used: {result['mode']}")

# 可能的值：
# - 'vscode': 使用了 VSCode API
# - 'cli': CLI 文本预览
# - 'direct': 直接修改
# - 'simple': 简单确认（无预览）

# 启用 RPC 调试日志
import os
os.environ['DEBUG_AGENT'] = '1'

# 查看详细的 RPC 通信日志
```

## 常见问题

### Q: 如何禁用所有交互？

```python
edit_file(..., confirm=False)
```

### Q: 如何强制使用 CLI 模式（即使在 VSCode 中）？

```python
import os
# 临时禁用 VSCode 模式
old_val = os.environ.get('VSCODE_INTEGRATION')
os.environ['VSCODE_INTEGRATION'] = 'false'

result = edit_file(...)  # 会使用 CLI 模式

# 恢复
if old_val:
    os.environ['VSCODE_INTEGRATION'] = old_val
else:
    del os.environ['VSCODE_INTEGRATION']
```

### Q: 如何知道是否使用了 VSCode API？

```python
result = edit_file(...)
if result.get('mode') == 'vscode':
    print("通过 VSCode API 应用，支持 undo/redo")
```

## 更新日志

- **v2.0** - 统一接口，参数化控制
  - 添加 `confirm` 和 `show_preview` 参数
  - 自动检测 VSCode 环境
  - 优雅降级（VSCode 失败时回退到直接修改）

- **v1.0** - 基础实现
  - 直接文件修改
  - 字符串替换验证
