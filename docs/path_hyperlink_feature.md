# 路径超链接功能

## 概述

在工具调用输出中，文件路径现在会自动转换为可点击的超链接，即使路径被压缩显示，仍然可以点击打开完整路径。

## 功能特性

### 1. 自动路径检测

系统会自动识别以下参数名作为文件路径：
```python
PATH_PARAM_NAMES = {
    'path', 'file', 'file_path', 'filepath',
    'source', 'target', 'destination', 'src', 'dst'
}
```

### 2. 智能压缩 + 超链接

- **项目内路径**（≤ 3 层）：保留完整相对路径
  ```
  backend/agent/tool_registry.py
  └─> 点击打开: /home/user/llmfccli/backend/agent/tool_registry.py
  ```

- **项目内路径**（> 3 层）：压缩显示，保留完整链接
  ```
  backend/.../filesystem_tools/view_file.py
  └─> 点击打开: /home/user/llmfccli/backend/tools/filesystem_tools/view_file.py
  ```

- **项目外路径**（≤ 4 层）：显示完整绝对路径
  ```
  /tmp/test.txt
  └─> 点击打开: /tmp/test.txt
  ```

- **项目外路径**（> 4 层）：压缩显示，保留完整链接
  ```
  /usr/lib/.../site-packages/module.py
  └─> 点击打开: /usr/lib/python3/site-packages/module.py
  ```

### 3. OSC 8 超链接协议

使用 Rich 库的 `[link=file://path]text[/link]` 语法，生成符合 [OSC 8 标准](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda) 的超链接。

## 实现细节

### 代码位置

**backend/cli/output_manager.py:100-108**

```python
# 如果是路径参数，压缩并添加超链接
if is_path_param:
    # 获取绝对路径用于超链接
    abs_path = os.path.abspath(value_str) if not os.path.isabs(value_str) else value_str

    # 压缩路径用于显示
    compressed = self.path_utils.compress_path(value_str, max_length=40)

    # 创建可点击的超链接（file:// protocol）
    value_str = f"[link=file://{abs_path}]{compressed}[/link]"
```

### 依赖注入架构

```
ToolOutputManager
    │
    ├─> PathUtils (压缩路径逻辑)
    └─> file:// hyperlink (超链接封装)
```

## 支持的终端

以下终端支持 OSC 8 超链接：

- ✅ **iTerm2** (macOS)
- ✅ **WezTerm** (跨平台)
- ✅ **Windows Terminal** (Windows 10/11)
- ✅ **kitty** (Linux/macOS)
- ✅ **GNOME Terminal** (3.38+)
- ✅ **Konsole** (KDE)
- ❌ **macOS Terminal.app** (不支持)
- ❌ **PuTTY** (不支持)

### 使用方法

在支持的终端中：
- **macOS**: `Cmd + 点击` 路径
- **Windows/Linux**: `Ctrl + 点击` 路径

## 示例输出

```python
# 工具调用显示
🔧 view_file (path=backend/agent/tool_registry.py, line_range=[1, 50])
              └─────────────────────────────────┘
                       可点击的超链接

🔧 edit_file (path=backend/.../filesystem_tools/view_file.py, ...)
              └─────────────────────────────────────────────┘
                  压缩后的路径仍然可点击！
```

## 测试覆盖

### 单元测试

**tests/unit/test_output_manager_hyperlink.py**
- ✅ 超链接格式验证
- ✅ 绝对路径验证
- ✅ 路径压缩 + 超链接组合
- ✅ 非路径参数不被处理

### 演示脚本

**tests/unit/test_hyperlink_demo.py**
- 完整的工具调用输出演示
- 多种路径格式展示

## 性能影响

- **启动时间**: 无影响（PathUtils 通过依赖注入）
- **运行时**: 每次路径处理增加 ~0.1ms（`os.path.abspath` 调用）
- **内存占用**: 忽略不计（只是字符串拼接）

## 向后兼容性

- ✅ 不支持 OSC 8 的终端会显示普通文本（忽略超链接标记）
- ✅ 路径压缩逻辑与之前完全相同
- ✅ 不影响现有功能

## 未来改进

1. **VS Code 集成**: 使用 `vscode://file/path:line:col` 协议在 VS Code 中打开文件
2. **行号跳转**: `file:///path/to/file.py#L42` 跳转到指定行
3. **可配置**: 允许用户禁用超链接或自定义压缩策略

## 相关文件

- `backend/cli/output_manager.py` - 超链接生成逻辑
- `backend/cli/path_utils.py` - 路径压缩逻辑
- `tests/unit/test_output_manager_hyperlink.py` - 单元测试
- `tests/unit/test_hyperlink_demo.py` - 演示脚本

## 参考资料

- [OSC 8 Hyperlinks Specification](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda)
- [Rich Library Documentation](https://rich.readthedocs.io/en/stable/markup.html#links)
- [File URI Scheme (RFC 8089)](https://datatracker.ietf.org/doc/html/rfc8089)
