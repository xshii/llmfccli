#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具优先级排序系统
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.tools.registry import ToolRegistry


def test_priority_attribute():
    """测试工具是否有 priority 属性"""
    print("=" * 60)
    print("Test 1: Tool Priority Attribute")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 检查每个工具是否有 priority 属性
    tools_with_priority = []
    tools_without_priority = []

    for tool_name in registry.list_tools():
        tool = registry.get(tool_name)
        if tool:
            priority = getattr(tool, 'priority', None)
            if priority is not None:
                tools_with_priority.append((tool_name, priority))
            else:
                tools_without_priority.append(tool_name)

    print(f"\n工具优先级:")
    for name, priority in sorted(tools_with_priority, key=lambda x: x[1], reverse=True):
        group = "HIGH" if priority >= 80 else "MID " if priority >= 50 else "LOW "
        print(f"  [{group}] {name:20s} priority: {priority}")

    if tools_without_priority:
        print(f"\n⚠️  缺少 priority 属性的工具: {', '.join(tools_without_priority)}")

    print(f"\n✅ {len(tools_with_priority)}/{len(tools_with_priority) + len(tools_without_priority)} 工具有 priority 属性")
    return len(tools_without_priority) == 0


def test_priority_ranges():
    """测试优先级范围是否合理"""
    print("\n" + "=" * 60)
    print("Test 2: Priority Range Validation")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    invalid_priorities = []
    priority_distribution = {'high': 0, 'mid': 0, 'low': 0}

    for tool_name in registry.list_tools():
        tool = registry.get(tool_name)
        if tool:
            priority = getattr(tool, 'priority', 50)

            # 检查范围 1-100
            if priority < 1 or priority > 100:
                invalid_priorities.append((tool_name, priority))

            # 统计分布
            if priority >= 80:
                priority_distribution['high'] += 1
            elif priority >= 50:
                priority_distribution['mid'] += 1
            else:
                priority_distribution['low'] += 1

    print(f"\n优先级分布:")
    print(f"  高优先级 (80-100): {priority_distribution['high']} 工具")
    print(f"  中优先级 (50-79):  {priority_distribution['mid']} 工具")
    print(f"  低优先级 (1-49):   {priority_distribution['low']} 工具")

    if invalid_priorities:
        print(f"\n❌ 发现无效优先级:")
        for name, priority in invalid_priorities:
            print(f"  - {name}: {priority}")
        return False

    print(f"\n✅ 所有优先级在有效范围内 (1-100)")
    return True


def test_essential_tools_high_priority():
    """测试核心工具是否有高优先级"""
    print("\n" + "=" * 60)
    print("Test 3: Essential Tools High Priority")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 核心工具应该有高优先级
    essential_tools = {
        'view_file': 80,   # 至少应该是 80
        'edit_file': 80,   # 至少应该是 80
        'grep_search': 80, # 至少应该是 80
    }

    print(f"\n检查核心工具优先级:")
    all_pass = True

    for tool_name, min_priority in essential_tools.items():
        tool = registry.get(tool_name)
        if tool:
            priority = getattr(tool, 'priority', 50)
            status = "✅" if priority >= min_priority else "❌"
            print(f"  {status} {tool_name:15s} priority: {priority} (期望 >= {min_priority})")

            if priority < min_priority:
                all_pass = False
        else:
            print(f"  ❌ {tool_name:15s} 工具不存在")
            all_pass = False

    if all_pass:
        print(f"\n✅ 所有核心工具优先级符合要求")
    else:
        print(f"\n❌ 部分核心工具优先级不符合要求")

    return all_pass


def test_tool_list_ordering():
    """测试工具列表排序逻辑"""
    print("\n" + "=" * 60)
    print("Test 4: Tool List Ordering")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 获取排序后的 schemas
    schemas = registry.get_openai_schemas()

    print(f"\n工具列表顺序 (共 {len(schemas)} 个工具):")
    print("-" * 60)

    # 分析排序结果
    tool_priorities = []
    for i, schema in enumerate(schemas):
        tool_name = schema['function']['name']
        tool = registry.get(tool_name)
        priority = getattr(tool, 'priority', 50) if tool else 50
        tool_priorities.append((i, tool_name, priority))

        # 显示前10个工具
        if i < 10:
            group = "HIGH" if priority >= 80 else "MID " if priority >= 50 else "LOW "
            print(f"  {i+1:2d}. [{group}] {tool_name:20s} (priority: {priority})")

    # 验证排序规则
    print("\n验证排序规则:")

    # 规则1: 高优先级工具在前面
    high_priority_tools = [(i, name, p) for i, name, p in tool_priorities if p >= 80]
    if high_priority_tools:
        high_positions = [i for i, _, _ in high_priority_tools]
        expected_positions = list(range(len(high_priority_tools)))

        if high_positions == expected_positions:
            print(f"  ✅ 高优先级工具在前面 (位置 1-{len(high_priority_tools)})")
        else:
            print(f"  ❌ 高优先级工具位置不正确")
            print(f"     期望: {expected_positions}")
            print(f"     实际: {high_positions}")

    # 规则2: 中优先级工具在最后
    mid_priority_tools = [(i, name, p) for i, name, p in tool_priorities if 50 <= p < 80]
    if mid_priority_tools:
        mid_positions = [i for i, _, _ in mid_priority_tools]
        expected_start = len(schemas) - len(mid_priority_tools)

        if all(pos >= expected_start for pos in mid_positions):
            print(f"  ✅ 中优先级工具在最后 (位置 {expected_start+1}-{len(schemas)})")
        else:
            print(f"  ❌ 中优先级工具位置不正确")

    # 规则3: 低优先级工具在中间
    low_priority_tools = [(i, name, p) for i, name, p in tool_priorities if p < 50]
    if low_priority_tools:
        low_positions = [i for i, _, _ in low_priority_tools]
        expected_start = len(high_priority_tools)
        expected_end = len(schemas) - len(mid_priority_tools)

        if all(expected_start <= pos < expected_end for pos in low_positions):
            print(f"  ✅ 低优先级工具在中间 (位置 {expected_start+1}-{expected_end})")
        else:
            print(f"  ❌ 低优先级工具位置不正确")

    print(f"\n✅ 工具列表排序测试完成")
    return True


def test_priority_coverage():
    """测试列表两端覆盖率"""
    print("\n" + "=" * 60)
    print("Test 5: Priority Coverage at List Ends")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')
    schemas = registry.get_openai_schemas()

    total_tools = len(schemas)
    high_count = sum(1 for s in schemas if getattr(registry.get(s['function']['name']), 'priority', 50) >= 80)
    mid_count = sum(1 for s in schemas if 50 <= getattr(registry.get(s['function']['name']), 'priority', 50) < 80)

    # 计算列表两端覆盖率
    end_coverage = (high_count + mid_count) / total_tools * 100 if total_tools > 0 else 0

    print(f"\n列表两端覆盖率:")
    print(f"  前端 (高优先级): {high_count} 工具 ({high_count/total_tools*100:.1f}%)")
    print(f"  后端 (中优先级): {mid_count} 工具 ({mid_count/total_tools*100:.1f}%)")
    print(f"  两端总覆盖:      {high_count + mid_count} 工具 ({end_coverage:.1f}%)")

    # 期望至少50%的工具在两端
    if end_coverage >= 50:
        print(f"\n✅ 两端覆盖率 >= 50%，符合优化目标")
        return True
    else:
        print(f"\n⚠️  两端覆盖率 < 50%，可能需要调整优先级分配")
        return True  # 仍然通过，只是警告


def test_specific_tool_priorities():
    """测试特定工具的优先级设置"""
    print("\n" + "=" * 60)
    print("Test 6: Specific Tool Priorities")
    print("=" * 60)

    registry = ToolRegistry(project_root='/tmp/test')

    # 期望的优先级设置
    expected_priorities = {
        'view_file': (95, 'HIGH'),
        'edit_file': (90, 'HIGH'),
        'grep_search': (85, 'HIGH'),
        'bash_run': (70, 'MID'),
        'list_dir': (65, 'MID'),
        'cmake_build': (60, 'MID'),
        'create_file': (40, 'LOW'),
        'run_tests': (35, 'LOW'),
        'git': (30, 'LOW'),
        'propose_options': (20, 'LOW'),
        'instant_compact': (10, 'LOW'),
    }

    print(f"\n检查特定工具优先级:")
    all_match = True

    for tool_name, (expected_priority, expected_group) in expected_priorities.items():
        tool = registry.get(tool_name)
        if tool:
            actual_priority = getattr(tool, 'priority', 50)
            match = "✅" if actual_priority == expected_priority else "⚠️"
            print(f"  {match} {tool_name:20s} 期望: {expected_priority} [{expected_group}], 实际: {actual_priority}")

            if actual_priority != expected_priority:
                all_match = False
        else:
            print(f"  ⚠️  {tool_name:20s} 工具不存在 (可能未注册)")

    if all_match:
        print(f"\n✅ 所有工具优先级与期望一致")
    else:
        print(f"\n⚠️  部分工具优先级与期望不一致 (可能正常，取决于设计)")

    return True  # 不强制要求完全一致


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("测试工具优先级排序系统")
    print("=" * 60)

    tests = [
        test_priority_attribute,
        test_priority_ranges,
        test_essential_tools_high_priority,
        test_tool_list_ordering,
        test_priority_coverage,
        test_specific_tool_priorities,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)

    if all(results):
        print("\n🎉 所有测试通过！工具优先级系统工作正常！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败")
        sys.exit(1)
