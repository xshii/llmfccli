# Claude-Qwen

基于 Ollama 本地部署的 AI 编程助手，支持 Qwen3-coder、GLM-4.7 等模型。

## 项目介绍

Claude-Qwen 是一个开源的 AI 编程助手，专注于 C/C++ 项目开发。通过 Ollama 本地部署大模型（推荐 Qwen3-coder），提供智能代码补全、错误修复、测试生成等功能。

**设计灵感**: 参考 Anthropic Claude Code 的工作机制，结合 Ollama 的本地部署优势。

**核心特性**:
- 🔍 智能文件导航 - 跨目录搜索定位代码
- 🔧 自动编译修复 - 识别并修复编译错误
- ✅ 测试用例生成 - 自动生成 GTest 单元测试和集成测试
- 💾 上下文管理 - Token 预算分配和智能压缩
- 🔄 VSCode 集成 - Diff 对比和一键应用修改
- 🎨 CLI Diff - 终端彩色差异显示（VSCode 不可用时的替代方案）

## 项目优势

### 1. 完全本地化
- 数据不上传云端，保护代码隐私
- 无需 API Key，零使用成本
- 离线可用，不依赖网络

### 2. C/C++ 专精
- 深度集成 CMake 和 GTest
- 理解 C++ 编译错误格式（gcc/clang/MSVC）
- 使用 tree-sitter 准确解析代码结构

### 3. 智能上下文管理
- 128k 超长上下文窗口
- 分类 token 预算，优先保留关键信息
- 自动压缩历史对话，保持流畅体验

### 4. 自主决策能力
- 两阶段 Agent 设计（意图识别 + 自主执行）
- 动态调整工具调用策略
- 编译-修复循环，最多 3 次重试

## 快速入门

### 环境要求

- Python 3.10+
- [Ollama](https://ollama.ai/) 已安装
- CMake 3.15+（仅用于测试项目构建）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/claude-qwen.git
cd claude-qwen

# 2. 安装依赖
pip install -e .[dev]

# 3. 拉取模型（推荐 qwen3-coder）
ollama pull qwen3-coder

# 4. 验证安装（运行单元测试）
python3 tests/run_unit_tests.py
```

### 基本使用

```bash
# 启动 CLI 交互模式
claude-qwen

# 常用命令示例
> 找到 network_handler.cpp 并添加超时重试机制
> 编译项目并修复所有错误
> 为当前文件生成单元测试
> 分析 HTTP 模块的依赖关系
```

### 配置说明

修改 `config/` 目录下的配置文件：

- `llm.yaml` - 模型配置（model, think mode, timeout 等）
- `token_budget.yaml` - Token 分配策略和压缩阈值
- `tools.yaml` - 工具白名单和安全限制
- `feature.yaml` - 功能开关（diff 显示、重试策略、会话恢复等）

## 测试用例

项目包含 6 个完整的端到端测试：

| 测试用例 | 说明 | 验证点 |
|---------|------|--------|
| test_case_1 | 跨目录文件定位 + 功能添加 | grep 搜索、代码插入、风格保持 |
| test_case_2 | 编译错误自动修复循环 | 错误解析、循环修复、终止条件 |
| test_case_3 | 单元测试生成 | GTest 框架、边界测试、函数覆盖 |
| test_case_4 | 模块集成测试生成 | 依赖分析、Mock 策略、边界行为 |
| test_case_5 | 上下文保持 | 多轮对话、历史记忆 |
| test_case_6 | 错误恢复机制 | 最大重试、Session 保存 |

运行测试：
```bash
# 单元测试（快速，不需要 LLM）
python3 tests/run_unit_tests.py

# 端到端测试（需要 LLM）
python3 tests/e2e/test_case_1.py

# Benchmark 测试
claude-qwen --test
```

## 项目结构

```
claude-qwen/
├── backend/              # Python 后端
│   ├── agent/           # Agent 核心逻辑
│   ├── llm/             # LLM 客户端（Ollama/OpenAI）
│   ├── tools/           # 工具系统（文件、编译、分析）
│   ├── cli/             # 命令行界面
│   └── utils/           # 工具函数
├── tests/               # 测试用例
│   ├── unit/            # 单元测试
│   ├── e2e/             # 端到端测试
│   ├── benchmark/       # 性能基准测试
│   └── fixtures/        # 测试项目
├── config/              # 配置文件
├── vscode-extension/    # VSCode 插件
├── QUICKSTART.md        # 快速入门指南
└── README.md
```

## 开发进度

- [x] 测试用例和测试项目
- [x] 项目结构和配置文件
- [x] Token 计数器
- [x] Ollama 客户端（支持 Qwen3-coder、GLM-4.7）
- [x] 基础工具（view/edit/grep/bash）
- [x] Agent 主循环
- [x] 上下文压缩
- [x] CLI 交互界面
- [x] Benchmark 测试框架
- [x] VSCode 插件
- [x] CLI 彩色 Diff 显示
- [x] Feature Flags 功能开关系统

## 更新日志

### v1.1.0 (2026-02-07)

**新功能**
- 默认模型切换为 qwen3-coder:latest
- CLI 彩色 diff 显示（`edit_file` / `create_file` 执行后显示 unified diff）
- `create_file` 支持 VSCode diff preview
- VSCode diff 确认后自动打开修改的文件
- 工具执行后空响应自动重试（feature flag 控制）
- Feature Flags 系统（`config/feature.yaml` 集中管理功能开关）

**改进**
- 修复 config 路径解析（`precheck_runner.py` / `i18n.py`）
- 会话恢复提示可通过 feature flag 关闭

### v1.0.0 (2025-02-02)

**新功能**
- 支持 GLM-4.7-flash 模型，默认模型切换为 glm-4.7-flash:latest
- 新增思考模式 (think mode) 支持，提升复杂任务推理能力
- 新增 `--test` 参数运行 benchmark 测试
- 新增 `--model` 参数指定模型
- 新增 QUICKSTART.md 快速入门指南

**改进**
- 优化 todo_write 工具描述，鼓励并行调用
- 简化 benchmark 测试用例，移除 GTest 依赖
- 清理 VSCode launch.json 配置

### v0.2.0 (2025-12-26)

**新功能**
- 工具执行结果摘要显示（最多5行，绿色成功/红色错误）
- `find_similar_file` 智能路径纠错，自动建议相似文件名

**Bug 修复**
- 修复 git 工具参数被 validator 校验掉的问题（LLM 发送 JSON 字符串时）
- 修复 "总是允许" 功能对 view_file 等工具未生效的问题
- 修复确认系统测试用例的 API 不匹配问题

**重构**
- 重写 `test_edit_file_confirmation.py` 适配新的 edit_file API（old_str/new_str）
- 更新确认测试以使用 `ConfirmResult` 返回类型

## 如何反馈

我们欢迎任何形式的反馈和贡献！

### 提交 Issue
- Bug 报告：[GitHub Issues](https://github.com/yourusername/claude-qwen/issues)
- 功能建议：打上 `enhancement` 标签
- 使用问题：打上 `question` 标签

### 贡献代码
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 交流讨论
- Discussions：项目设计、架构讨论

## 致谢

- [Anthropic Claude Code](https://docs.anthropic.com/) - 设计灵感来源
- [Ollama](https://ollama.ai/) - 本地大模型部署
- [GLM / 智谱AI](https://github.com/THUDM/GLM-4) - 推荐模型
- [Qwen / 通义千问](https://github.com/QwenLM/Qwen) - 支持模型
- [tree-sitter](https://tree-sitter.github.io/) - 代码解析

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
