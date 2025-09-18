# AST-Based Performance Analysis Report

## File: yaml_for_humans/dumper.py

### Function Complexity (Cyclomatic)
- **dump**: 8 (HIGH)

### Loop Nesting Depth
- No deeply nested loops detected

## File: yaml_for_humans/emitter.py

### Function Complexity (Cyclomatic)
- **HumanFriendlyEmitter._is_empty_container_fast**: 6 (HIGH)

## File: yaml_for_humans/multi_document.py

### Function Complexity (Cyclomatic)
- All functions have low complexity (≤5)

### Loop Nesting Depth
- No deeply nested loops detected

### Comprehension Usage (Optimized)
- **<module>**: 1 comprehensions

## File: yaml_for_humans/document_processors.py

### Function Complexity (Cyclomatic)
- All functions have low complexity (≤5)

### Loop Nesting Depth
- No deeply nested loops detected

### Comprehension Usage (Optimized)
- **process_multi_document_yaml**: 2 comprehensions
- **process_items_array**: 1 comprehensions

## File: yaml_for_humans/__init__.py

## File: yaml_for_humans/cli.py

### Function Complexity (Cyclomatic)
- **_huml_main**: 13 (HIGH)
- **_read_stdin_with_timeout**: 7 (HIGH)
- **_generate_k8s_filename**: 7 (HIGH)
- **_is_valid_file_type**: 7 (HIGH)
- **FilePathExpander._expand_directory**: 6 (HIGH)
- **InputProcessor._process_single_file**: 6 (HIGH)
- **DirectoryOutputWriter._generate_unique_filename**: 6 (HIGH)

### Loop Nesting Depth
- No deeply nested loops detected

### Comprehension Usage (Optimized)
- **FilePathExpander.expand_paths**: 1 comprehensions
- **_is_json_lines**: 1 comprehensions
- **_generate_k8s_filename**: 1 comprehensions

## File: yaml_for_humans/formatting_emitter.py

### Function Complexity (Cyclomatic)
- All functions have low complexity (≤5)

### Loop Nesting Depth
- No deeply nested loops detected

## File: yaml_for_humans/formatting_aware.py

### Function Complexity (Cyclomatic)
- **FormattingAwareComposer._calculate_end_line**: 9 (HIGH)
- **FormattingAwareComposer._add_mapping_formatting_metadata**: 7 (HIGH)

### Loop Nesting Depth
- **FormattingAwareComposer._calculate_end_line**: depth 2 (HIGH)

### Potentially Expensive Operations
- **FormattingAwareComposer._calculate_end_line**: nested_loop_depth_2 (×1)

### Comprehension Usage (Optimized)
- **FormattingAwareComposer._add_mapping_formatting_metadata**: 1 comprehensions
- **FormattingAwareComposer._add_sequence_formatting_metadata**: 1 comprehensions

## Performance Summary

### Top Complexity Hotspots
1. **yaml_for_humans/cli.py:_huml_main** - Complexity: 13
1. **yaml_for_humans/formatting_aware.py:FormattingAwareComposer._calculate_end_line** - Complexity: 9
1. **yaml_for_humans/dumper.py:dump** - Complexity: 8
1. **yaml_for_humans/cli.py:_read_stdin_with_timeout** - Complexity: 7
1. **yaml_for_humans/cli.py:_generate_k8s_filename** - Complexity: 7
1. **yaml_for_humans/cli.py:_is_valid_file_type** - Complexity: 7
1. **yaml_for_humans/formatting_aware.py:FormattingAwareComposer._add_mapping_formatting_metadata** - Complexity: 7
1. **yaml_for_humans/emitter.py:HumanFriendlyEmitter._is_empty_container_fast** - Complexity: 6
1. **yaml_for_humans/cli.py:FilePathExpander._expand_directory** - Complexity: 6
1. **yaml_for_humans/cli.py:InputProcessor._process_single_file** - Complexity: 6

### Loop Complexity Issues
- **yaml_for_humans/formatting_aware.py:FormattingAwareComposer._calculate_end_line** - Nesting depth: 2

### Algorithmic Complexity Patterns
- **Potential O(n²) patterns**: 1 detected
- **Dictionary operations**: 19 (efficient lookups)
- **Comprehensions used**: 9 (memory efficient)

### Performance Recommendations
1. **Reduce cyclomatic complexity** in high-complexity functions
2. **Review nested loops** for potential algorithmic improvements
3. **Continue using comprehensions** instead of explicit loops
4. **Leverage dictionary lookups** for O(1) access patterns
5. **YAML-specific optimizations**:
   - Cache frequently accessed metadata
   - Use frozenset for constant key lookups (already done)
   - Consider lazy evaluation for large document processing