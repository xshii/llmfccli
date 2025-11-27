# Windows 平台使用说明

## 持久化 Shell 会话

在 Windows 上，`/cmd` 命令使用 `cmd.exe` 作为持久化 shell。

## 平台差异

### 环境变量

**设置环境变量**:
```cmd
# Windows
/cmd set MY_VAR=value

# Linux/Mac
/cmd export MY_VAR=value
```

**使用环境变量**:
```cmd
# Windows
/cmd echo %MY_VAR%

# Linux/Mac
/cmd echo $MY_VAR
```

### 目录切换

**跨磁盘切换**:
```cmd
# Windows: 需要 /d 参数切换磁盘
/cmd cd /d D:\Projects

# Linux/Mac: 直接 cd
/cmd cd /home/user/projects
```

**查看当前目录**:
```cmd
# Windows: cd 不带参数
/cmd cd

# Linux/Mac: pwd 命令
/cmd pwd

# 或使用统一命令
/cmdpwd
```

### 命令对照表

| 功能 | Windows (cmd.exe) | Unix (bash) |
|------|-------------------|-------------|
| 设置变量 | `set VAR=value` | `export VAR=value` |
| 使用变量 | `%VAR%` | `$VAR` |
| 查看目录 | `cd` 或 `dir` | `pwd` 或 `ls` |
| 切换目录 | `cd /d PATH` | `cd PATH` |
| 文本搜索 | `findstr` | `grep` |
| 查看文件 | `type` | `cat` |
| 退出码 | `%ERRORLEVEL%` | `$?` |

## Windows 工作流示例

### 示例 1: Python 开发环境

```cmd
# 切换到项目目录
/cmd cd /d D:\Projects\MyPythonApp

# 激活虚拟环境
/cmd venv\Scripts\activate.bat

# 设置环境变量
/cmd set FLASK_APP=app.py
/cmd set FLASK_ENV=development

# 安装依赖（环境变量已设置）
/cmd pip install -r requirements.txt

# 运行应用
/cmd python -m flask run

# 查看当前状态
/cmdpwd
# 输出：D:\Projects\MyPythonApp
```

### 示例 2: C++ 编译环境

```cmd
# 进入项目
/cmd cd /d C:\Dev\CppProject

# 设置 MinGW 环境
/cmd set PATH=%PATH%;C:\MinGW\bin
/cmd set INCLUDE=C:\MinGW\include

# 创建并进入构建目录
/cmd mkdir build
/cmd cd build

# 配置和编译
/cmd cmake -G "MinGW Makefiles" ..
/cmd mingw32-make

# 运行测试（仍在 build 目录）
/cmd ctest -V

# 查看当前目录
/cmdpwd
# 输出：C:\Dev\CppProject\build
```

### 示例 3: Git 工作流

```cmd
# 进入仓库
/cmd cd /d E:\Repositories\MyRepo

# 查看状态
/cmd git status

# 创建分支
/cmd git checkout -b feature/new-feature

# 查看日志
/cmd git log --oneline -10

# 查看差异
/cmd git diff

# 当前分支会保持
/cmd git branch
```

### 示例 4: Node.js 开发

```cmd
# 进入项目
/cmd cd /d D:\WebProjects\MyApp

# 设置 npm 镜像（环境会保留）
/cmd set npm_config_registry=https://registry.npmmirror.com

# 安装依赖
/cmd npm install

# 设置开发环境变量
/cmd set NODE_ENV=development
/cmd set PORT=3000

# 启动开发服务器
/cmd npm run dev

# 变量在会话中保持
/cmd echo %NODE_ENV%
# 输出：development
```

## 常见问题

### Q: 命令执行失败，提示找不到命令

**A**: 确保命令在 PATH 中，或使用完整路径：
```cmd
# 错误
/cmd python script.py

# 正确（使用完整路径）
/cmd C:\Python39\python.exe script.py

# 或先设置 PATH
/cmd set PATH=%PATH%;C:\Python39
/cmd python script.py
```

### Q: 如何在不同磁盘之间切换？

**A**: 使用 `cd /d`：
```cmd
# 从 C: 切换到 D:
/cmd cd /d D:\Projects

# 只用 cd 不会切换磁盘
/cmd cd D:\Projects  # ❌ 不会切换到 D:
```

### Q: 环境变量设置后看不到效果

**A**: 检查变量引用语法：
```cmd
# 错误（Unix 语法）
/cmd echo $MY_VAR  # ❌ Windows 显示 "$MY_VAR"

# 正确（Windows 语法）
/cmd echo %MY_VAR%  # ✓ 显示变量值
```

### Q: 如何重置会话？

**A**: 使用 `/cmdclear`：
```cmd
# 会话被修改了
/cmd cd D:\SomeDir
/cmd set SOME_VAR=value

# 重置到初始状态
/cmdclear

# 现在回到项目根目录，环境变量清除
/cmdpwd
```

## 限制

### Windows 特定限制

1. **不支持 Unix 命令**：
   - `grep` → 使用 `findstr`
   - `cat` → 使用 `type`
   - `ls` → 使用 `dir`

2. **路径分隔符**：
   - Windows: `\` 或 `/`（cmd 两者都支持）
   - Unix: `/`

3. **交互式命令**：
   - 不支持需要交互的命令（如 `vim`、`nano`）
   - 考虑使用非交互式替代方案

4. **命令长度限制**：
   - cmd.exe 有 8191 字符的命令长度限制

## 最佳实践

### 1. 使用绝对路径

```cmd
# 推荐：明确的绝对路径
/cmd cd /d D:\Projects\MyApp

# 避免：相对路径可能导致混淆
/cmd cd ..\OtherApp
```

### 2. 验证环境变量

```cmd
# 设置后立即验证
/cmd set MY_PATH=C:\Tools\bin
/cmd echo %MY_PATH%
# 确认输出正确
```

### 3. 使用 /cmdpwd 确认位置

```cmd
# 切换目录后确认
/cmd cd build
/cmdpwd
# 确保在正确的目录
```

### 4. 重置会话避免污染

```cmd
# 完成一个任务后重置
/cmd cd /d D:\TempWork
/cmd set TEMP_VAR=value
# ... 完成工作 ...
/cmdclear
# 开始新任务，环境干净
```

## 相关文档

- [命令透传功能](CMD_PASSTHROUGH.md)
- [Tab 补全功能](TAB_COMPLETION.md)
