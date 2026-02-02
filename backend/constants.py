# -*- coding: utf-8 -*-
"""
全局常量定义

集中管理项目中的魔法数字，提高可维护性。
"""

# ============================================================
# 超时常量 (秒)
# ============================================================

class Timeout:
    """超时时间常量"""

    # 快速操作 (文件检查、简单命令)
    QUICK = 5

    # 一般操作 (搜索、git 状态)
    MEDIUM = 30

    # 较长操作 (git 操作、测试)
    LONG = 60

    # 构建操作 (cmake, make)
    BUILD = 300

    # 模型操作 (下载、加载大模型)
    MODEL = 600

    # Shell drain 操作
    SHELL_DRAIN = 0.2
    SHELL_DRAIN_INIT = 0.3
    SHELL_DRAIN_CLOSE = 0.5

    # RPC 操作
    RPC_HEARTBEAT = 2.0
    RPC_THREAD_JOIN = 1.0


# ============================================================
# 限制常量
# ============================================================

class Limit:
    """数量限制常量"""

    # 目录遍历深度
    MAX_DEPTH_DEFAULT = 3

    # 会话列表数量
    SESSION_LIST_DEFAULT = 15
    SESSION_LIST_MAX = 100

    # 搜索结果数量
    SEARCH_RESULTS_MAX = 50

    # 文件列表数量
    FILE_LIST_MAX = 500

    # 字符串截断长度
    STRING_PREVIEW_LENGTH = 50


# ============================================================
# 工具默认参数
# ============================================================

class ToolDefaults:
    """工具默认参数"""

    # bash_run 默认超时
    BASH_TIMEOUT = 60

    # grep_search 超时
    GREP_TIMEOUT = 30

    # list_dir 默认深度
    LIST_DIR_DEPTH = 3

    # cmake 构建超时
    CMAKE_CONFIGURE_TIMEOUT = 60
    CMAKE_BUILD_TIMEOUT = 300


# ============================================================
# 重试配置
# ============================================================

class Retry:
    """重试配置常量"""

    # 最大重试次数
    MAX_ATTEMPTS = 3

    # 基础延迟 (秒)
    BASE_DELAY = 1.0

    # 最大延迟 (秒)
    MAX_DELAY = 30.0

    # 指数退避因子
    BACKOFF_FACTOR = 2.0
