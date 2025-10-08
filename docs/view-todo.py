#!/usr/bin/env python3
"""Human-readable viewer for TODO.xml"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


def format_section(title: str, level: int = 1) -> str:
    """Format a section header"""
    if level == 1:
        return f"\n{'='*80}\n{title.upper()}\n{'='*80}\n"
    elif level == 2:
        return f"\n{'-'*80}\n{title}\n{'-'*80}\n"
    else:
        return f"\n{title}\n{'-'*len(title)}\n"


def format_improvement(elem: ET.Element, index: int) -> str:
    """Format a single improvement item"""
    imp_id = elem.get('id', '?')
    priority = elem.get('priority', '?')
    pattern = elem.get('pattern', '?')

    title = elem.find('title')
    location = elem.find('location')
    issue = elem.find('issue')
    current_complexity = elem.find('current-complexity')
    target_complexity = elem.find('target-complexity')
    estimated_effort = elem.find('estimated-effort')

    output = []
    output.append(f"\n[{index}] IMPROVEMENT #{imp_id} (Priority: {priority.upper()})")

    if title is not None:
        output.append(f"  Title: {title.text}")

    if location is not None:
        output.append(f"  Location: {location.text}")

    if pattern:
        output.append(f"  Pattern: {pattern}")

    if current_complexity is not None and target_complexity is not None:
        output.append(f"  Complexity: {current_complexity.text} → {target_complexity.text}")

    if issue is not None:
        output.append(f"\n  Issue:\n    {issue.text.strip()}")

    # Refactoring steps
    refactoring = elem.find('proposed-refactoring')
    if refactoring is not None:
        steps = refactoring.findall('step')
        if steps:
            output.append("\n  Refactoring Steps:")
            for step in steps:
                output.append(f"    {step.text}")

    # Benefits
    benefits = elem.find('benefits')
    if benefits is not None:
        output.append("\n  Benefits:")
        for line in benefits.text.strip().split('\n'):
            line = line.strip()
            if line:
                output.append(f"    {line}")

    # Tests to add
    tests = elem.find('tests-to-add')
    if tests is not None:
        output.append("\n  Tests to Add:")
        for line in tests.text.strip().split('\n'):
            line = line.strip()
            if line:
                output.append(f"    {line}")

    if estimated_effort is not None:
        output.append(f"\n  Estimated Effort: {estimated_effort.text}")

    return '\n'.join(output)


def format_opportunity(elem: ET.Element, index: int) -> str:
    """Format a pattern application opportunity"""
    opp_id = elem.get('id', '?')
    pattern = elem.get('pattern', '?')

    title = elem.find('title')
    location = elem.find('location')
    status = elem.find('status')
    observation = elem.find('observation')

    output = []
    output.append(f"\n[{index}] OPPORTUNITY #{opp_id}")

    if title is not None:
        output.append(f"  Title: {title.text}")

    if pattern:
        output.append(f"  Pattern: {pattern}")

    if location is not None:
        output.append(f"  Location: {location.text}")

    if status is not None:
        output.append(f"  Status: {status.text}")

    if observation is not None:
        output.append(f"\n  Observation:\n    {observation.text.strip()}")

    return '\n'.join(output)


def format_phase(elem: ET.Element) -> str:
    """Format a priority sequence phase"""
    name = elem.get('name', '?')
    duration = elem.get('duration', '?')

    output = []
    output.append(f"\nPhase: {name} (Duration: {duration})")

    tasks = elem.findall('task')
    if tasks:
        for task in tasks:
            ref = task.get('ref', '?')
            output.append(f"  • {task.text} (ref: {ref})")

    return '\n'.join(output)


def display_todo(xml_path: Path) -> None:
    """Display TODO.xml in human-readable format"""

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return

    # Meta information
    meta = root.find('meta')
    if meta is not None:
        print(format_section("TODO Metadata", level=1))
        for child in meta:
            print(f"  {child.tag}: {child.text}")

    # Summary
    summary = root.find('summary')
    if summary is not None:
        print(format_section("Summary", level=1))

        overview = summary.find('overview')
        if overview is not None:
            print(f"{overview.text.strip()}\n")

        # Metrics
        metrics = summary.find('metrics')
        if metrics is not None:
            print("\nMetrics:")
            for metric in metrics:
                label = metric.tag.replace('-', ' ').title()
                print(f"  • {label}: {metric.text}")

        # Current state
        current = summary.find('current-state')
        if current is not None:
            strengths = current.find('strengths')
            if strengths is not None:
                print("\n\nStrengths:")
                for line in strengths.text.strip().split('\n'):
                    line = line.strip()
                    if line:
                        print(f"  {line}")

            opportunities = current.find('opportunities')
            if opportunities is not None:
                print("\nOpportunities:")
                for line in opportunities.text.strip().split('\n'):
                    line = line.strip()
                    if line:
                        print(f"  {line}")

    # Testability Improvements
    test_improvements = root.find('testability-improvements')
    if test_improvements is not None:
        print(format_section("Testability Improvements", level=1))
        improvements = test_improvements.findall('improvement')
        for idx, imp in enumerate(improvements, 1):
            print(format_improvement(imp, idx))

    # Architectural Improvements
    arch_improvements = root.find('architectural-improvements')
    if arch_improvements is not None:
        print(format_section("Architectural Improvements", level=1))
        improvements = arch_improvements.findall('improvement')
        for idx, imp in enumerate(improvements, 1):
            print(format_improvement(imp, idx))

    # Pattern Application Opportunities
    pattern_opps = root.find('pattern-application-opportunities')
    if pattern_opps is not None:
        print(format_section("Pattern Application Opportunities", level=1))
        opportunities = pattern_opps.findall('opportunity')
        for idx, opp in enumerate(opportunities, 1):
            print(format_opportunity(opp, idx))

    # Priority Sequence
    priority_seq = root.find('priority-sequence')
    if priority_seq is not None:
        print(format_section("Priority Sequence", level=1))
        phases = priority_seq.findall('phase')
        for phase in phases:
            print(format_phase(phase))

    # Success Criteria
    success = root.find('success-criteria')
    if success is not None:
        print(format_section("Success Criteria", level=1))
        criteria = success.findall('criterion')
        for criterion in criteria:
            print(f"  • {criterion.text}")

    # AST Performance Analysis Summary
    ast_analysis = root.find('ast-performance-analysis')
    if ast_analysis is not None:
        print(format_section("AST Performance Analysis", level=1))

        summary_elem = ast_analysis.find('summary')
        if summary_elem is not None:
            print(f"{summary_elem.text.strip()}\n")

        # File complexity ranking
        file_ranking = ast_analysis.find('file-complexity-ranking')
        if file_ranking is not None:
            print("\nFile Complexity Ranking:")
            files = file_ranking.findall('file')
            for file_elem in files[:5]:  # Top 5
                rank = file_elem.get('rank', '?')
                name = file_elem.find('name')
                complexity = file_elem.find('complexity')
                percentage = file_elem.find('percentage')
                if name is not None and complexity is not None:
                    print(f"  {rank}. {name.text}: {complexity.text} ({percentage.text if percentage is not None else '?'})")

        # High parameter functions
        param_analysis = ast_analysis.find('function-parameter-analysis')
        if param_analysis is not None:
            print("\nHigh Parameter Functions (Top 5):")
            functions = param_analysis.find('high-parameter-functions')
            if functions is not None:
                func_list = functions.findall('function')
                for func in func_list[:5]:
                    rank = func.get('rank', '?')
                    name = func.find('name')
                    params = func.find('parameters')
                    if name is not None and params is not None:
                        print(f"  {rank}. {name.text}: {params.text} parameters")

        # Overall assessment
        overall = ast_analysis.find('overall-assessment')
        if overall is not None:
            grade = overall.find('grade')
            if grade is not None:
                print(f"\nOverall Grade: {grade.text}")

    # Mock Usage Analysis Summary
    mock_analysis = root.find('mock-usage-analysis')
    if mock_analysis is not None:
        print(format_section("Mock Usage Analysis", level=1))

        summary_elem = mock_analysis.find('summary')
        if summary_elem is not None:
            print(f"{summary_elem.text.strip()}\n")

        usage_pct = mock_analysis.find('mock-usage-percentage')
        if usage_pct is not None:
            files_pct = usage_pct.find('files')
            test_pct = usage_pct.find('test-methods')
            if files_pct is not None:
                print(f"\n  Files using mocks: {files_pct.text}")
            if test_pct is not None:
                print(f"  Test methods using mocks: {test_pct.text}")

        comparison = mock_analysis.find('comparison-to-industry')
        if comparison is not None:
            grade = comparison.find('grade')
            if grade is not None:
                print(f"\n  Industry Comparison Grade: {grade.text}")


def main():
    """Main entry point"""
    todo_path = Path(__file__).parent.parent / 'TODO.xml'

    if not todo_path.exists():
        print(f"Error: {todo_path} not found")
        return 1

    display_todo(todo_path)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
