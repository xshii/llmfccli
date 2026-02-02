# -*- coding: utf-8 -*-
"""
Agent Benchmark - 基于 E2E 用例的性能基准测试

评估维度：
1. 成功率 (Success Rate)
2. 执行时间 (Execution Time)
3. 工具调用次数 (Tool Calls)
4. Token 使用量 (Token Usage)
5. 迭代次数 (Iterations)
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.agent.loop import AgentLoop
from backend.llm.client import OllamaClient


@dataclass
class BenchmarkResult:
    """单个测试用例的结果"""
    name: str
    success: bool
    duration: float  # 秒
    tool_calls: int
    iterations: int
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkReport:
    """整体基准测试报告"""
    timestamp: str
    model: str
    total_cases: int
    passed: int
    failed: int
    total_duration: float
    avg_duration: float
    total_tool_calls: int
    avg_tool_calls: float
    results: List[BenchmarkResult] = field(default_factory=list)


class AgentBenchmark:
    """Agent 性能基准测试"""

    def __init__(self, project_root: str, model: str = "claude-qwen:latest"):
        self.project_root = project_root
        self.model = model
        self.results: List[BenchmarkResult] = []

    def _create_agent(self) -> AgentLoop:
        """创建新的 Agent 实例"""
        # 加载基础配置并覆盖 model
        from backend.llm.config import load_yaml_config
        base_config = load_yaml_config().get('ollama', {})
        base_config['model'] = self.model
        client = OllamaClient(config=base_config)
        agent = AgentLoop(client)
        agent.set_project_root(self.project_root)
        # 保存最后一个 agent 供 verbose 模式使用
        self._last_agent = agent
        return agent

    def _backup_fixtures(self):
        """备份 fixtures 目录"""
        import shutil
        import tempfile

        if not hasattr(self, '_backup_dir'):
            self._backup_dir = tempfile.mkdtemp(prefix='benchmark_backup_')
            shutil.copytree(self.project_root, self._backup_path, dirs_exist_ok=True)
            print(f"Fixtures backed up to: {self._backup_dir}")

    @property
    def _backup_path(self) -> str:
        return os.path.join(self._backup_dir, 'fixtures')

    def _reset_fixtures(self):
        """从备份恢复 fixtures"""
        import shutil

        if not hasattr(self, '_backup_dir') or not os.path.exists(self._backup_path):
            # 首次运行，创建备份
            self._backup_fixtures()
            return

        # 删除当前 fixtures，从备份恢复
        shutil.rmtree(self.project_root)
        shutil.copytree(self._backup_path, self.project_root)

    def _cleanup_backup(self):
        """清理备份目录"""
        import shutil
        if hasattr(self, '_backup_dir') and os.path.exists(self._backup_dir):
            shutil.rmtree(self._backup_dir)
            print(f"Backup cleaned up: {self._backup_dir}")

    # ========== Benchmark Cases ==========

    def bench_file_location(self) -> BenchmarkResult:
        """
        Case 1: 文件定位与功能实现

        任务：在 network_handler.cpp 添加超时重试机制
        评估：文件定位准确性、代码修改正确性
        """
        name = "file_location"
        agent = self._create_agent()

        user_input = """
        在 network_handler.cpp 的 connect() 函数中添加连接超时和重试机制。
        要求：超时时间 5 秒，最多重试 3 次，每次重试间隔 1 秒。
        """

        start = time.time()
        try:
            response = agent.run(user_input)
            duration = time.time() - start

            # 验证
            target_file = os.path.join(self.project_root, 'src/network_handler.cpp')
            with open(target_file, 'r') as f:
                content = f.read()

            has_timeout = 'timeout' in content.lower() or 'retry' in content.lower()
            has_edit = any(
                t.get('function', {}).get('name') == 'edit_file'
                for t in agent.tool_calls
            )

            success = has_timeout and has_edit

            return BenchmarkResult(
                name=name,
                success=success,
                duration=duration,
                tool_calls=len(agent.tool_calls),
                iterations=len([m for m in agent.conversation_history if m['role'] == 'assistant']),
                details={
                    'has_timeout_code': has_timeout,
                    'has_edit_call': has_edit,
                    'tools_used': [t.get('function', {}).get('name') for t in agent.tool_calls]
                }
            )
        except Exception as e:
            return BenchmarkResult(
                name=name,
                success=False,
                duration=time.time() - start,
                tool_calls=len(agent.tool_calls) if agent else 0,
                iterations=0,
                error=str(e)
            )

    def bench_compile_fix(self) -> BenchmarkResult:
        """
        Case 2: 编译错误自动修复

        任务：编译项目并修复所有编译错误
        评估：错误识别准确性、修复有效性、循环控制
        """
        name = "compile_fix"
        agent = self._create_agent()

        user_input = "编译项目并修复所有编译错误"

        start = time.time()
        try:
            response = agent.run(user_input)
            duration = time.time() - start

            # 统计编译和修复次数
            bash_calls = [t for t in agent.tool_calls if t.get('function', {}).get('name') == 'bash_run']
            edit_calls = [t for t in agent.tool_calls if t.get('function', {}).get('name') == 'edit_file']

            compile_count = len([c for c in bash_calls if 'cmake' in str(c) or 'make' in str(c)])

            # 验证修复
            json_parser = os.path.join(self.project_root, 'src/parser/json_parser.cpp')
            if os.path.exists(json_parser):
                with open(json_parser, 'r') as f:
                    content = f.read()
                fixed = 'poss' not in content  # 拼写错误已修复
            else:
                fixed = False

            success = compile_count >= 2 and len(edit_calls) > 0 and fixed

            return BenchmarkResult(
                name=name,
                success=success,
                duration=duration,
                tool_calls=len(agent.tool_calls),
                iterations=len([m for m in agent.conversation_history if m['role'] == 'assistant']),
                details={
                    'compile_attempts': compile_count,
                    'edit_attempts': len(edit_calls),
                    'error_fixed': fixed
                }
            )
        except Exception as e:
            return BenchmarkResult(
                name=name,
                success=False,
                duration=time.time() - start,
                tool_calls=len(agent.tool_calls) if agent else 0,
                iterations=0,
                error=str(e)
            )

    def bench_context_preservation(self) -> BenchmarkResult:
        """
        Case 3: 上下文保持（多轮对话）

        任务：创建类后添加线程安全
        评估：上下文记忆、增量修改能力
        """
        name = "context_preservation"
        agent = self._create_agent()

        # 第 1 轮
        round1 = """
        创建一个 DataProcessor 类，包含以下功能：
        - process(data) 方法处理数据
        - validate(data) 方法验证数据
        文件路径: src/data/data_processor.h 和 src/data/data_processor.cpp
        """

        # 第 2 轮
        round2 = "为 DataProcessor 类添加线程安全，使用互斥锁保护 process 和 validate 方法"

        start = time.time()
        try:
            response1 = agent.run(round1)
            response2 = agent.run(round2)
            duration = time.time() - start

            # 验证
            header = os.path.join(self.project_root, 'src/data/data_processor.h')
            impl = os.path.join(self.project_root, 'src/data/data_processor.cpp')

            if os.path.exists(header) and os.path.exists(impl):
                with open(header, 'r') as f:
                    h_content = f.read()
                with open(impl, 'r') as f:
                    cpp_content = f.read()

                has_class = 'class DataProcessor' in h_content
                has_mutex = 'mutex' in h_content.lower()
                has_lock = 'lock' in cpp_content.lower()
                preserved_methods = 'process' in h_content and 'validate' in h_content
            else:
                has_class = has_mutex = has_lock = preserved_methods = False

            success = has_class and has_mutex and has_lock and preserved_methods

            return BenchmarkResult(
                name=name,
                success=success,
                duration=duration,
                tool_calls=len(agent.tool_calls),
                iterations=len([m for m in agent.conversation_history if m['role'] == 'assistant']),
                details={
                    'class_created': has_class,
                    'mutex_added': has_mutex,
                    'lock_used': has_lock,
                    'methods_preserved': preserved_methods,
                    'conversation_turns': len(agent.conversation_history)
                }
            )
        except Exception as e:
            return BenchmarkResult(
                name=name,
                success=False,
                duration=time.time() - start,
                tool_calls=len(agent.tool_calls) if agent else 0,
                iterations=0,
                error=str(e)
            )

    def bench_code_search(self) -> BenchmarkResult:
        """
        Case 4: 代码搜索与理解

        任务：找到所有使用 NetworkHandler 的地方
        评估：搜索准确性、结果完整性
        """
        name = "code_search"
        agent = self._create_agent()

        user_input = "找到项目中所有使用 NetworkHandler 类的地方，列出文件和行号"

        start = time.time()
        try:
            response = agent.run(user_input)
            duration = time.time() - start

            # 验证
            grep_calls = [t for t in agent.tool_calls if t.get('function', {}).get('name') == 'grep_search']
            view_calls = [t for t in agent.tool_calls if t.get('function', {}).get('name') == 'view_file']

            # 检查是否找到了关键文件
            found_network = 'network_handler' in response.lower()
            found_http = 'http' in response.lower()

            success = len(grep_calls) > 0 and found_network

            return BenchmarkResult(
                name=name,
                success=success,
                duration=duration,
                tool_calls=len(agent.tool_calls),
                iterations=len([m for m in agent.conversation_history if m['role'] == 'assistant']),
                details={
                    'grep_calls': len(grep_calls),
                    'view_calls': len(view_calls),
                    'found_network_handler': found_network,
                    'found_http_module': found_http
                }
            )
        except Exception as e:
            return BenchmarkResult(
                name=name,
                success=False,
                duration=time.time() - start,
                tool_calls=len(agent.tool_calls) if agent else 0,
                iterations=0,
                error=str(e)
            )

    def bench_simple_edit(self) -> BenchmarkResult:
        """
        Case 5: 简单代码修改

        任务：添加日志输出
        评估：精准修改能力、代码正确性
        """
        name = "simple_edit"
        agent = self._create_agent()

        user_input = """
        在 network_handler.cpp 的 connect() 函数开头添加一行日志：
        std::cout << "Connecting to server..." << std::endl;
        """

        start = time.time()
        try:
            response = agent.run(user_input)
            duration = time.time() - start

            # 验证
            target = os.path.join(self.project_root, 'src/network_handler.cpp')
            with open(target, 'r') as f:
                content = f.read()

            has_log = 'Connecting to server' in content
            has_edit = any(t.get('function', {}).get('name') == 'edit_file' for t in agent.tool_calls)

            success = has_log and has_edit

            return BenchmarkResult(
                name=name,
                success=success,
                duration=duration,
                tool_calls=len(agent.tool_calls),
                iterations=len([m for m in agent.conversation_history if m['role'] == 'assistant']),
                details={
                    'log_added': has_log,
                    'edit_called': has_edit
                }
            )
        except Exception as e:
            return BenchmarkResult(
                name=name,
                success=False,
                duration=time.time() - start,
                tool_calls=len(agent.tool_calls) if agent else 0,
                iterations=0,
                error=str(e)
            )

    def bench_write_test(self) -> BenchmarkResult:
        """
        Case 6: 编写测试并调试运行

        任务：为 JsonParser 类编写单元测试，编译运行
        评估：测试编写、编译修复、调试能力
        """
        name = "write_test"
        agent = self._create_agent()

        user_input = """
为 src/parser/json_parser.cpp 中的 JsonParser 类编写单元测试。
要求：
1. 创建 test_json_parser.cpp
2. 使用 assert 测试 parse() 和 get_value() 方法
3. 不使用外部测试框架，直接 g++ 编译运行
4. 确保测试通过
"""

        start = time.time()
        try:
            response = agent.run(user_input)
            duration = time.time() - start

            # 验证：检查是否创建了测试文件
            create_calls = [t for t in agent.tool_calls
                           if t.get('function', {}).get('name') == 'create_file']
            test_created = any('test' in str(c).lower() and 'json' in str(c).lower()
                              for c in create_calls)

            # 检查是否有编译尝试 (g++ 或 cmake)
            bash_calls = [t for t in agent.tool_calls
                         if t.get('function', {}).get('name') == 'bash_run']
            compile_attempts = len([c for c in bash_calls
                                   if 'g++' in str(c) or 'cmake' in str(c).lower()])

            # 检查是否有运行测试
            run_attempts = len([c for c in bash_calls
                               if './test' in str(c) or 'test_json' in str(c)])

            success = test_created and compile_attempts > 0

            return BenchmarkResult(
                name=name,
                success=success,
                duration=duration,
                tool_calls=len(agent.tool_calls),
                iterations=len([m for m in agent.conversation_history if m['role'] == 'assistant']),
                details={
                    'test_created': test_created,
                    'compile_attempts': compile_attempts,
                    'run_attempts': run_attempts,
                }
            )
        except Exception as e:
            return BenchmarkResult(
                name=name,
                success=False,
                duration=time.time() - start,
                tool_calls=len(agent.tool_calls) if agent else 0,
                iterations=0,
                error=str(e)
            )

    # ========== Run Benchmark ==========

    def run_all(self, iterations: int = 1) -> BenchmarkReport:
        """运行所有基准测试"""
        all_results = []

        benchmarks = [
            ("file_location", self.bench_file_location),
            ("compile_fix", self.bench_compile_fix),
            ("context_preservation", self.bench_context_preservation),
            ("code_search", self.bench_code_search),
            ("simple_edit", self.bench_simple_edit),
            ("write_test", self.bench_write_test),
        ]

        total_start = time.time()

        for iteration in range(iterations):
            print(f"\n{'='*60}")
            print(f"Iteration {iteration + 1}/{iterations}")
            print('='*60)

            for name, bench_func in benchmarks:
                print(f"\n[{name}] Running...")
                self._reset_fixtures()

                result = bench_func()
                all_results.append(result)

                status = "PASS" if result.success else "FAIL"
                print(f"[{name}] {status} - {result.duration:.2f}s, {result.tool_calls} tools")
                if result.error:
                    print(f"  Error: {result.error}")

        total_duration = time.time() - total_start

        # 清理备份
        self._cleanup_backup()

        # 生成报告
        passed = len([r for r in all_results if r.success])
        failed = len(all_results) - passed

        report = BenchmarkReport(
            timestamp=datetime.now().isoformat(),
            model=self.model,
            total_cases=len(all_results),
            passed=passed,
            failed=failed,
            total_duration=total_duration,
            avg_duration=sum(r.duration for r in all_results) / len(all_results) if all_results else 0,
            total_tool_calls=sum(r.tool_calls for r in all_results),
            avg_tool_calls=sum(r.tool_calls for r in all_results) / len(all_results) if all_results else 0,
            results=all_results
        )

        return report

    def print_report(self, report: BenchmarkReport):
        """打印报告"""
        print("\n" + "="*60)
        print("BENCHMARK REPORT")
        print("="*60)
        print(f"Timestamp: {report.timestamp}")
        print(f"Model: {report.model}")
        print(f"\nResults: {report.passed}/{report.total_cases} passed")
        print(f"Success Rate: {report.passed/report.total_cases*100:.1f}%")
        print(f"\nTotal Duration: {report.total_duration:.2f}s")
        print(f"Avg Duration: {report.avg_duration:.2f}s")
        print(f"Total Tool Calls: {report.total_tool_calls}")
        print(f"Avg Tool Calls: {report.avg_tool_calls:.1f}")

        print("\n" + "-"*60)
        print("DETAILED RESULTS")
        print("-"*60)

        for result in report.results:
            status = "PASS" if result.success else "FAIL"
            print(f"\n[{result.name}] {status}")
            print(f"  Duration: {result.duration:.2f}s")
            print(f"  Tool Calls: {result.tool_calls}")
            print(f"  Iterations: {result.iterations}")
            if result.error:
                print(f"  Error: {result.error}")
            if result.details:
                for k, v in result.details.items():
                    print(f"  {k}: {v}")

    def save_report(self, report: BenchmarkReport, output_file: str):
        """保存报告到 JSON"""
        data = asdict(report)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {output_file}")


def main():
    import argparse

    # 可用的测试用例
    CASES = {
        'file_location': '文件定位与功能实现',
        'compile_fix': '编译错误自动修复',
        'context_preservation': '上下文保持（多轮对话）',
        'code_search': '代码搜索与理解',
        'simple_edit': '简单代码修改',
        'write_test': '编写测试并调试运行',
    }

    parser = argparse.ArgumentParser(description='Agent Benchmark')
    parser.add_argument('--iterations', '-n', type=int, default=1,
                        help='Number of iterations')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output JSON file')
    parser.add_argument('--model', '-m', type=str, default='glm-4.7-flash:latest',
                        help='Model name')
    parser.add_argument('--case', '-c', type=str, default=None,
                        choices=list(CASES.keys()),
                        help='Run single case (default: all)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available cases')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show agent conversation')

    args = parser.parse_args()

    # 列出用例
    if args.list:
        print("Available benchmark cases:")
        for name, desc in CASES.items():
            print(f"  {name:25} - {desc}")
        return

    # 设置项目根目录
    project_root = os.path.join(os.path.dirname(__file__), '../fixtures/sample-cpp')

    print(f"Project Root: {project_root}")
    print(f"Model: {args.model}")

    benchmark = AgentBenchmark(project_root, args.model)

    # 运行单个用例或全部
    if args.case:
        print(f"Case: {args.case} ({CASES[args.case]})")
        benchmark._backup_fixtures()

        # 获取对应的方法
        bench_method = getattr(benchmark, f'bench_{args.case}')
        result = bench_method()

        status = "PASS" if result.success else "FAIL"
        print(f"\n{'='*60}")
        print(f"[{result.name}] {status}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Tool Calls: {result.tool_calls}")
        print(f"Iterations: {result.iterations}")
        if result.error:
            print(f"Error: {result.error}")
        if result.details:
            print("Details:")
            for k, v in result.details.items():
                print(f"  {k}: {v}")

        # Verbose 模式：显示对话历史
        if args.verbose and hasattr(benchmark, '_last_agent'):
            agent = benchmark._last_agent
            print(f"\n{'='*60}")
            print("CONVERSATION HISTORY")
            print('='*60)
            for msg in agent.conversation_history:
                role = msg['role'].upper()
                content = msg.get('content', '')
                if content:
                    print(f"\n[{role}]")
                    print(content[:500] + '...' if len(content) > 500 else content)
                # 显示工具调用
                if 'tool_calls' in msg:
                    for tc in msg['tool_calls']:
                        func = tc.get('function', {})
                        print(f"\n[TOOL CALL] {func.get('name')}")
                        args_str = func.get('arguments', '')
                        if len(args_str) > 200:
                            args_str = args_str[:200] + '...'
                        print(f"  Args: {args_str}")

        benchmark._cleanup_backup()
        return

    print(f"Iterations: {args.iterations}")
    report = benchmark.run_all(args.iterations)

    benchmark.print_report(report)

    if args.output:
        benchmark.save_report(report, args.output)
    else:
        # 默认保存到 benchmark 目录
        output_file = os.path.join(
            os.path.dirname(__file__),
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        benchmark.save_report(report, output_file)


if __name__ == '__main__':
    main()
