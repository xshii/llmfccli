# 文件名补全演示

本文档演示智能文件名补全功能的使用场景和多选择界面。

## 功能亮点

✨ **智能模糊匹配** - 输入部分文件名即可找到匹配文件
⚡ **高性能缓存** - 60 秒缓存，快速响应
🎯 **精确排序** - 按相关度智能排序
🚀 **自然语言集成** - 在对话中直接补全文件名

## 使用场景

### 场景 1: 查找网络相关文件

```bash
> 请修改 net[Tab]

# 自动显示匹配的文件（多个选择）
backend/remotectl/client.py           - File (.py)
src/network_handler.cpp               - File (.cpp)
src/network_handler.h                 - File (.h)
tests/test_network.cpp                - File (.cpp)

# 使用方向键选择，按 Enter 确认
> 请修改 src/network_handler.cpp
```

### 场景 2: 部分路径补全

```bash
> 查看 src/net[Tab]

# 只显示 src/ 目录下的匹配文件
src/network_handler.cpp               - File (.cpp)
src/network_handler.h                 - File (.h)

> 查看 src/network_handler.cpp
```

### 场景 3: 文件名模糊搜索

```bash
> 编辑配置文件 conf[Tab]

# 显示所有配置相关的文件
config/ollama.yaml                    - File (.yaml)
config/token_budget.yaml              - File (.yaml)
config/tools.yaml                     - File (.yaml)
backend/remotectl/cli_interactive.py  - File (.py)  # 也包含 "conf" 的文件

> 编辑配置文件 config/ollama.yaml
```

### 场景 4: 查找文档文件

```bash
> 阅读文档 README[Tab]

# 显示所有 README 文件
README.md                             - File (.md)
docs/README.md                        - File (.md)
vscode-extension/README.md            - File (.md)
tests/extension/README.md             - File (.md)

> 阅读文档 README.md
```

### 场景 5: 查找测试文件

```bash
> 运行测试 test_[Tab]

# 显示所有测试文件（按相关度排序）
tests/unit/test_tab_completion.py             - File (.py)
tests/unit/test_filename_completion.py        - File (.py)
tests/unit/test_cmd_passthrough.py            - File (.py)
tests/unit/test_tools_only.py                 - File (.py)
tests/unit/test_basic.py                      - File (.py)
... 还有 25 个匹配文件

# 可以继续输入缩小范围
> 运行测试 test_tab[Tab]
tests/unit/test_tab_completion.py             - File (.py)

> 运行测试 tests/unit/test_tab_completion.py
```

## 多选择界面

当有多个匹配时，prompt_toolkit 会自动显示选择界面：

```
> 请修改 cli[Tab]

  backend/cli_completer.py                     ← 光标在这里
  backend/cli.py
  backend/remotectl/cli_interactive.py
  backend/remotectl/cli.py
  backend/remotectl/cli_standalone.py
  backend/remotectl/client.py
  backend/rpc/client.py
  backend/llm/client.py
  vscode-extension/src/cliManager.ts
  tests/unit/test_enhanced_cli.py

# 键盘操作：
↑/↓     - 上下选择
Enter   - 确认选择
Tab     - 选择下一个
Esc     - 取消
```

## 智能匹配算法

补全器使用评分系统对匹配进行排序：

| 匹配类型 | 分数 | 示例 |
|---------|------|------|
| **精确匹配** | 1000 | 输入 `cli.py` → `cli.py` |
| **路径前缀** | 900 | 输入 `backend/cli` → `backend/cli.py` |
| **文件名前缀** | 800 | 输入 `net` → `network_handler.cpp` |
| **包含查询** | 500+ | 输入 `handler` → `network_handler.cpp` |

**额外加分**：
- 优先扩展名（.cpp, .h, .py, .md）：+100 分
- 路径较短：+0~50 分

## 文件类型优先级

补全器优先显示以下类型的文件：

### 源代码
- C/C++: `.cpp`, `.cc`, `.cxx`, `.c`, `.h`, `.hpp`, `.hxx`
- Python: `.py`, `.pyx`, `.pyi`
- JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`
- Java/Kotlin: `.java`, `.kt`
- Go/Rust: `.go`, `.rs`

### 配置文件
- `.yaml`, `.yml`, `.json`, `.toml`, `.ini`

### 文档
- `.md`, `.rst`, `.txt`

### 脚本
- `.sh`, `.bash`, `.zsh`

## 性能特性

### 缓存机制

```
第一次查询: 扫描项目 → 建立索引 → 返回结果 (约 1-5ms)
后续查询:   读取缓存 → 返回结果 (< 0.1ms)
缓存有效期: 60 秒
```

### 目录过滤

自动跳过以下目录：
- VCS: `.git`, `.svn`, `.hg`
- 缓存: `__pycache__`, `.pytest_cache`, `.mypy_cache`
- 依赖: `node_modules`, `.venv`, `venv`, `env`
- 构建: `build`, `dist`, `.eggs`
- IDE: `.vscode`, `.idea`

### 扫描限制

- **最大深度**: 5 层目录
- **最多结果**: 30 个文件
- **最小查询**: 2 个字符

## 实际使用技巧

### 技巧 1: 组合使用路径和文件名

```bash
# 不确定文件在哪里？先输入文件名
> 查看 handler[Tab]
# 看到所有包含 handler 的文件

# 知道大致位置？输入路径
> 查看 src/handler[Tab]
# 只显示 src/ 下的文件
```

### 技巧 2: 利用文件扩展名

```bash
# 查找配置文件
> 编辑 .yaml[Tab]
config/ollama.yaml
config/token_budget.yaml
config/tools.yaml

# 查找 C++ 源文件
> 修改 .cpp[Tab]
src/network_handler.cpp
src/file_manager.cpp
src/main.cpp
```

### 技巧 3: 渐进式输入

```bash
# 太多结果？继续输入
> test[Tab]           # 30+ 个结果
> test_tab[Tab]       # 1 个结果
> tests/unit/test_tab_completion.py
```

### 技巧 4: 结合自然语言

```bash
# 在自然语言中使用补全
> 请帮我重构 net[Tab] 文件中的错误处理逻辑
  → src/network_handler.cpp

> 为 test_[Tab] 添加新的测试用例
  → tests/unit/test_tab_completion.py

> 查看 README[Tab] 了解项目结构
  → README.md
```

## 常见问题

### Q: 为什么有些文件没有出现在补全列表中？

**A**: 可能的原因：
1. 文件在被跳过的目录中（如 `.git`, `node_modules`）
2. 文件名是隐藏文件（以 `.` 开头）
3. 文件深度超过 5 层
4. 匹配分数太低（没进入前 30 名）

### Q: 如何强制刷新文件列表缓存？

**A**: 缓存会在 60 秒后自动刷新。如果需要立即刷新，重启 CLI 即可。

### Q: 补全速度慢怎么办？

**A**:
- 首次扫描可能需要几毫秒，后续会使用缓存
- 如果项目很大，考虑缩小扫描范围（未来版本可能支持）
- 使用更具体的查询减少匹配数量

### Q: 能补全绝对路径吗？

**A**: 目前只支持相对于项目根目录的路径。绝对路径补全请使用 `/root` 命令。

## 与其他补全功能的配合

文件名补全与其他补全器无缝配合：

```bash
# 命令补全 + 文件名补全
/cmd cat README[Tab]
  → /cmd cat README.md

# 路径补全（仅目录）vs 文件名补全（文件）
/root ~/proj[Tab]        # 只显示目录
  → /root ~/projects/

编辑 proj[Tab]           # 显示文件
  → projects/config.yaml
```

## 未来增强

计划中的功能：
- [ ] 支持正则表达式搜索
- [ ] 可配置的缓存时间
- [ ] 可配置的扫描深度
- [ ] 支持文件内容搜索
- [ ] 最近使用的文件优先
- [ ] 自定义文件类型优先级

## 反馈

如有建议或问题，欢迎：
- 提交 Issue: https://github.com/xshii/llmfccli/issues
- 贡献代码改进匹配算法
- 分享您的使用技巧

---

**提示**: 文件名补全让您无需记住完整路径，输入几个字母就能快速找到目标文件！
