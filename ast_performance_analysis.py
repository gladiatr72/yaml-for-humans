#!/usr/bin/env python3
"""
AST-based performance analysis for yaml-for-humans.

This script analyzes Python source code using AST parsing to identify
performance characteristics, bottlenecks, and optimization opportunities.
"""

import ast
import sys
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
import time

class PerformanceAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes performance characteristics."""

    def __init__(self, filename: str):
        self.filename = filename
        self.metrics = {
            'loops': [],
            'comprehensions': [],
            'function_calls': [],
            'method_calls': [],
            'string_operations': [],
            'dict_operations': [],
            'list_operations': [],
            'regex_patterns': [],
            'class_definitions': [],
            'function_definitions': [],
            'complex_expressions': [],
            'recursive_calls': [],
            'memory_allocations': [],
            'io_operations': [],
            'imports': [],
        }
        self.line_complexity = defaultdict(int)
        self.current_function = None
        self.current_class = None
        self.complexity_score = 0

    def visit_ClassDef(self, node):
        """Analyze class definitions."""
        old_class = self.current_class
        self.current_class = node.name

        # Count methods and inheritance complexity
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        bases_count = len(node.bases)

        self.metrics['class_definitions'].append({
            'name': node.name,
            'line': node.lineno,
            'methods_count': len(methods),
            'bases_count': bases_count,
            'complexity': len(methods) + bases_count * 2
        })

        self.complexity_score += len(methods) + bases_count * 2
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Analyze function definitions."""
        old_function = self.current_function
        self.current_function = node.name

        # Calculate function complexity
        args_count = len(node.args.args)
        defaults_count = len(node.args.defaults)

        self.metrics['function_definitions'].append({
            'name': node.name,
            'class': self.current_class,
            'line': node.lineno,
            'args_count': args_count,
            'defaults_count': defaults_count,
            'has_varargs': node.args.vararg is not None,
            'has_kwargs': node.args.kwarg is not None,
        })

        self.complexity_score += args_count + defaults_count
        self.generic_visit(node)
        self.current_function = old_function

    def visit_For(self, node):
        """Analyze for loops."""
        self.metrics['loops'].append({
            'type': 'for',
            'line': node.lineno,
            'function': self.current_function,
            'class': self.current_class,
            'target_type': type(node.target).__name__,
            'iter_type': type(node.iter).__name__,
        })
        self.line_complexity[node.lineno] += 3
        self.complexity_score += 3
        self.generic_visit(node)

    def visit_While(self, node):
        """Analyze while loops."""
        self.metrics['loops'].append({
            'type': 'while',
            'line': node.lineno,
            'function': self.current_function,
            'class': self.current_class,
            'test_type': type(node.test).__name__,
        })
        self.line_complexity[node.lineno] += 4
        self.complexity_score += 4
        self.generic_visit(node)

    def visit_ListComp(self, node):
        """Analyze list comprehensions."""
        generators_count = len(node.generators)
        self.metrics['comprehensions'].append({
            'type': 'list',
            'line': node.lineno,
            'function': self.current_function,
            'generators_count': generators_count,
            'has_conditions': any(g.ifs for g in node.generators)
        })
        self.line_complexity[node.lineno] += generators_count
        self.complexity_score += generators_count
        self.generic_visit(node)

    def visit_DictComp(self, node):
        """Analyze dict comprehensions."""
        generators_count = len(node.generators)
        self.metrics['comprehensions'].append({
            'type': 'dict',
            'line': node.lineno,
            'function': self.current_function,
            'generators_count': generators_count,
            'has_conditions': any(g.ifs for g in node.generators)
        })
        self.line_complexity[node.lineno] += generators_count
        self.complexity_score += generators_count
        self.generic_visit(node)

    def visit_SetComp(self, node):
        """Analyze set comprehensions."""
        generators_count = len(node.generators)
        self.metrics['comprehensions'].append({
            'type': 'set',
            'line': node.lineno,
            'function': self.current_function,
            'generators_count': generators_count,
            'has_conditions': any(g.ifs for g in node.generators)
        })
        self.line_complexity[node.lineno] += generators_count
        self.complexity_score += generators_count
        self.generic_visit(node)

    def visit_Call(self, node):
        """Analyze function and method calls."""
        if isinstance(node.func, ast.Attribute):
            # Method call
            method_name = node.func.attr

            # Check for potentially expensive operations
            if method_name in ['append', 'extend', 'insert', 'pop', 'remove']:
                self.metrics['list_operations'].append({
                    'operation': method_name,
                    'line': node.lineno,
                    'function': self.current_function,
                    'args_count': len(node.args)
                })
            elif method_name in ['get', 'setdefault', 'pop', 'update', 'keys', 'values', 'items']:
                self.metrics['dict_operations'].append({
                    'operation': method_name,
                    'line': node.lineno,
                    'function': self.current_function,
                    'args_count': len(node.args)
                })
            elif method_name in ['split', 'join', 'replace', 'strip', 'format', 'encode', 'decode']:
                self.metrics['string_operations'].append({
                    'operation': method_name,
                    'line': node.lineno,
                    'function': self.current_function,
                    'args_count': len(node.args)
                })
            elif method_name in ['read', 'write', 'seek', 'tell', 'flush']:
                self.metrics['io_operations'].append({
                    'operation': method_name,
                    'line': node.lineno,
                    'function': self.current_function,
                    'args_count': len(node.args)
                })

            self.metrics['method_calls'].append({
                'method': method_name,
                'line': node.lineno,
                'function': self.current_function,
                'args_count': len(node.args),
                'kwargs_count': len(node.keywords)
            })

        elif isinstance(node.func, ast.Name):
            # Function call
            func_name = node.func.id

            # Check for recursive calls
            if func_name == self.current_function:
                self.metrics['recursive_calls'].append({
                    'function': func_name,
                    'line': node.lineno,
                    'args_count': len(node.args)
                })

            # Check for memory allocation patterns
            if func_name in ['list', 'dict', 'set', 'tuple', 'str']:
                self.metrics['memory_allocations'].append({
                    'type': func_name,
                    'line': node.lineno,
                    'function': self.current_function,
                    'args_count': len(node.args)
                })

            self.metrics['function_calls'].append({
                'function': func_name,
                'line': node.lineno,
                'caller': self.current_function,
                'args_count': len(node.args),
                'kwargs_count': len(node.keywords)
            })

        self.line_complexity[node.lineno] += 1
        self.complexity_score += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        """Analyze imports."""
        for alias in node.names:
            self.metrics['imports'].append({
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Analyze from imports."""
        module = node.module or ''
        for alias in node.names:
            self.metrics['imports'].append({
                'module': f"{module}.{alias.name}" if module else alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'from_import'
            })
        self.generic_visit(node)

    def visit_BinOp(self, node):
        """Analyze binary operations for complexity."""
        if isinstance(node.op, (ast.Mult, ast.Pow)):
            self.line_complexity[node.lineno] += 2
            self.complexity_score += 2
        else:
            self.line_complexity[node.lineno] += 1
            self.complexity_score += 1
        self.generic_visit(node)


def analyze_file(filepath: Path) -> PerformanceAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Could not read {filepath} (encoding issue)")
        return None

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        print(f"Warning: Syntax error in {filepath}: {e}")
        return None

    analyzer = PerformanceAnalyzer(str(filepath))
    analyzer.visit(tree)
    return analyzer


def analyze_repository():
    """Perform AST-based performance analysis on the entire repository."""
    src_dir = Path('src/yaml_for_humans')
    if not src_dir.exists():
        print(f"Source directory {src_dir} not found")
        return

    python_files = list(src_dir.glob('**/*.py'))
    print(f"Analyzing {len(python_files)} Python files...\n")

    all_metrics = defaultdict(list)
    total_complexity = 0
    file_results = {}

    start_time = time.time()

    for filepath in python_files:
        print(f"Analyzing {filepath}")
        analyzer = analyze_file(filepath)
        if analyzer:
            file_results[str(filepath)] = analyzer
            total_complexity += analyzer.complexity_score

            # Aggregate metrics
            for metric_type, items in analyzer.metrics.items():
                all_metrics[metric_type].extend(items)

    analysis_time = time.time() - start_time

    # Generate performance analysis report
    generate_report(file_results, all_metrics, total_complexity, analysis_time)


def generate_report(file_results: Dict, all_metrics: Dict, total_complexity: int, analysis_time: float):
    """Generate comprehensive performance analysis report."""

    print("\n" + "="*80)
    print("AST-BASED PERFORMANCE ANALYSIS REPORT")
    print("="*80)

    print(f"\nAnalysis completed in {analysis_time:.2f} seconds")
    print(f"Total complexity score: {total_complexity}")
    print(f"Files analyzed: {len(file_results)}")

    # File complexity ranking
    print("\n1. FILE COMPLEXITY RANKING")
    print("-" * 40)
    complexity_by_file = [(filepath, analyzer.complexity_score)
                          for filepath, analyzer in file_results.items()]
    complexity_by_file.sort(key=lambda x: x[1], reverse=True)

    for filepath, complexity in complexity_by_file[:10]:
        filename = Path(filepath).name
        print(f"{filename:30} {complexity:5d}")

    # Function complexity analysis
    print("\n2. FUNCTION COMPLEXITY ANALYSIS")
    print("-" * 40)
    functions = all_metrics['function_definitions']
    if functions:
        complex_functions = sorted(functions,
                                 key=lambda x: x['args_count'] + x['defaults_count'],
                                 reverse=True)[:10]

        for func in complex_functions:
            name = f"{func['class']}.{func['name']}" if func['class'] else func['name']
            complexity = func['args_count'] + func['defaults_count']
            print(f"{name:40} {complexity:3d} args ({func['line']:4d})")

    # Loop analysis
    print("\n3. LOOP ANALYSIS")
    print("-" * 40)
    loops = all_metrics['loops']
    loop_types = Counter(loop['type'] for loop in loops)

    print(f"Total loops: {len(loops)}")
    for loop_type, count in loop_types.items():
        print(f"  {loop_type} loops: {count}")

    # Hot spots by line complexity
    print("\n4. COMPLEXITY HOT SPOTS")
    print("-" * 40)
    all_line_complexity = defaultdict(int)
    for analyzer in file_results.values():
        for line, complexity in analyzer.line_complexity.items():
            filepath = analyzer.filename
            all_line_complexity[(filepath, line)] += complexity

    hot_spots = sorted(all_line_complexity.items(), key=lambda x: x[1], reverse=True)[:10]
    for (filepath, line), complexity in hot_spots:
        filename = Path(filepath).name
        print(f"{filename}:{line:4d} {complexity:3d}")

    # Method call frequency analysis
    print("\n5. METHOD CALL FREQUENCY")
    print("-" * 40)
    method_calls = all_metrics['method_calls']
    method_freq = Counter(call['method'] for call in method_calls)

    for method, count in method_freq.most_common(10):
        print(f"{method:20} {count:4d} calls")

    # Memory allocation patterns
    print("\n6. MEMORY ALLOCATION PATTERNS")
    print("-" * 40)
    allocations = all_metrics['memory_allocations']
    alloc_types = Counter(alloc['type'] for alloc in allocations)

    for alloc_type, count in alloc_types.items():
        print(f"{alloc_type:10} {count:4d} allocations")

    # Comprehension usage
    print("\n7. COMPREHENSION USAGE")
    print("-" * 40)
    comprehensions = all_metrics['comprehensions']
    comp_types = Counter(comp['type'] for comp in comprehensions)

    for comp_type, count in comp_types.items():
        print(f"{comp_type} comprehensions: {count}")

    # Performance bottleneck identification
    print("\n8. POTENTIAL PERFORMANCE BOTTLENECKS")
    print("-" * 40)

    # Nested loops
    nested_loops = []
    for analyzer in file_results.values():
        for loop in analyzer.metrics['loops']:
            if analyzer.line_complexity[loop['line']] > 5:
                nested_loops.append((analyzer.filename, loop))

    if nested_loops:
        print("High-complexity loops (potential nested loops):")
        for filepath, loop in nested_loops[:5]:
            filename = Path(filepath).name
            print(f"  {filename}:{loop['line']} ({loop['type']} loop)")

    # String operations in loops
    string_ops_in_loops = 0
    for analyzer in file_results.values():
        loop_lines = {loop['line'] for loop in analyzer.metrics['loops']}
        for string_op in analyzer.metrics['string_operations']:
            if any(abs(string_op['line'] - loop_line) <= 5 for loop_line in loop_lines):
                string_ops_in_loops += 1

    if string_ops_in_loops > 0:
        print(f"String operations near loops: {string_ops_in_loops} (potential inefficiency)")

    # Recursive calls
    recursive_calls = all_metrics['recursive_calls']
    if recursive_calls:
        print(f"Recursive calls detected: {len(recursive_calls)}")
        for call in recursive_calls[:3]:
            print(f"  {call['function']} (line {call['line']})")

    # IO operations
    io_ops = all_metrics['io_operations']
    if io_ops:
        print(f"I/O operations: {len(io_ops)}")
        io_types = Counter(op['operation'] for op in io_ops)
        for op_type, count in io_types.most_common(3):
            print(f"  {op_type}: {count}")

    print("\n9. OPTIMIZATION RECOMMENDATIONS")
    print("-" * 40)

    # Generate specific recommendations based on analysis
    recommendations = []

    # Check for excessive string operations
    string_ops = len(all_metrics['string_operations'])
    if string_ops > 50:
        recommendations.append(f"Consider optimizing string operations ({string_ops} found)")

    # Check for list operations that could be optimized
    list_ops = all_metrics['list_operations']
    expensive_list_ops = [op for op in list_ops if op['operation'] in ['insert', 'pop', 'remove']]
    if len(expensive_list_ops) > 10:
        recommendations.append(f"Consider using deque for frequent insert/pop operations ({len(expensive_list_ops)} found)")

    # Check for dict operations
    dict_gets = [op for op in all_metrics['dict_operations'] if op['operation'] == 'get']
    if len(dict_gets) > 20:
        recommendations.append("Consider using defaultdict or setdefault for frequent dict.get() operations")

    # Check for regex patterns
    if len(all_metrics.get('regex_patterns', [])) > 5:
        recommendations.append("Consider compiling regex patterns for reuse")

    # Function complexity recommendations
    complex_funcs = [f for f in functions if f['args_count'] > 5]
    if complex_funcs:
        recommendations.append(f"Consider refactoring functions with many parameters ({len(complex_funcs)} found)")

    if not recommendations:
        recommendations.append("Code appears well-optimized based on static analysis")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    print("\n" + "="*80)


if __name__ == '__main__':
    analyze_repository()