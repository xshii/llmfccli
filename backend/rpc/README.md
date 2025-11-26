# JSON-RPC Communication Module

该模块实现 CLI 与 VSCode extension 之间的双向通信。

## 架构

```
┌──────────────────┐         ┌──────────────────┐
│  VSCode          │  stdin  │   CLI            │
│  Extension       │◄────────┤   (Python)       │
│                  │  stdout │                  │
│  - JSON-RPC      ├────────►│  - RPC Client    │
│    Server        │         │  - Tools         │
│  - UI Operations │         │  - Agent Loop    │
└──────────────────┘         └──────────────────┘
```

## 通信流程

### 1. CLI 启动时自动初始化

当设置 `VSCODE_INTEGRATION=true` 环境变量时，CLI 自动启动 RPC 客户端：

```python
# backend/cli.py
if os.getenv('VSCODE_INTEGRATION') == 'true':
    rpc_client = get_client()  # 启动后台监听线程
```

### 2. CLI 向 VSCode 发送请求

当 CLI 需要 VSCode 操作时（如显示 diff）：

```python
# backend/tools/vscode.py
response = send_vscode_request("showDiff", {
    "title": "修改对比",
    "originalPath": "/path/to/file.cpp",
    "modifiedContent": "..."
})
```

**发送流程：**
1. `send_vscode_request()` 构建 JSON-RPC 请求
2. 通过 `print()` 输出到 stdout
3. VSCode extension 从 CLI 的 stdout 读取
4. Extension 处理请求并执行 VSCode API
5. Extension 将响应写入 CLI 的 stdin
6. RPC 客户端从 stdin 读取响应
7. 返回结果给调用者

### 3. 请求/响应格式

**请求 (CLI → VSCode)：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "getActiveFile",
  "params": {}
}
```

**响应 (VSCode → CLI)：**
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

**错误响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error"
  }
}
```

## 模块结构

### client.py

**核心类：**

#### `JsonRpcClient`
- 管理请求/响应生命周期
- 后台线程监听 stdin
- 超时处理和错误处理

**关键方法：**
- `start()` - 启动响应监听线程
- `send_request(method, params, timeout)` - 发送请求并等待响应
- `_listen_for_responses()` - 后台监听 stdin

**全局函数：**
- `get_client()` - 获取或创建全局客户端实例
- `is_vscode_mode()` - 检测是否在 VSCode 模式
- `send_vscode_request(method, params)` - 便捷发送请求

### 与 backend/tools/vscode.py 的集成

每个工具函数都实现了双模式：

```python
def get_active_file():
    if is_vscode_mode():
        # 使用实际 RPC 通信
        return send_vscode_request("getActiveFile", {})
    else:
        # 使用 Mock 模式（用于测试）
        return mock_response()
```

## 使用示例

### 从命令行测试

```bash
# 1. 启动 VSCode extension (模拟)
# 在一个终端：
node vscode-extension/out/test-server.js

# 2. 在另一个终端启动 CLI
export VSCODE_INTEGRATION=true
python3 -m backend.cli
```

### 在 VSCode extension 中使用

```typescript
// 启动 CLI 进程
const cli = spawn('python3', ['-m', 'backend.cli'], {
    env: {
        ...process.env,
        VSCODE_INTEGRATION: 'true'
    }
});

// 监听请求
cli.stdout.on('data', (data) => {
    const request = JSON.parse(data.toString());
    const response = await handleRequest(request);
    cli.stdin.write(JSON.stringify(response) + '\n');
});
```

## 工作模式

### 模式 1：Mock 模式（默认）

不设置 `VSCODE_INTEGRATION` 时使用 mock 数据：

```bash
python3 -m backend.cli
> /testvs
# 显示 mock 数据
```

### 模式 2：VSCode 集成模式

由 VSCode extension 启动 CLI 时：

```bash
VSCODE_INTEGRATION=true python3 -m backend.cli
```

**自动行为：**
- ✅ 启动 RPC 客户端
- ✅ 后台监听 stdin
- ✅ 所有 VSCode 工具使用实际通信
- ✅ 显示 "RPC 客户端已启动" 提示

## 线程模型

```
Main Thread               Background Thread
───────────                ────────────────
CLI Init
├── create RPC client
├── start()  ────────────►  _listen_for_responses()
│                           └── while running:
│                                 ├── readline(stdin)
│                                 ├── parse JSON
│                                 └── put to response queue
│
User Input
├── call get_active_file()
│   ├── send_vscode_request()
│   │   ├── print to stdout  ─►  VSCode reads
│   │   │   ◄─────────────────  VSCode writes to stdin
│   │   └── wait for response  ◄─  Background thread reads
│   │       (from queue)          and puts in queue
│   └── return result
└── continue
```

## 超时处理

默认超时 10 秒：

```python
response = send_vscode_request("getActiveFile", {}, timeout=5.0)
```

**超时时：**
- 抛出 `TimeoutError`
- 清理待处理请求队列
- 不影响后续请求

## 错误处理

### JSON 解析错误

非 JSON 行（如 CLI 输出）会被忽略：

```python
# 只处理以 { 开头的行
if not line.startswith('{'):
    continue
```

### 请求超时

```python
try:
    result = send_vscode_request("method", {})
except TimeoutError:
    print("VSCode 没有响应")
```

### 连接错误

如果 VSCode extension 崩溃或关闭：
- 后台线程继续运行
- 请求会超时
- 可以通过 `client.stop()` 清理

## 调试

启用调试输出：

```bash
export DEBUG_AGENT=1
export VSCODE_INTEGRATION=true
python3 -m backend.cli
```

**调试信息：**
```
[RPC CLIENT] Sent request: getActiveFile
[RPC CLIENT] Error reading response: ...
```

## 性能优化

### 请求队列

- 每个请求有独立的响应队列
- 支持并发请求（不同 ID）
- 响应按 ID 路由

### 线程安全

- 使用 `threading.Lock` 保护共享状态
- 响应队列使用 `queue.Queue`（线程安全）

### 内存管理

- 请求完成后自动清理队列
- 超时请求自动从待处理列表移除

## 测试

运行集成测试：

```bash
python3 tests/test_rpc_integration.py
```

**测试覆盖：**
- ✅ RPC 客户端基础功能
- ✅ VSCode 模式检测
- ✅ Mock 模式工具调用
- ✅ CLI 初始化

## 常见问题

### Q: 为什么使用 stdout/stdin 而不是 Socket？

**A:** VSCode extension API 使用子进程通信，stdout/stdin 是最简单可靠的方式。未来可以添加 Socket 模式作为可选项。

### Q: 如果 stdin 阻塞怎么办？

**A:** 后台线程处理 stdin，主线程不会阻塞。使用 Queue 传递响应。

### Q: 支持并发请求吗？

**A:** 是的。每个请求有唯一 ID 和独立响应队列，可以并发发送。

### Q: Mock 模式和实际模式如何切换？

**A:** 工具函数自动检测 `VSCODE_INTEGRATION` 环境变量，无需手动切换。

## 扩展

### 添加新的 RPC 方法

1. 在 `backend/tools/vscode.py` 添加工具函数：

```python
def new_operation(param1, param2):
    if is_vscode_mode():
        return send_vscode_request("newOperation", {
            "param1": param1,
            "param2": param2
        })
    else:
        return mock_response()
```

2. 在 VSCode extension 的 `jsonRpcServer.ts` 添加处理器：

```typescript
private handleNewOperation(params: any) {
    // 实现 VSCode 操作
    return { success: true };
}
```

3. 注册方法：

```typescript
this.requestHandlers.set('newOperation', this.handleNewOperation.bind(this));
```

## 参考

- JSON-RPC 2.0 规范: https://www.jsonrpc.org/specification
- VSCode Extension API: https://code.visualstudio.com/api
- Python Threading: https://docs.python.org/3/library/threading.html
