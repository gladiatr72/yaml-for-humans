#!/usr/bin/env python3
"""
AST-based performance analysis for yaml-for-humans.

This script analyzes the codebase for performance characteristics using AST parsing:
- Function complexity analysis
- Loop nesting depth
- Algorithmic complexity patterns
- Memory allocation patterns
- Call frequency estimation
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
import os


class PerformanceAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes performance characteristics."""

    def __init__(self, filename: str):
        self.filename = filename
        self.current_function = None
        self.current_class = None

        # Performance metrics
        self.function_complexity = {}
        self.loop_nesting = defaultdict(int)
        self.max_loop_nesting = defaultdict(int)
        self.current_loop_depth = 0

        # Algorithmic patterns
        self.list_operations = defaultdict(list)
        self.dict_operations = defaultdict(list)
        self.string_operations = defaultdict(list)
        self.comprehensions = defaultdict(list)

        # Call patterns
        self.function_calls = defaultdict(list)
        self.method_calls = defaultdict(list)
        self.builtin_calls = defaultdict(list)

        # Memory patterns
        self.object_creations = defaultdict(list)
        self.collection_sizes = defaultdict(list)

        # Control flow
        self.conditional_complexity = defaultdict(int)

    def get_function_key(self) -> str:
        """Get current function identifier."""
        if self.current_class and self.current_function:
            return f"{self.current_class}.{self.current_function}"
        elif self.current_function:
            return self.current_function
        else:
            return "<module>"

    def visit_FunctionDef(self, node):
        """Analyze function definitions."""
        old_function = self.current_function
        self.current_function = node.name
        func_key = self.get_function_key()

        # Calculate cyclomatic complexity approximation
        complexity = 1  # base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        self.function_complexity[func_key] = complexity

        # Analyze function body
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node):
        """Analyze class definitions."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_For(self, node):
        """Analyze for loops."""
        self.current_loop_depth += 1
        func_key = self.get_function_key()

        self.loop_nesting[func_key] += 1
        self.max_loop_nesting[func_key] = max(
            self.max_loop_nesting[func_key],
            self.current_loop_depth
        )

        # Check for potential O(n²) patterns
        if self.current_loop_depth > 1:
            self.list_operations[func_key].append(f"nested_loop_depth_{self.current_loop_depth}")

        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_While(self, node):
        """Analyze while loops."""
        self.current_loop_depth += 1
        func_key = self.get_function_key()

        self.loop_nesting[func_key] += 1
        self.max_loop_nesting[func_key] = max(
            self.max_loop_nesting[func_key],
            self.current_loop_depth
        )

        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_ListComp(self, node):
        """Analyze list comprehensions."""
        func_key = self.get_function_key()
        generators = len(node.generators)

        if generators > 1:
            self.comprehensions[func_key].append(f"nested_listcomp_{generators}")
        else:
            self.comprehensions[func_key].append("listcomp")

        self.generic_visit(node)

    def visit_DictComp(self, node):
        """Analyze dict comprehensions."""
        func_key = self.get_function_key()
        generators = len(node.generators)

        if generators > 1:
            self.comprehensions[func_key].append(f"nested_dictcomp_{generators}")
        else:
            self.comprehensions[func_key].append("dictcomp")

        self.generic_visit(node)

    def visit_SetComp(self, node):
        """Analyze set comprehensions."""
        func_key = self.get_function_key()
        generators = len(node.generators)

        if generators > 1:
            self.comprehensions[func_key].append(f"nested_setcomp_{generators}")
        else:
            self.comprehensions[func_key].append("setcomp")

        self.generic_visit(node)

    def visit_Call(self, node):
        """Analyze function/method calls."""
        func_key = self.get_function_key()

        if isinstance(node.func, ast.Name):
            # Function call
            func_name = node.func.id
            self.function_calls[func_key].append(func_name)

            # Check for expensive builtins
            expensive_builtins = {'sorted', 'max', 'min', 'sum', 'len'}
            if func_name in expensive_builtins:
                self.builtin_calls[func_key].append(func_name)

        elif isinstance(node.func, ast.Attribute):
            # Method call
            method_name = node.func.attr
            self.method_calls[func_key].append(method_name)

            # Check for potentially expensive operations
            expensive_methods = {
                'sort', 'index', 'count', 'remove', 'pop', 'insert',
                'append', 'extend', 'keys', 'values', 'items',
                'get', 'setdefault', 'update'
            }

            if method_name in expensive_methods:
                if isinstance(node.func.value, ast.Name):
                    obj_type = "unknown"
                    # Try to infer type from common patterns
                    if hasattr(node.func.value, 'id'):
                        var_name = node.func.value.id
                        if 'list' in var_name or 'items' in var_name:
                            obj_type = "list"
                        elif 'dict' in var_name or 'map' in var_name:
                            obj_type = "dict"

                    self.list_operations[func_key].append(f"{obj_type}.{method_name}")

        self.generic_visit(node)

    def visit_List(self, node):
        """Analyze list literals."""
        func_key = self.get_function_key()
        size = len(node.elts)

        if size > 10:  # Large literal lists
            self.collection_sizes[func_key].append(f"large_list_{size}")

        self.object_creations[func_key].append(f"list_{size}")
        self.generic_visit(node)

    def visit_Dict(self, node):
        """Analyze dict literals."""
        func_key = self.get_function_key()
        size = len(node.keys)

        if size > 10:  # Large literal dicts
            self.collection_sizes[func_key].append(f"large_dict_{size}")

        self.object_creations[func_key].append(f"dict_{size}")
        self.generic_visit(node)

    def visit_If(self, node):
        """Analyze conditional complexity."""
        func_key = self.get_function_key()
        self.conditional_complexity[func_key] += 1

        # Check for complex boolean expressions
        if isinstance(node.test, ast.BoolOp):
            complexity = len(node.test.values)
            if complexity > 3:
                self.conditional_complexity[func_key] += complexity - 1

        self.generic_visit(node)


def analyze_file(filepath: Path) -> PerformanceAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
        analyzer = PerformanceAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def analyze_codebase(src_dir: Path) -> Dict[str, PerformanceAnalyzer]:
    """Analyze all Python files in the codebase."""
    analyzers = {}

    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        analyzer = analyze_file(py_file)
        if analyzer:
            analyzers[str(py_file.relative_to(src_dir))] = analyzer

    return analyzers


def generate_performance_report(analyzers: Dict[str, PerformanceAnalyzer]) -> str:
    """Generate comprehensive performance analysis report."""
    report = []
    report.append("# AST-Based Performance Analysis Report\n")

    # Aggregate metrics
    all_complexity = {}
    all_loops = {}
    all_operations = defaultdict(list)
    hotspot_functions = []

    for filepath, analyzer in analyzers.items():
        report.append(f"## File: {filepath}\n")

        # Function complexity analysis
        if analyzer.function_complexity:
            report.append("### Function Complexity (Cyclomatic)")
            complex_functions = [(f, c) for f, c in analyzer.function_complexity.items() if c > 5]
            if complex_functions:
                complex_functions.sort(key=lambda x: x[1], reverse=True)
                for func, complexity in complex_functions:
                    report.append(f"- **{func}**: {complexity} (HIGH)")
                    hotspot_functions.append((filepath, func, complexity))
                    all_complexity[f"{filepath}:{func}"] = complexity
            else:
                report.append("- All functions have low complexity (≤5)")
            report.append("")

        # Loop nesting analysis
        if analyzer.max_loop_nesting:
            report.append("### Loop Nesting Depth")
            deep_loops = [(f, d) for f, d in analyzer.max_loop_nesting.items() if d > 1]
            if deep_loops:
                deep_loops.sort(key=lambda x: x[1], reverse=True)
                for func, depth in deep_loops:
                    severity = "CRITICAL" if depth > 2 else "HIGH"
                    report.append(f"- **{func}**: depth {depth} ({severity})")
                    all_loops[f"{filepath}:{func}"] = depth
            else:
                report.append("- No deeply nested loops detected")
            report.append("")

        # Algorithmic operation analysis
        expensive_ops = []

        for func, ops in analyzer.list_operations.items():
            if ops:
                op_counts = Counter(ops)
                for op, count in op_counts.items():
                    if count > 5 or "nested" in op:
                        expensive_ops.append((func, op, count))
                        all_operations['list_ops'].append((filepath, func, op, count))

        for func, calls in analyzer.builtin_calls.items():
            if calls:
                call_counts = Counter(calls)
                for call, count in call_counts.items():
                    if count > 10:
                        expensive_ops.append((func, f"builtin.{call}", count))
                        all_operations['builtin_calls'].append((filepath, func, call, count))

        if expensive_ops:
            report.append("### Potentially Expensive Operations")
            for func, op, count in expensive_ops:
                report.append(f"- **{func}**: {op} (×{count})")
            report.append("")

        # Comprehension usage (positive indicator)
        comprehension_usage = []
        for func, comps in analyzer.comprehensions.items():
            if comps:
                comp_counts = Counter(comps)
                total = sum(comp_counts.values())
                comprehension_usage.append((func, total))

        if comprehension_usage:
            report.append("### Comprehension Usage (Optimized)")
            for func, count in comprehension_usage:
                report.append(f"- **{func}**: {count} comprehensions")
            report.append("")

    # Summary section
    report.append("## Performance Summary\n")

    # Top complexity hotspots
    if hotspot_functions:
        hotspot_functions.sort(key=lambda x: x[2], reverse=True)
        report.append("### Top Complexity Hotspots")
        for filepath, func, complexity in hotspot_functions[:10]:
            report.append(f"1. **{filepath}:{func}** - Complexity: {complexity}")
        report.append("")

    # Loop complexity issues
    if all_loops:
        report.append("### Loop Complexity Issues")
        sorted_loops = sorted(all_loops.items(), key=lambda x: x[1], reverse=True)
        for func_path, depth in sorted_loops:
            if depth > 1:
                report.append(f"- **{func_path}** - Nesting depth: {depth}")
        report.append("")

    # Overall algorithmic analysis
    report.append("### Algorithmic Complexity Patterns")

    # Check for O(n²) patterns
    nested_patterns = 0
    for analyzer in analyzers.values():
        for func, ops in analyzer.list_operations.items():
            nested_patterns += sum(1 for op in ops if 'nested_loop' in op)

    if nested_patterns > 0:
        report.append(f"- **Potential O(n²) patterns**: {nested_patterns} detected")

    # Check for dictionary usage (good for performance)
    dict_usage = 0
    for analyzer in analyzers.values():
        for func, calls in analyzer.method_calls.items():
            dict_usage += sum(1 for call in calls if call in ['get', 'setdefault', 'items', 'keys'])

    report.append(f"- **Dictionary operations**: {dict_usage} (efficient lookups)")

    # Check comprehension usage
    total_comprehensions = 0
    for analyzer in analyzers.values():
        for func, comps in analyzer.comprehensions.items():
            total_comprehensions += len(comps)

    report.append(f"- **Comprehensions used**: {total_comprehensions} (memory efficient)")

    report.append("")

    # Performance recommendations
    report.append("### Performance Recommendations")

    if hotspot_functions:
        report.append("1. **Reduce cyclomatic complexity** in high-complexity functions")

    if nested_patterns > 0:
        report.append("2. **Review nested loops** for potential algorithmic improvements")

    report.append("3. **Continue using comprehensions** instead of explicit loops")
    report.append("4. **Leverage dictionary lookups** for O(1) access patterns")

    # Check for specific patterns in this YAML library
    report.append("5. **YAML-specific optimizations**:")
    report.append("   - Cache frequently accessed metadata")
    report.append("   - Use frozenset for constant key lookups (already done)")
    report.append("   - Consider lazy evaluation for large document processing")

    return "\n".join(report)


def main():
    """Main analysis entry point."""
    src_path = Path("src")
    if not src_path.exists():
        print("src/ directory not found. Run from project root.")
        sys.exit(1)

    print("Analyzing codebase with AST...")
    analyzers = analyze_codebase(src_path)

    if not analyzers:
        print("No Python files found to analyze.")
        sys.exit(1)

    print(f"Analyzed {len(analyzers)} files.")

    # Generate report
    report = generate_performance_report(analyzers)

    # Write to TODO.md as requested
    with open("TODO.md", "w") as f:
        f.write(report)

    print("Performance analysis written to TODO.md")

    # Also print summary to console
    lines = report.split('\n')
    summary_start = next(i for i, line in enumerate(lines) if "## Performance Summary" in line)
    summary = '\n'.join(lines[summary_start:summary_start+20])
    print("\nPerformance Summary:")
    print(summary)


if __name__ == "__main__":
    main()