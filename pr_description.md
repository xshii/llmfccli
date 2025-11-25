## 功能概述

本 PR 实现了多个重要功能改进，显著提升了 Claude-Qwen 的用户体验和安全性：

### 1. 🔐 工具执行确认系统（核心功能）

为 CLI 模式添加了用户确认机制，在执行工具前要求用户批准，防止意外或危险操作。

**功能特性**：
- ✅ 三种确认选项：
  - **本次允许** - 仅本次执行允许
  - **始终允许** - 该工具/命令永久允许
  - **拒绝并停止** - 拒绝执行并停止任务
- ✅ 工具分类管理（filesystem、executor、analyzer）
- ✅ bash_run 特殊处理：按命令名称单独确认（如 `ls` 允许后，`ls -la` 和 `ls /tmp` 都无需再次确认，但 `pwd` 仍需确认）
- ✅ 持久化存储到 `~/.claude_qwen_confirmations.json`
- ✅ 新增 `/reset-confirmations` 命令重置所有确认

**实现文件**：
- `backend/agent/tool_confirmation.py` - 核心确认逻辑（180 行）
- `backend/agent/loop.py` - AgentLoop 集成
- `backend/cli.py` - CLI 用户交互界面
- `test_confirmation.py` - 完整测试套件（所有测试通过 ✅）

**用户体验**：
```
┌── 需要确认 ────────────────────────────┐
│ ⚠ 工具执行确认                         │
│                                         │
│ 工具: bash_run                         │
│ 类别: executor                         │
│ 命令: ls -la                           │
│                                         │
│ 参数:                                   │
│   • command: ls -la                    │
│   • project_root: /home/user/project   │
└─────────────────────────────────────────┘

选择操作:
  1 - 本次允许 (ALLOW_ONCE)
  2 - 始终允许 (ALLOW_ALWAYS)
  3 - 拒绝并停止 (DENY)

请输入选择 (1/2/3):
```

### 2. 🌊 流式输出支持

**功能特性**：
- ✅ 实时显示 LLM 响应内容（类似 ChatGPT 效果）
- ✅ 通过 `config/ollama.yaml` 配置 `stream: true/false` 切换模式
- ✅ 流式模式：实时输出，提升交互体验
- ✅ 非流式模式：等待完整响应，以 Panel 形式展示

**实现文件**：
- `backend/llm/client.py` - 添加 `stream` 和 `on_chunk` 参数
- `backend/agent/loop.py` - 传递流式参数
- `backend/cli.py` - 实现实时打印回调

### 3. 🔧 工具调用 ID 优化

**改进前**：`view_file_1732512345_0`（包含时间戳，冗长）
**改进后**：`view_file_0`（简洁明了）

格式：`{function_name}_{index}`

### 4. 📋 执行器工具 TODO 打印

为所有执行器工具添加详细的进度打印：
- `bash_run` - 显示命令、工作目录、超时设置、执行结果
- `cmake_build` - 显示步骤进度（1/4, 2/4...）
- `run_tests` - 显示测试结果汇总

### 5. 🧹 测试 Fixtures 清理

将测试用的 C++ 示例文件加入 `.gitignore`，保持仓库整洁（文件仍保留在本地用于测试）。

## 测试验证

### 单元测试
```bash
python3 test_confirmation.py
```
**结果**：✅ 所有 4 个测试通过
- ✅ 基础确认流程
- ✅ bash_run 按命令确认
- ✅ 工具分类
- ✅ 持久化存储

### 手动测试
- ✅ 确认提示界面正常显示
- ✅ 三种确认选项均正常工作
- ✅ 持久化存储和加载正常
- ✅ `/reset-confirmations` 命令正常
- ✅ 流式输出实时显示正常
- ✅ 配置切换正常工作

## 影响范围

- **向后兼容**：✅ 完全兼容，现有代码无需修改
- **性能影响**：✅ 无明显性能影响
- **依赖变更**：❌ 无新增外部依赖

## 文件变更统计

```
新增文件：
  backend/agent/tool_confirmation.py  (180 行)
  test_confirmation.py                (197 行)

修改文件：
  backend/agent/loop.py               (+46 行)
  backend/cli.py                      (+90 行)
  .gitignore                          (+6 行)

删除文件：
  tests/fixtures/**/*.cpp             (加入 .gitignore)
```

## 使用说明

### 启用/禁用流式输出
编辑 `config/ollama.yaml`：
```yaml
ollama:
  stream: true   # 启用流式输出
  # stream: false  # 使用完整响应模式
```

### 管理工具确认
```bash
# 查看帮助
/help

# 重置所有确认
/reset-confirmations
```

## 相关 Issue

解决了用户关于工具执行安全性和实时输出体验的需求。
