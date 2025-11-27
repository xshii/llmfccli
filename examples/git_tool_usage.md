# Git Tool 使用示例

## 概述

Git 工具提供了统一的接口来执行各种 Git 操作，支持细粒度的确认控制。

## 基本用法

### 1. 查看状态

```python
# Agent 调用
git(action='status', args={})

# 用户确认对话框
⚠ 工具执行确认 - 工具: git | 类别: git
操作: status | 参数: {}
选择操作:
  1. 仅本次允许
  2. 始终允许
  3. 拒绝并停止

# 用户选择 2 (始终允许)
✓ 始终允许 Git 操作: status
  允许标识: git:status

# 以后所有 git status 都不再提示
```

### 2. 添加文件

```python
# 添加单个文件
git(action='add', args={'files': ['src/main.py']})

# 添加多个文件
git(action='add', args={'files': ['file1.py', 'file2.py']})

# 添加所有修改的文件
git(action='add', args={'all': True})
```

### 3. 提交更改

```python
# 普通提交
git(action='commit', args={
    'message': 'feat: Add new feature'
})

# 修改最后一次提交
git(action='commit', args={
    'message': 'feat: Add new feature (updated)',
    'amend': True
})

# 跳过 pre-commit hooks
git(action='commit', args={
    'message': 'fix: Emergency hotfix',
    'no_verify': True
})
```

### 4. 分支操作

```python
# 列出所有分支
git(action='branch', args={'operation': 'list', 'all': True})

# 创建新分支
git(action='branch', args={
    'operation': 'create',
    'name': 'feature/new-ui'
})

# 切换分支
git(action='checkout', args={'target': 'feature/new-ui'})

# 创建并切换到新分支
git(action='checkout', args={
    'target': 'feature/new-feature',
    'create': True
})

# 删除分支
git(action='branch', args={
    'operation': 'delete',
    'name': 'old-feature'
})
```

### 5. 远程操作

```python
# 推送到远程
git(action='push', args={
    'remote': 'origin',
    'branch': 'main'
})

# 设置上游分支并推送
git(action='push', args={
    'remote': 'origin',
    'branch': 'feature/new',
    'set_upstream': True
})

# 拉取更新
git(action='pull', args={
    'remote': 'origin',
    'branch': 'main'
})

# 使用 rebase 拉取
git(action='pull', args={
    'remote': 'origin',
    'branch': 'main',
    'rebase': True
})

# 获取远程更新
git(action='fetch', args={
    'remote': 'origin',
    'prune': True
})
```

### 6. 查看历史和差异

```python
# 查看提交历史
git(action='log', args={
    'count': 10,
    'oneline': True,
    'graph': True
})

# 查看工作区差异
git(action='diff', args={})

# 查看暂存区差异
git(action='diff', args={'staged': True})

# 查看特定文件的差异
git(action='diff', args={'files': ['src/main.py']})

# 查看特定提交
git(action='show', args={'commit': 'HEAD'})
```

### 7. 高级操作

```python
# Stash 暂存
git(action='stash', args={
    'operation': 'save',
    'message': 'WIP: Work in progress',
    'include_untracked': True
})

# Stash 恢复
git(action='stash', args={
    'operation': 'pop'
})

# Reset
git(action='reset', args={
    'mode': 'mixed',
    'target': 'HEAD~1'
})

# Rebase
git(action='rebase', args={
    'operation': 'start',
    'branch': 'main',
    'interactive': False
})

# Cherry-pick
git(action='cherry-pick', args={
    'operation': 'pick',
    'commits': ['abc123', 'def456']
})
```

## 危险操作示例

### 1. Hard Reset (⚠️ 危险)

```python
# Agent 调用
git(action='reset', args={
    'mode': 'hard',
    'target': 'HEAD~1'
})

# 确认对话框
⚠ 工具执行确认 - 工具: git | 类别: git
操作: reset | 参数:
  mode: hard
  target: HEAD~1

选择操作: [1/2/3]
```

**即使用户之前选择了 "始终允许 git:reset"，由于 `mode=hard`，系统仍会要求确认！**

### 2. Force Push (⚠️ 危险)

```python
# Agent 调用
git(action='push', args={
    'remote': 'origin',
    'branch': 'main',
    'force': True
})

# 确认对话框会标记为危险操作
⚠ 工具执行确认 - 工具: git | 类别: git
操作: push | 参数:
  remote: origin
  branch: main
  force: true  ⚠️

选择操作: [1/2/3]

# 如果用户选择 2 (始终允许)
✓ 始终允许 Git 操作: push
  ⚠️  注意：危险参数仍需确认 (如 --force, --hard)
  允许标识: git:push
```

**下次正常 push 不会提示，但 force push 仍会提示！**

## 细粒度控制场景

### 场景 1: 开发工作流

```python
# 1. 用户允许常用的安全操作
git:status    ✓ 始终允许
git:log       ✓ 始终允许
git:diff      ✓ 始终允许
git:add       ✓ 始终允许
git:commit    ✓ 始终允许

# 2. 敏感操作仍需确认
git:push      ❌ 每次都要确认
git:reset     ❌ 每次都要确认
git:rebase    ❌ 每次都要确认

# 结果：Agent 可以自由查看状态、添加文件、提交，
# 但推送前必须经过用户确认
```

### 场景 2: CI/CD 自动化

```python
# 自动化脚本中，所有操作都设置为始终允许
git:status    ✓
git:pull      ✓
git:add       ✓
git:commit    ✓
git:push      ✓

# 但危险参数仍会触发确认
push --force   ⚠️ 仍需确认
reset --hard   ⚠️ 仍需确认
```

### 场景 3: 只读访问

```python
# 只允许查询操作
git:status    ✓ 始终允许
git:log       ✓ 始终允许
git:diff      ✓ 始终允许
git:show      ✓ 始终允许

# 所有修改操作都拒绝
git:add       ❌ 拒绝
git:commit    ❌ 拒绝
git:push      ❌ 拒绝
```

## 错误处理

```python
# 所有操作都返回统一格式的结果
result = git(action='commit', args={'message': 'Test'})

# 检查结果
if result['success']:
    print(f"✓ 操作成功: {result['output']}")
else:
    print(f"✗ 操作失败: {result['error']}")
    print(f"返回码: {result['returncode']}")

# 示例: 缺少 commit message
{
    'success': False,
    'output': '',
    'error': 'Commit message is required',
    'returncode': 1
}

# 示例: 成功提交
{
    'success': True,
    'output': '[main abc123] feat: Add feature\n 1 file changed...',
    'error': '',
    'returncode': 0
}
```

## 安全特性

### 1. 危险操作自动检测

| 操作 | 触发条件 | 示例 |
|------|---------|------|
| reset | mode=hard | `git reset --hard HEAD~1` |
| push | force=true | `git push --force origin main` |
| branch | operation=delete + force | `git branch -D feature` |
| rebase | 任何 rebase | `git rebase main` |
| stash | operation=drop/clear | `git stash clear` |
| cherry-pick | 任何 cherry-pick | `git cherry-pick abc123` |

### 2. 项目根目录验证

```python
# Git 命令只能在项目根目录内执行
# 防止意外修改其他仓库
git(action='status', args={}, project_root='/home/user/project')
# ✓ 只在 /home/user/project 内执行

git(action='status', args={}, project_root='/invalid/path')
# ✗ 错误: Invalid project root
```

### 3. 超时保护

```python
# 所有命令都有超时限制
- 普通操作: 30 秒
- 网络操作 (push/pull/fetch): 60 秒
- Rebase: 120 秒

# 超时后返回错误
{
    'success': False,
    'error': 'Command timed out after 30 seconds',
    'returncode': 124
}
```

## 与 Agent 集成

Agent 可以智能地使用 Git 工具：

```python
# 用户: "提交当前更改"
# Agent 会执行:
1. git(action='status', args={})  # 查看当前状态
2. git(action='add', args={'all': True})  # 添加所有文件
3. git(action='commit', args={'message': '...'})  # 提交

# 用户: "推送到远程"
# Agent 会执行:
1. git(action='status', args={})  # 检查状态
2. git(action='push', args={'remote': 'origin', 'branch': 'main'})
   # ⚠️ 这里会弹出确认对话框

# 用户: "回退到上一个提交"
# Agent 会执行:
1. git(action='log', args={'count': 2})  # 查看历史
2. git(action='reset', args={'mode': 'soft', 'target': 'HEAD~1'})
   # 使用 soft 模式，保留修改
```

## 实际使用示例

完整的真实工作流程：

```python
# 1. 开始新功能
git(action='checkout', args={'target': 'feature/new-ui', 'create': True})

# 2. 修改代码后查看状态
git(action='status', args={})

# 3. 查看具体修改
git(action='diff', args={})

# 4. 添加并提交
git(action='add', args={'all': True})
git(action='commit', args={'message': 'feat: Implement new UI design'})

# 5. 查看提交历史
git(action='log', args={'count': 5, 'oneline': True})

# 6. 推送到远程 (需要确认)
git(action='push', args={
    'remote': 'origin',
    'branch': 'feature/new-ui',
    'set_upstream': True
})

# 7. 切换回主分支
git(action='checkout', args={'target': 'main'})

# 8. 拉取最新更新
git(action='pull', args={'remote': 'origin', 'branch': 'main'})
```

## 总结

Git 工具的优势：

1. **统一接口**: 一个工具，15 种操作
2. **细粒度控制**: 每个操作都有独立的确认签名
3. **智能安全**: 自动检测危险参数，即使已白名单也会提示
4. **用户友好**: 清晰的确认消息和警告提示
5. **错误处理**: 统一的错误返回格式
6. **超时保护**: 防止长时间阻塞

这样的设计既保证了灵活性，又确保了操作安全性！
