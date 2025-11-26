# VSCode 扩展测试

此目录包含与 VSCode 扩展集成相关的测试。

## 测试文件

### test_rpc_integration.py
RPC 客户端基础功能测试

**测试内容:**
- RPC 客户端初始化
- 请求 ID 生成
- VSCode 模式检测（环境变量）
- VSCode 工具 Mock 模式
- CLI VSCode 模式初始化

**运行:**
```bash
python3 tests/extension/test_rpc_integration.py
```

### test_vscode.py
VSCode 工具函数测试（Mock 模式）

**测试内容:**
- Mock 数据可用性
- get_active_file() - 获取当前文件
- get_selection() - 获取选中文本
- show_diff() - 显示差异
- apply_changes() - 应用更改
- open_file() - 打开文件
- get_workspace_folder() - 获取工作区

**运行:**
```bash
python3 tests/extension/test_vscode.py
```

### test_rpc_e2e_simple.py
RPC E2E 集成测试（不需要真实 VSCode）

**测试内容:**
- RPC/Mock 模式自动切换
- 环境变量大小写不敏感性
- 所有 VSCode 工具函数集成测试
- 工具函数 API 验证

**运行:**
```bash
python3 tests/extension/test_rpc_e2e_simple.py
```

## 快速运行所有测试

使用专用的 RPC 测试运行器：

```bash
python3 tests/run_rpc_tests.py
```

## 测试模式

### Mock 模式（默认）
不需要真实的 VSCode 环境，使用模拟数据进行测试。

```bash
# 确保环境变量未设置
unset VSCODE_INTEGRATION

# 运行测试
python3 tests/run_rpc_tests.py
```

### RPC 模式（需要 VSCode 扩展）
测试真实的 RPC 通信，需要运行 VSCode 扩展。

```bash
# 在 VSCode 中启动 CLI
# Cmd+Shift+P → "Claude-Qwen: Start Assistant"

# 在 CLI 中运行
/testvs
```

## 测试覆盖率

当前测试覆盖：
- ✅ RPC 客户端初始化和线程管理
- ✅ JSON-RPC 请求格式化
- ✅ VSCode 模式自动检测
- ✅ Mock 数据回退机制
- ✅ 所有 6 个 VSCode 工具函数

## 相关文档

- [RPC 测试指南](../../docs/RPC_TESTING.md) - 完整的 RPC 测试文档
- [VSCode 扩展](../../vscode-extension/) - VSCode 扩展源码
- [启动模式](../../docs/LAUNCH_MODES.md) - CLI 和 VSCode 的启动方式

## 添加新测试

要添加新的 VSCode 集成测试：

1. 在此目录创建新的测试文件
2. 确保导入路径正确：
   ```python
   import sys
   import os
   project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   sys.path.insert(0, project_root)
   ```
3. 添加到 `tests/run_rpc_tests.py` 的测试列表
4. 运行测试验证
