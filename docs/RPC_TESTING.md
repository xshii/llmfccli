# RPC 通信测试指南

本文档说明如何测试 CLI 与 VSCode 扩展之间的 JSON-RPC 通信。

## 测试类型

### 1. 单元测试（不需要 VSCode）

这些测试验证 RPC 客户端基础功能，使用 Mock 数据，不需要真实的 VSCode 环境。

#### 运行基础 RPC 测试

```bash
# RPC 客户端基础功能测试
python3 tests/test_rpc_integration.py

# VSCode 工具 Mock 模式测试
python3 tests/unit/test_vscode.py

# RPC E2E 集成测试（模拟 VSCode 响应）
python3 tests/test_rpc_e2e_simple.py
```

#### 测试覆盖

**test_rpc_integration.py**:
- RPC 客户端初始化
- 请求 ID 生成
- VSCode 模式检测（环境变量）
- VSCode 工具 Mock 模式
- CLI VSCode 模式初始化

**test_vscode.py**:
- Mock 数据可用性
- get_active_file() - 获取当前文件
- get_selection() - 获取选中文本
- show_diff() - 显示差异
- apply_changes() - 应用更改
- open_file() - 打开文件
- get_workspace_folder() - 获取工作区

**test_rpc_e2e_simple.py**:
- RPC/Mock 模式自动切换
- 所有 VSCode 工具函数集成测试
- 环境变量大小写不敏感性
- 工具函数 API 验证

### 2. 交互式 E2E 测试（需要 VSCode 扩展）

真实的端到端测试需要实际的 VSCode 扩展。

#### 准备工作

1. **构建 VSCode 扩展**

```bash
cd vscode-extension

# 安装依赖
npm install

# 编译 TypeScript
npm run compile

# 打包成 .vsix（可选）
npm run package
```

2. **安装扩展**

```bash
# 方法 1: 从源码安装（开发模式）
# 在 VSCode 中按 F5，会打开扩展开发主机

# 方法 2: 安装 .vsix 包
code --install-extension claude-qwen-0.1.0.vsix
```

#### 手动 E2E 测试流程

1. **从 VSCode 启动 CLI**

```bash
# 在 VSCode 中打开项目
code /path/to/your/cpp/project

# 按 Cmd+Shift+P (Mac) 或 Ctrl+Shift+P (Windows/Linux)
# 输入: Claude-Qwen: Start Assistant
# 这会启动 CLI 并设置 VSCODE_INTEGRATION=true
```

2. **在 CLI 中测试 VSCode 集成**

```bash
# 在打开的 CLI 终端中输入
/testvs

# 应该看到:
# ✓ 通信模式: VSCode RPC
# ✓ 所有 VSCode 工具测试通过
```

3. **测试双向通信**

在 CLI 中执行以下操作，验证 VSCode 响应：

```bash
# 获取当前活动文件
> 请问当前打开的是什么文件？

# 查看选中的代码
> 我选中的代码是什么？

# 显示差异（如果实现了编辑功能）
> 请修改这个函数...
```

### 3. 自动化 E2E 测试（进阶）

对于 CI/CD 集成，可以使用无头模式运行 VSCode：

```bash
# 使用 VSCode CLI 在无头模式下测试扩展
code --extensionDevelopmentPath=./vscode-extension \
     --extensionTestsPath=./vscode-extension/src/test \
     --disable-extensions
```

## RPC 通信架构

### 通信流程

```
CLI (RPC Client)                    VSCode Extension (RPC Server)
================                    =============================

1. 启动时检测环境变量
   VSCODE_INTEGRATION=true

2. 初始化 RPC 客户端
   - 启动后台监听线程
   - 线程读取 stdin

3. 调用 VSCode 工具                → 4. 扩展从 CLI stdout 读取
   例: get_active_file()

5. 发送 JSON-RPC 请求             → 6. 解析请求
   print(json) → stdout               {
                                        "jsonrpc": "2.0",
                                        "id": 1,
                                        "method": "getActiveFile",
                                        "params": {}
                                      }

                                    7. 调用 VSCode API
                                       vscode.window.activeTextEditor

                                    8. 构造响应
                                       {
                                         "jsonrpc": "2.0",
                                         "id": 1,
                                         "result": {...}
                                       }

9. 后台线程读取响应              ← 10. 写入到 CLI stdin
   stdin.readline()

11. 将响应放入队列
    pending_requests[1].put(response)

12. 主线程获取响应
    return result
```

### Mock 模式（无 VSCode）

当 `VSCODE_INTEGRATION` 环境变量未设置时：

```python
from backend.tools import vscode
from backend.rpc.client import is_vscode_mode

if is_vscode_mode():
    # 使用真实 RPC 通信
    response = send_vscode_request("getActiveFile", {})
else:
    # 使用 Mock 数据
    response = _mock_response("getActiveFile", {})
```

## 调试 RPC 通信

### 启用调试日志

```bash
# 设置调试环境变量
export DEBUG_AGENT=1
export VSCODE_INTEGRATION=true

# 启动 CLI
python3 -m backend.cli

# 查看 RPC 日志（stderr）
# [RPC CLIENT] Sent request: getActiveFile
# [RPC CLIENT] Received response for request 1
```

### 常见问题

#### 1. CLI 没有检测到 VSCode 模式

**症状**: `/testvs` 显示 "通信模式: Mock"

**解决方案**:
```bash
# 检查环境变量
echo $VSCODE_INTEGRATION

# 应该输出: true

# 如果没有，手动设置
export VSCODE_INTEGRATION=true
```

#### 2. RPC 请求超时

**症状**: `TimeoutError: No response for method 'xxx' after 10s`

**可能原因**:
- VSCode 扩展未运行
- stdin/stdout 管道断开
- 后台监听线程未启动

**调试步骤**:
```python
# 检查 RPC 客户端状态
from backend.rpc.client import get_client

client = get_client()
print(f"Running: {client.running}")
print(f"Thread alive: {client.response_listener_thread.is_alive()}")
```

#### 3. JSON 解析错误

**症状**: `JSONDecodeError: Expecting value`

**可能原因**:
- stdout 包含非 JSON 输出（如 print 语句）
- 响应格式不正确

**解决方案**:
- 确保所有用户输出使用 `sys.stderr.write()` 而非 `print()`
- RPC 通信使用 `print()` 输出到 stdout

## 编写新的 RPC 工具

### 1. 在 `backend/tools/vscode.py` 中添加工具函数

```python
def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """新的 VSCode 工具"""
    from backend.rpc.client import is_vscode_mode, send_vscode_request

    params = {
        "param1": param1,
        "param2": param2
    }

    if is_vscode_mode():
        # RPC 模式
        response = send_vscode_request("myNewMethod", params)
        if response.get("success"):
            return response["data"]
        else:
            raise VSCodeError(response.get("error"))
    else:
        # Mock 模式
        return {
            "success": True,
            "data": "Mock result"
        }
```

### 2. 在 VSCode 扩展中实现对应的处理器

编辑 `vscode-extension/src/jsonRpcServer.ts`:

```typescript
private registerHandlers() {
    // ... 现有处理器

    this.requestHandlers.set('myNewMethod',
        this.handleMyNewMethod.bind(this));
}

private async handleMyNewMethod(params: any): Promise<any> {
    const { param1, param2 } = params;

    // 调用 VSCode API
    const result = await vscode.window.showInputBox({
        prompt: `Processing ${param1} with ${param2}`
    });

    return {
        success: true,
        data: result
    };
}
```

### 3. 添加 Mock 数据

在 `backend/tools/vscode.py` 的 `MOCK_DATA` 中：

```python
MOCK_DATA = {
    # ... 现有数据
    "my_new_tool_result": {
        "success": True,
        "data": "Mock result for testing"
    }
}
```

### 4. 编写测试

在 `tests/unit/test_vscode.py` 中：

```python
def test_my_new_tool():
    """Test my new tool"""
    # Ensure mock mode
    if 'VSCODE_INTEGRATION' in os.environ:
        del os.environ['VSCODE_INTEGRATION']

    result = vscode.my_new_tool("test", 42)
    assert result['success'] == True
    assert 'data' in result
```

## 性能指标

### 典型 RPC 延迟

- **Mock 模式**: < 1ms
- **RPC 模式（本地）**: 10-50ms
- **超时设置**: 10秒（可配置）

### 并发限制

- RPC 客户端支持并发请求
- 每个请求有独立的响应队列
- 无并发数量限制（受操作系统限制）

## 参考资料

- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [VSCode Extension API](https://code.visualstudio.com/api)
- [Python subprocess 文档](https://docs.python.org/3/library/subprocess.html)
- [Threading 文档](https://docs.python.org/3/library/threading.html)
