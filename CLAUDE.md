# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Claude-Qwen 是一个专为 C/C++ 开发设计的开源 AI 编程助手。通过 Ollama 本地部署大模型（推荐 GLM-4.7-flash），提供智能代码补全、错误修复和测试生成功能。设计灵感来自 Anthropic 的 Claude Code 架构，通过本地部署实现完全的数据隐私保护。

## 开发命令

### 安装和设置
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .[dev]

# 拉取模型（推荐 GLM-4.7-flash）
ollama pull glm-4.7-flash
```

### 运行应用
```bash
# 启动交互式 CLI
claude-qwen

# 指定项目根目录启动
claude-qwen --root /path/to/project

# 运行 benchmark 测试
claude-qwen --test
claude-qwen --test -m qwen3:latest
```

### 测试
```bash
# 快速单元测试（几秒钟，不需要 LLM）
python3 tests/run_unit_tests.py

# 运行单个 benchmark
python3 tests/benchmark/run_single.py simple_edit
python3 tests/benchmark/run_single.py write_test

# 端到端测试（需要 LLM）
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

### Agent 系统

系统采用 Agent 设计实现自主任务执行：

- **主循环** (`backend/agent/loop.py`)：协调 LLM 和工具调用直到任务完成（最多 20 次迭代）
- **设计模式** (`backend/agent/patterns/`)：Chain of Responsibility、Observer、Command、Pipeline

### 分类 Token 预算的上下文管理

系统通过 `config/token_budget.yaml` 定义的分类预算管理上下文窗口：

- **active_files** (25%)：当前打开的文件和单元测试（不可压缩）
- **processed_files** (15%)：已处理文件的摘要
- **project_structure** (5%)：目录树（不可压缩）
- **compressed_history** (30%)：压缩后的对话历史
- **recent_messages** (25%)：最近的未压缩消息

当容量达到 85% 时自动触发压缩，目标压缩至 60%。

### 工具系统

通过 `backend/agent/tools/registry.py` 的 `ToolRegistry` 模式注册工具：

- **文件系统工具** (`backend/tools/filesystem_tools/`)：view_file, edit_file, create_file, grep_search, list_dir
- **执行器工具** (`backend/tools/executor_tools/`)：bash_run, cmake_build, run_tests
- **Agent 工具** (`backend/tools/agent_tools/`)：todo_write
- **Git 工具** (`backend/tools/git_tools/`)：git 操作

工具 schema 遵循 OpenAI 函数调用格式。所有工具都执行安全检查以防止路径遍历攻击。

### LLM 客户端架构

`backend/llm/ollama.py` 使用 subprocess 调用 curl 实现 Ollama 客户端。主要特性：

- 流式响应与提前停止 token 检测
- 指数退避自动重试（3 次尝试）
- 支持 OpenAI 格式的工具/函数调用
- 思考模式支持（GLM-4.7 think mode）

配置从 `config/llm.yaml` 加载，包括 model、timeout、stream、think 等参数。

## 配置文件

- `config/llm.yaml`：LLM 后端配置（模型、think mode、timeout）
- `config/token_budget.yaml`：Token 分配和压缩阈值
- `config/tools.yaml`：工具定义、白名单和安全限制

## 测试套件结构

### 单元测试 (`tests/unit/`)
快速测试，不依赖 LLM，用于验证基础功能。

### 端到端测试 (`tests/e2e/`)
完整流程测试，需要 LLM 参与，验证核心功能。

### Benchmark (`tests/benchmark/`)
性能基准测试，评估模型在不同任务上的表现：
- `simple_edit`：简单代码修改
- `code_search`：代码搜索
- `file_location`：文件定位与功能实现
- `write_test`：编写测试并调试

## 关键实现细节

### Edit File 策略
`edit_file` 工具使用精确字符串替换，要求 `old_str` 在文件中恰好出现一次。

### 初始化时预热
`OllamaClient` 在初始化时发送预热请求将模型预加载到内存。

### 安全边界
所有文件系统工具验证路径保持在项目根目录内以防止目录遍历攻击。

## 开发进度

当前实现状态（v1.0.0）：
- [x] 项目结构和配置
- [x] Token 计数器 (`backend/agent/token_counter/`)
- [x] Ollama 客户端 (`backend/llm/ollama.py`)
- [x] 文件系统工具 (`backend/tools/filesystem_tools/`)
- [x] 执行器工具 (`backend/tools/executor_tools/`)
- [x] Agent 主循环 (`backend/agent/loop.py`)
- [x] 上下文压缩 (`backend/llm/compression.py`)
- [x] CLI 界面 (`backend/cli/`)
- [x] Benchmark 框架 (`tests/benchmark/`)
- [x] GLM-4.7 思考模式支持
- [ ] VSCode 插件

## 入口点

- **CLI**：`backend/cli/main.py::main()` - 交互式命令行界面
- **Agent**：`backend/agent/loop.py::AgentLoop.run()` - 核心执行循环
- **单元测试**：`tests/run_unit_tests.py` - 快速单元测试运行器
- **Benchmark**：`tests/benchmark/run_benchmark.py` - 性能基准测试

## 快速入门

详见 [QUICKSTART.md](QUICKSTART.md)
