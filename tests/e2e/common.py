# -*- coding: utf-8 -*-
"""
E2E测试的公共工具和配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 测试 fixture 目录
FIXTURES_DIR = str(Path(__file__).parent.parent / 'fixtures')
SAMPLE_CPP_PROJECT = str(Path(FIXTURES_DIR) / 'sample-cpp')


def setup_test_environment():
    """
    设置测试环境

    Returns:
        dict: 包含常用路径的字典
    """
    return {
        'project_root': PROJECT_ROOT,
        'fixtures_dir': FIXTURES_DIR,
        'sample_cpp': SAMPLE_CPP_PROJECT,
    }


def get_tool_calls_by_name(agent, tool_name: str) -> list:
    """
    从 agent.tool_calls 中获取指定名称的工具调用

    Args:
        agent: AgentLoop 实例
        tool_name: 工具名称

    Returns:
        list: 匹配的工具调用列表
    """
    return [
        tool for tool in agent.tool_calls
        if tool.get('function', {}).get('name') == tool_name
    ]


def has_tool_call(agent, tool_name: str) -> bool:
    """
    检查是否调用了指定工具

    Args:
        agent: AgentLoop 实例
        tool_name: 工具名称

    Returns:
        bool: 是否调用了该工具
    """
    return any(
        tool.get('function', {}).get('name') == tool_name
        for tool in agent.tool_calls
    )


def print_tool_calls_summary(agent):
    """
    打印工具调用摘要

    Args:
        agent: AgentLoop 实例
    """
    print(f"\nTool calls made: {len(agent.tool_calls)}")
    for i, call in enumerate(agent.tool_calls):
        func = call.get('function', {})
        print(f"  {i+1}. {func.get('name', 'unknown')}")
        args = func.get('arguments', {})
        if args:
            # 只显示前 3 个参数
            args_str = ', '.join(f"{k}={v}" for k, v in list(args.items())[:3])
            if len(args) > 3:
                args_str += ", ..."
            print(f"      Args: {args_str}")
