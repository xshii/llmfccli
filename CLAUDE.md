# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Claude-Qwen 是一个专为 C/C++ 开发设计的开源 AI 编程助手。通过 Ollama 本地部署 Qwen3 模型，提供智能代码补全、错误修复和测试生成功能。设计灵感来自 Anthropic 的 Claude Code 架构，通过本地部署实现完全的数据隐私保护。

## 开发命令

### 安装和设置
```bash
# 安装依赖
pip install -e .[dev]

# 拉取 Qwen3 模型（必需）
ollama pull qwen3
```

### 运行应用
```bash
# 启动交互式 CLI
claude-qwen

# 指定项目根目录启动
claude-qwen --root /path/to/project
```

### 测试
```bash
# 快速单元测试（几秒钟，不需要 LLM）
python3 tests/run_unit_tests.py

# 运行所有测试（单元测试 + 端到端测试）
python3 tests/run_all_tests.py

# 运行单个测试
python3 tests/unit/test_tools_only.py
python3 tests/e2e/test_case_1.py
```

### 代码质量
```bash
# 格式化代码
black backend/ tests/ --line-length 100

# 代码检查
ruff check backend/ tests/

# 类型检查
mypy backend/
```

## 架构设计

### 两阶段 Agent 系统

系统采用两阶段 Agent 设计实现自主任务执行：

1. **意图识别阶段** (`backend/agent/planner.py`)：分析用户请求，在执行前确定任务类型、所需工具和复杂度。

2. **自主执行阶段** (`backend/agent/loop.py`)：主 Agent 循环，协调 LLM 和工具调用直到任务完成（最多 20 次迭代）。

### 分类 Token 预算的上下文管理

系统通过 `config/token_budget.yaml` 定义的分类预算管理 128K token 上下文窗口：

- **active_files** (25%)：当前打开的文件和单元测试（不可压缩）
- **processed_files** (15%)：已处理文件的摘要
- **project_structure** (5%)：目录树（不可压缩）
- **compressed_history** (30%)：压缩后的对话历史
- **recent_messages** (25%)：最近的未压缩消息

当容量达到 85% 时自动触发压缩，目标压缩至 60%。`backend/agent/context.py` 模块通过调用 LLM 进行智能压缩，选择性保留重要信息。

### 工具系统

通过 `backend/agent/tools.py` 的 `ToolRegistry` 模式注册工具：

- **文件系统工具** (`backend/tools/filesystem.py`)：view_file, edit_file, create_file, grep_search, list_dir
- **执行器工具**（计划中）：bash_run, cmake_build, run_tests
- **分析器工具**（计划中）：parse_cpp, find_functions, get_dependencies
- **VSCode 集成**（计划中）：get_active_file, show_diff, apply_changes

工具 schema 遵循 OpenAI 函数调用格式。所有工具都执行安全检查以防止路径遍历攻击。

### LLM 客户端架构

`backend/llm/client.py` 使用 subprocess 调用 curl 实现 Ollama 客户端（而非 Python SDK）。主要特性：

- 流式响应与提前停止 token 检测
- 指数退避自动重试（3 次尝试）
- 支持 OpenAI 格式的工具/函数调用
- 通过专用 LLM 调用进行上下文压缩

配置从 `config/ollama.yaml` 加载，包括 temperature (0.1)、top_p (0.9) 和上下文窗口 (131072 tokens) 等参数。

### 编译错误恢复循环

Agent 实现编译-修复-重试循环（最多 3 次尝试）处理 C++ 编译错误：

1. 执行 cmake/make 构建
2. 解析编译器错误（gcc/clang/MSVC 格式）
3. 使用 LLM 生成修复方案
4. 通过 edit_file 工具应用修复
5. 重试编译
6. 如达到最大重试次数，保存会话状态供人工审查

会话恢复由 `backend/agent/loop.py::save_session()` 处理。

## 配置文件

- `config/token_budget.yaml`：Token 分配和压缩阈值
- `config/ollama.yaml`：模型参数和重试配置
- `config/tools.yaml`：工具定义、白名单和安全限制

## 测试套件结构

测试分为两类：

### 单元测试 (`tests/unit/`)
快速测试，不依赖 LLM，用于验证基础功能：

1. **test_tools_only.py**：文件系统工具测试（grep_search, view_file, edit_file）
2. **test_ollama_hello.py**：Ollama 连接和基础通信测试
3. **test_basic.py**：工具注册和集成测试

### 端到端测试 (`tests/e2e/`)
完整流程测试，需要 LLM 参与，验证核心功能：

1. **test_case_1.py**：跨目录文件定位 + 功能添加
2. **test_case_2.py**：编译错误自动修复循环
3. **test_case_3.py**：GTest 单元测试生成
4. **test_case_4.py**：带依赖分析的集成测试生成
5. **test_case_5.py**：多轮对话上下文保持
6. **test_case_6.py**：错误恢复和会话保存机制

所有测试使用 `tests/fixtures/` 中包含故意错误的 C++ 代码作为 fixtures。

## 关键实现细节

### Edit File 策略
`edit_file` 工具使用精确字符串替换，要求 `old_str` 在文件中恰好出现一次。这防止了歧义编辑并确保精确修改。

### 初始化时预热
`OllamaClient` 在初始化时发送预热请求（"hi"）将模型预加载到内存，减少后续请求的延迟。

### 停止 Token 处理
客户端监控流式响应中的停止 token（`<|endoftext|>`, `<|im_end|>`, `Human:`）并提前终止，防止模型生成不需要的续写。

### 安全边界
所有文件系统工具验证路径保持在项目根目录内以防止目录遍历攻击。Bash 命令在 `config/tools.yaml` 中白名单化。

## 开发进度

当前实现状态：
- [x] 测试用例和测试项目
- [x] 项目结构和配置
- [x] Token 计数器 (`backend/agent/token_counter.py`)
- [x] Ollama 客户端 (`backend/llm/client.py`)
- [x] 文件系统工具 (`backend/tools/filesystem.py`)
- [x] Agent 主循环 (`backend/agent/loop.py`)
- [x] 上下文压缩 (`backend/agent/context.py`)
- [x] CLI 界面 (`backend/cli.py`)
- [ ] 执行器工具 (bash, cmake, ctest)
- [ ] 分析器工具 (tree-sitter 集成)
- [ ] VSCode 插件

## 远程 Ollama 配置

如果 Ollama 服务部署在远程服务器，需要配置 SSH 隧道：

### SSH 配置文件

在 `~/.ssh/config` 中添加：

```
Host ollama-tunnel
    HostName 192.168.3.41
    User gakki
    LocalForward 11434 localhost:11434
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 使用步骤

```bash
# 1. 生成 SSH 密钥（如果没有）
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# 2. 复制公钥到远程服务器
ssh-copy-id gakki@192.168.3.41

# 3. 启动后台隧道
ssh -fN ollama-tunnel

# 4. 验证隧道
ps aux | grep "ssh.*ollama-tunnel"
curl http://localhost:11434/api/tags

# 5. 停止隧道
pkill -f "ssh.*ollama-tunnel"
```

### 配置文件设置

- `config/ollama.yaml` 中的 `base_url` 设置为 `http://localhost:11434`
- `model` 设置为 `qwen3:latest`（完整模型名称包含标签）

### 依赖安装

```bash
# 安装所有依赖
pip3 install -e .[dev]

# 主要依赖
pip3 install tiktoken  # Token 计数
```

## VS Code 调试配置

项目包含 `.vscode/launch.json` 配置，提供以下调试选项：

- **Run All Unit Tests** - 运行所有单元测试（推荐用于快速验证）
- **Run All Tests (Unit + E2E)** - 运行完整测试套件
- **Test: Filesystem Tools** - 单独测试文件系统工具
- **Test: Ollama Connection** - 单独测试 Ollama 连接
- **Test: Basic** - 基础功能测试
- **Claude-Qwen CLI** - 启动 CLI 应用
- **Python: Current File** - 运行当前文件

使用方法：`Cmd+Shift+D` 打开 Run and Debug 面板，选择配置后按 `F5` 运行。

## 入口点

- **CLI**：`backend/cli.py::main()` - 交互式命令行界面
- **Agent**：`backend/agent/loop.py::AgentLoop.run()` - 核心执行循环
- **单元测试**：`tests/run_unit_tests.py` - 快速单元测试运行器
- **完整测试**：`tests/run_all_tests.py` - 完整测试套件运行器
