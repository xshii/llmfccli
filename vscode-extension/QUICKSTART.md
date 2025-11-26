# Quick Start Guide

快速上手 Claude-Qwen VSCode Extension。

## 前置条件

1. **安装 Ollama**
   ```bash
   # macOS/Linux
   curl https://ollama.ai/install.sh | sh

   # 或访问 https://ollama.ai 下载安装包
   ```

2. **拉取 Qwen3 模型**
   ```bash
   ollama pull qwen3
   ```

3. **安装 Claude-Qwen CLI**
   ```bash
   # 从项目根目录
   cd /path/to/llmfccli
   pip install -e .[dev]
   ```

## 安装扩展

### 方式 1：从源码构建并安装

```bash
# 1. 进入扩展目录
cd vscode-extension

# 2. 安装依赖
npm install

# 3. 编译 TypeScript
npm run compile

# 4. 打包为 VSIX
npm run package

# 5. 安装扩展
code --install-extension claude-qwen-0.1.0.vsix
```

### 方式 2：开发模式（推荐开发者）

```bash
# 1. 在 VSCode 中打开 vscode-extension 目录
code vscode-extension

# 2. 按 F5 启动扩展开发主机
```

## 首次使用

### 1. 配置扩展

打开 VSCode 设置 (`Ctrl+,` / `Cmd+,`)，搜索 "claude-qwen"：

```json
{
  "claude-qwen.pythonPath": "python3",
  "claude-qwen.autoStart": true,
  "claude-qwen.logLevel": "info"
}
```

### 2. 打开 C/C++ 项目

```bash
# 打开你的 C++ 项目
code /path/to/your/cpp/project
```

### 3. 启动助手

**方法 1：命令面板**
- 按 `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`)
- 输入 "Claude-Qwen: Start"
- 回车

**方法 2：自动启动**
- 如果设置了 `autoStart: true`，打开 C/C++ 文件时会自动启动

### 4. 查看输出

- 打开输出面板：`View → Output`
- 选择 "Claude-Qwen" 频道
- 应该看到类似输出：
  ```
  Claude-Qwen extension activated
  Commands registered successfully
  Starting CLI: python3 -m backend.cli --root /path/to/project
  CLI started successfully
  ```

## 常用功能

### 1. 修复编译错误

```bash
# 方式 1: 命令面板
Ctrl+Shift+P → "Claude-Qwen: Fix Compile Errors"

# 方式 2: 直接在 CLI 中输入
编译项目并修复所有错误
```

### 2. 生成单元测试

```bash
# 方式 1: 命令面板
Ctrl+Shift+P → "Claude-Qwen: Generate Unit Tests"

# 方式 2: 快捷键
Ctrl+Shift+T (Mac: Cmd+Shift+T)

# 方式 3: 右键菜单
右键点击编辑器 → "Generate Unit Tests"
```

### 3. 解释代码

```bash
# 1. 选中代码
# 2. 按 Ctrl+Shift+E (Mac: Cmd+Shift+E)
# 或右键 → "Explain Selected Code"
```

### 4. 测试集成

```bash
# 验证 VSCode 和 CLI 通信是否正常
Ctrl+Shift+P → "Claude-Qwen: Test VSCode Integration"

# 在 CLI 终端应该看到测试结果表格
```

## 示例场景

### 场景 1：修复编译错误

```cpp
// main.cpp
#include <iostream>

int main() {
    std::cout << "Hello World << std::endl;  // 缺少引号
    return 0;
}
```

**操作：**
1. 运行 `Claude-Qwen: Fix Compile Errors`
2. AI 检测到语法错误
3. 自动修复为：`std::cout << "Hello World" << std::endl;`

### 场景 2：生成测试

```cpp
// calculator.cpp
int add(int a, int b) {
    return a + b;
}
```

**操作：**
1. 光标放在 `add` 函数中
2. 运行 `Claude-Qwen: Generate Unit Tests`
3. AI 生成 GTest 测试代码

### 场景 3：代码解释

```cpp
// 选中这段代码
std::unique_ptr<int[]> arr(new int[10]);
std::fill_n(arr.get(), 10, 0);
```

**操作：**
1. 选中代码
2. 按 `Ctrl+Shift+E`
3. AI 解释智能指针和数组初始化

## 常见问题

### 扩展无法启动

**检查清单：**
```bash
# 1. Python 是否正确安装
python3 --version

# 2. CLI 是否安装
python3 -m backend.cli --help

# 3. Ollama 是否运行
ollama list

# 4. Qwen3 模型是否存在
ollama list | grep qwen3
```

### CLI 进程崩溃

**查看日志：**
1. 打开输出面板：`View → Output`
2. 选择 "Claude-Qwen"
3. 查找错误信息

**重启 CLI：**
```bash
# 停止
Ctrl+Shift+P → "Claude-Qwen: Stop"

# 启动
Ctrl+Shift+P → "Claude-Qwen: Start"
```

### 响应很慢

**可能原因：**
- Ollama 模型未预加载
- 系统资源不足
- 远程 Ollama 需要 SSH 隧道

**解决方案：**
```bash
# 预热模型
ollama run qwen3 "hi"

# 检查系统资源
htop  # 或 Activity Monitor (Mac)

# 远程 Ollama: 启动隧道
ssh -fN ollama-tunnel
```

## 高级配置

### 远程 Ollama

如果 Ollama 在远程服务器：

```bash
# 1. 配置 SSH 隧道 (~/.ssh/config)
Host ollama-tunnel
    HostName your-server
    User your-user
    LocalForward 11434 localhost:11434

# 2. 启动隧道
ssh -fN ollama-tunnel

# 3. 验证连接
curl http://localhost:11434/api/tags
```

### 自定义提示词

编辑 `config/modelfiles/claude-qwen.modelfile`：

```modelfile
FROM qwen3:latest

SYSTEM """
你是一个专业的 C++ 编程助手...
（自定义你的系统提示词）
"""
```

重新创建模型：
```bash
ollama create claude-qwen -f config/modelfiles/claude-qwen.modelfile
```

## 下一步

- 阅读完整文档：[README.md](./README.md)
- 了解架构设计：[VSCODE_INTEGRATION.md](../docs/VSCODE_INTEGRATION.md)
- 查看 API 文档：[CLAUDE.md](../CLAUDE.md)
- 贡献代码：提交 Pull Request 到 GitHub

## 获取帮助

遇到问题？

1. 查看输出日志
2. 阅读 [README.md](./README.md)
3. 提交 Issue：https://github.com/xshii/llmfccli/issues
