# -*- coding: utf-8 -*-
"""
Prompt templates for Qwen3 model
"""

# System prompt for the main agent
SYSTEM_PROMPT = """你是一个专业的 C/C++ 编程助手，基于 Qwen3 模型。

核心能力：
- 跨目录搜索和定位代码文件
- 理解和修改 C/C++ 代码
- 自动检测和修复编译错误
- 生成单元测试和集成测试
- 分析代码依赖关系

工作原则：
1. **直接调用工具，不要只描述计划** - 看到任务后立即使用工具执行，而不是说"我需要..."或"让我..."
2. 使用工具流程：grep 搜索 → view 读取 → edit/create 修改 → bash 验证
3. 保持代码风格一致（缩进、括号、命名）
4. 编译错误最多重试 3 次
5. 生成测试时使用 GTest 框架
6. 修改前先理解上下文

可用工具：
- view_file: 读取文件内容
- edit_file: str_replace 方式编辑
- create_file: 创建新文件
- grep_search: 搜索代码模式
- list_dir: 列出目录
- bash_run: 执行命令（cmake, make, g++, git）
- cmake_build: CMake 构建
- parse_cpp: 解析 C++ 结构
- find_functions: 提取函数签名
- get_dependencies: 分析依赖

重要约束：
- 危险操作（删除 >10 文件）需确认
- bash 命令限白名单
- 单个文件不超过 10000 tokens
- **每次响应都必须包含tool_calls，直到任务完成**
"""

# Intent recognition prompt
INTENT_RECOGNITION_PROMPT = """分析用户意图并预估所需工具。

用户输入: {user_input}

项目上下文:
- 根目录: {project_root}
- 当前活动文件: {active_file}
- 最近修改: {recent_changes}

返回 JSON 格式：
{{
  "task_type": "file_location|compile_fix|test_generation|code_analysis|general",
  "estimated_tools": ["tool1", "tool2"],
  "estimated_complexity": "low|medium|high",
  "reasoning": "简短说明"
}}

注意：这只是建议，实际执行可动态调整。
"""

# TODO generation prompt
TODO_GENERATION_PROMPT = """为任务生成执行计划（TODO 列表）。

任务: {task_description}

上下文:
{context}

生成 JSON 格式的 TODO 列表：
{{
  "todos": [
    {{"step": 1, "action": "搜索目标文件", "tool": "grep_search", "priority": "high"}},
    {{"step": 2, "action": "读取文件内容", "tool": "view_file", "priority": "high"}},
    {{"step": 3, "action": "修改代码", "tool": "edit_file", "priority": "medium"}}
  ],
  "estimated_steps": 5,
  "risks": ["可能的风险点"]
}}

规则：
1. 步骤要具体可执行
2. 优先级: high > medium > low
3. 预估总步骤数
"""

# Compilation error parsing prompt
COMPILE_ERROR_PROMPT = """解析编译错误并提供修复建议。

编译输出:
{compile_output}

返回 JSON 格式：
{{
  "errors": [
    {{
      "file": "src/parser.cpp",
      "line": 42,
      "column": 10,
      "type": "error|warning",
      "message": "错误描述",
      "suggested_fix": "修复建议"
    }}
  ],
  "total_errors": 3,
  "total_warnings": 1,
  "fixable": true
}}

支持的编译器格式：
- GCC: "file.cpp:42:10: error: message"
- Clang: "file.cpp:42:10: error: message"
- MSVC: "file.cpp(42): error C2065: message"
"""

# Context compression prompt
CONTEXT_COMPRESSION_PROMPT = """压缩对话历史到 {target_tokens} tokens。

当前状态:
- 总 tokens: {current_tokens}
- 目标 tokens: {target_tokens}
- 压缩比: {compression_ratio}

必须保留（不可压缩）:
{must_keep}

可压缩内容:
{compressible}

返回 JSON:
{{
  "compressed_summary": "压缩后的摘要（保留关键信息）",
  "keep_message_indices": [0, 5, 10],  # 完整保留的消息索引
  "processed_files_summary": {{
    "file1.cpp": "关键修改：添加了超时机制",
    "file2.h": "声明了新函数"
  }},
  "deleted_indices": [1, 2, 3, 4],  # 删除的消息索引
  "estimated_tokens": 50000
}}

压缩策略:
1. 删除冗余工具输出
2. 合并相似的对话
3. 保留决策点和结果
4. 压缩文件内容为摘要
"""

# Test generation prompts
UNIT_TEST_GENERATION_PROMPT = """为指定文件生成 GTest 单元测试。

源文件: {source_file}

函数签名:
{function_signatures}

生成要求:
1. 使用 GTest 框架
2. 测试文件路径: tests/{module}/{filename}_test.cpp
3. 包含边界条件测试
4. 每个 public 函数至少 2 个测试用例
5. 使用 EXPECT_* 断言

测试模板:
```cpp
#include <gtest/gtest.h>
#include "{header_file}"

TEST(ClassNameTest, FunctionName_Scenario) {{
    // Arrange
    // Act
    // Assert
}}
```

返回完整的测试文件内容。
"""

INTEGRATION_TEST_GENERATION_PROMPT = """为模块生成集成测试。

模块: {module_name}

模块文件:
{module_files}

依赖关系:
{dependencies}

生成要求:
1. 测试文件: tests/integration/{module_name}_test.cpp
2. 测试模块边界行为
3. Mock 外部依赖
4. 验证模块间交互

返回完整的集成测试代码。
"""

# Code style analysis prompt
CODE_STYLE_PROMPT = """分析代码风格并在修改时保持一致。

文件内容:
{file_content}

分析要点:
1. 缩进: 空格数或 tab
2. 括号位置: K&R, Allman, GNU
3. 命名: camelCase, snake_case, PascalCase
4. 注释风格: //, /* */
5. 包含顺序

返回 JSON:
{{
  "indent": "4_spaces|2_spaces|tabs",
  "brace_style": "k&r|allman|gnu",
  "naming_convention": "snake_case|camelCase|PascalCase",
  "comment_style": "single_line|block",
  "include_order": ["system", "project", "local"]
}}
"""

# Error recovery prompt
ERROR_RECOVERY_PROMPT = """编译修复失败，准备保存会话状态。

失败原因: {failure_reason}
尝试次数: {attempt_count}
最后错误: {last_error}

生成会话快照:
{{
  "timestamp": "ISO 8601 格式",
  "project_root": "项目路径",
  "active_files": ["正在处理的文件"],
  "last_error": "最后的错误信息",
  "attempted_fixes": [
    {{"file": "file.cpp", "change": "修改描述", "result": "failed"}}
  ],
  "compressed_context": "压缩的上下文摘要",
  "next_steps": ["建议的下一步操作"]
}}

保存到: {project_root}/.claude_session
"""

# Function calling format
FUNCTION_CALL_FORMAT = """调用工具时使用 JSON 格式：

{{
  "tool_calls": [
    {{
      "id": "call_1",
      "name": "grep_search",
      "arguments": {{
        "pattern": "class NetworkHandler",
        "scope": "src/"
      }}
    }},
    {{
      "id": "call_2", 
      "name": "view_file",
      "arguments": {{
        "path": "src/network/handler.cpp",
        "line_range": [10, 50]
      }}
    }}
  ]
}}

可以一次调用多个工具，但要考虑依赖关系。
"""

# Helper function to format prompts
def format_prompt(template: str, **kwargs) -> str:
    """Format prompt template with variables"""
    return template.format(**kwargs)


def get_system_prompt() -> str:
    """Get the main system prompt"""
    return SYSTEM_PROMPT


def get_intent_prompt(user_input: str, project_root: str = "", 
                      active_file: str = "", recent_changes: str = "") -> str:
    """Get intent recognition prompt"""
    return format_prompt(
        INTENT_RECOGNITION_PROMPT,
        user_input=user_input,
        project_root=project_root,
        active_file=active_file,
        recent_changes=recent_changes
    )


def get_todo_prompt(task_description: str, context: str = "") -> str:
    """Get TODO generation prompt"""
    return format_prompt(
        TODO_GENERATION_PROMPT,
        task_description=task_description,
        context=context
    )


def get_compile_error_prompt(compile_output: str) -> str:
    """Get compilation error parsing prompt"""
    return format_prompt(
        COMPILE_ERROR_PROMPT,
        compile_output=compile_output
    )


def get_compression_prompt(current_tokens: int, target_tokens: int,
                           must_keep: str, compressible: str) -> str:
    """Get context compression prompt"""
    compression_ratio = target_tokens / current_tokens if current_tokens > 0 else 1.0
    return format_prompt(
        CONTEXT_COMPRESSION_PROMPT,
        current_tokens=current_tokens,
        target_tokens=target_tokens,
        compression_ratio=f"{compression_ratio:.2%}",
        must_keep=must_keep,
        compressible=compressible
    )


def get_unit_test_prompt(source_file: str, function_signatures: str,
                         header_file: str = "") -> str:
    """Get unit test generation prompt"""
    return format_prompt(
        UNIT_TEST_GENERATION_PROMPT,
        source_file=source_file,
        function_signatures=function_signatures,
        header_file=header_file
    )


def get_integration_test_prompt(module_name: str, module_files: str,
                                dependencies: str) -> str:
    """Get integration test generation prompt"""
    return format_prompt(
        INTEGRATION_TEST_GENERATION_PROMPT,
        module_name=module_name,
        module_files=module_files,
        dependencies=dependencies
    )


def get_code_style_prompt(file_content: str) -> str:
    """Get code style analysis prompt"""
    return format_prompt(
        CODE_STYLE_PROMPT,
        file_content=file_content
    )


def get_error_recovery_prompt(failure_reason: str, attempt_count: int,
                              last_error: str, project_root: str) -> str:
    """Get error recovery prompt"""
    return format_prompt(
        ERROR_RECOVERY_PROMPT,
        failure_reason=failure_reason,
        attempt_count=attempt_count,
        last_error=last_error,
        project_root=project_root
    )
