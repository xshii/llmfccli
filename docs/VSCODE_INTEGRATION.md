# VSCode Extension 集成

本文档描述了 Claude-Qwen 与 VSCode Extension 的集成方案。

## 概述

VSCode 集成允许 Claude-Qwen 与 VSCode 编辑器进行交互，支持以下功能：

- 获取当前编辑的文件
- 获取选中的文本
- 在 VSCode 中显示 diff 对比
- 应用代码修改
- 打开指定文件并跳转到行号
- 获取工作区路径

## 测试命令

### `/testvs` - 测试 VSCode 集成

在 CLI 中运行 `/testvs` 命令可以测试 VSCode 集成功能（Mock 模式）：

```bash
> /testvs
```

**输出示例：**
```
═══════════════════════════════════════
  VSCode Extension 集成测试
═══════════════════════════════════════

通信模式: mock

┌───────────────────────────┬────────┬──────────────────────────┐
│ 测试项                    │ 状态   │ 结果                     │
├───────────────────────────┼────────┼──────────────────────────┤
│ 1. 获取当前文件           │ ✓      │ 路径: /path/to/file.cpp  │
│ 2. 获取选中文本           │ ✓      │ 文本: std::cout << ...   │
│ 3. 显示 Diff 对比         │ ✓      │ Diff shown: 测试修改      │
│ 4. 应用代码修改           │ ✓      │ Changes applied          │
│ 5. 打开文件               │ ✓      │ File opened              │
│ 6. 获取工作区路径         │ ✓      │ 路径: /path/to/project   │
└───────────────────────────┴────────┴──────────────────────────┘
```

## 通信协议

VSCode extension 通过 JSON-RPC 2.0 协议与 CLI 通信。

### 通信模式

1. **Mock 模式** (默认)
   - 用于开发和测试
   - 返回模拟数据，不依赖实际的 VSCode extension

2. **IPC 模式** (计划中)
   - 通过 stdin/stdout 进行通信
   - 适用于 VSCode extension 作为子进程的场景

3. **Socket 模式** (计划中)
   - 通过 Unix Domain Socket 或 TCP Socket 通信
   - 适用于独立运行的 CLI 进程

### JSON-RPC 消息格式

**请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "getActiveFile",
  "params": {}
}
```

**响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "file": {
      "path": "/path/to/file.cpp",
      "content": "...",
      "language": "cpp",
      "lineCount": 100
    }
  }
}
```

## 支持的方法

### 1. getActiveFile

获取当前编辑的文件。

**参数：** 无

**返回：**
```json
{
  "success": true,
  "file": {
    "path": "/path/to/file.cpp",
    "content": "file contents...",
    "language": "cpp",
    "lineCount": 100
  }
}
```

### 2. getSelection

获取当前选中的文本。

**参数：** 无

**返回：**
```json
{
  "success": true,
  "selection": {
    "text": "selected text...",
    "start": {"line": 10, "character": 5},
    "end": {"line": 12, "character": 20}
  }
}
```

### 3. showDiff

在 VSCode 中显示 diff 对比。

**参数：**
```json
{
  "title": "修改对比",
  "originalPath": "/path/to/file.cpp",
  "modifiedContent": "modified content..."
}
```

**返回：**
```json
{
  "success": true,
  "message": "Diff shown: 修改对比"
}
```

### 4. applyChanges

应用代码修改。

**参数：**
```json
{
  "path": "/path/to/file.cpp",
  "oldStr": "old code...",
  "newStr": "new code..."
}
```

**返回：**
```json
{
  "success": true,
  "message": "Applied changes to /path/to/file.cpp"
}
```

### 5. openFile

打开文件并跳转到指定位置。

**参数：**
```json
{
  "path": "/path/to/file.cpp",
  "line": 42,
  "column": 10
}
```

**返回：**
```json
{
  "success": true,
  "message": "Opened file: /path/to/file.cpp"
}
```

### 6. getWorkspaceFolder

获取 VSCode 工作区路径。

**参数：** 无

**返回：**
```json
{
  "success": true,
  "folder": "/path/to/workspace"
}
```

## 开发指南

### 客户端初始化

```python
from backend.tools import vscode

# 初始化客户端（Mock 模式）
client = vscode.init_vscode_client(mode="mock")

# 或者使用 IPC 模式（需要实现）
# client = vscode.init_vscode_client(mode="ipc")

# 或者使用 Socket 模式（需要实现）
# client = vscode.init_vscode_client(mode="socket", socket_path="/tmp/vscode.sock")
```

### 使用工具函数

```python
from backend.tools import vscode

# 获取当前文件
file_info = vscode.get_active_file()
print(f"当前文件: {file_info['path']}")

# 获取选中文本
selection = vscode.get_selection()
print(f"选中: {selection['text']}")

# 显示 diff
vscode.show_diff(
    title="修改预览",
    original_path="/path/to/file.cpp",
    modified_content="new content"
)

# 应用修改
vscode.apply_changes(
    path="/path/to/file.cpp",
    old_str="old code",
    new_str="new code"
)

# 打开文件
vscode.open_file("/path/to/file.cpp", line=42)

# 获取工作区
workspace = vscode.get_workspace_folder()
```

## 测试

运行单元测试：

```bash
# 运行 VSCode 集成测试
python3 tests/unit/test_vscode.py

# 或者运行所有单元测试
python3 tests/run_unit_tests.py
```

## 下一步计划

1. **实现 IPC 通信模式**
   - VSCode extension 通过 stdin/stdout 与 CLI 通信
   - 适用于 extension 启动 CLI 进程的场景

2. **实现 Socket 通信模式**
   - 使用 Unix Domain Socket 或 TCP Socket
   - 适用于 CLI 独立运行的场景

3. **开发 VSCode Extension**
   - 实现 JSON-RPC 服务端
   - 处理所有支持的方法
   - 集成到 VSCode UI

4. **添加更多功能**
   - 批量文件操作
   - 符号查找和跳转
   - 诊断信息集成
   - Terminal 集成

## 相关文件

- `backend/tools/vscode.py` - VSCode 工具实现
- `backend/cli.py` - CLI 中的 `/testvs` 命令
- `tests/unit/test_vscode.py` - 单元测试
- `docs/VSCODE_INTEGRATION.md` - 本文档
