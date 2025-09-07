# TODO - YAML for Humans

## Performance Optimization Hot Spots



### 3. Optimize metadata calculation in formatting_aware.py:40-94 (line number calculations)
- **Status**: In Progress - Analysis Complete
- **Issues Identified**:
  - Recursive `_get_node_end_line` calls for every mapping item's value node (lines 59, 74, 116-140)
  - Redundant line calculations and duplicate `_get_node_end_line` calls (lines 52, 80)
  - Inefficient array access with bounds checking and tuple unpacking (lines 70-71)
  - Metadata object creation overhead and frequent `hasattr()` checks (lines 54-56, 84, 91-93)
  - Double processing: each mapping item processed in main loop AND structural check
- **Expected Gain**: 40-60% reduction in line calculation overhead, 25-35% fewer object allocations
- **Optimization Strategy**:
  - Implement memoized end line calculation with cache
  - Replace recursive traversal with iterative stack-based approach
  - Use bulk line processing in single pass
  - Add metadata object pooling to reduce allocation overhead

### 4. Optimize resource sorting in multi_document.py:190-209 (precompute priorities)
- **Status**: In Progress - Analysis Complete
- **Issues Identified**:
  - Linear search with `list.index()` performs O(n) search through 20-item list for every document (line 205)
  - Exception handling in hot path with try/except for every document (lines 204-207)
  - Redundant `len()` calculation for every unknown kind (line 207)
  - Dictionary access overhead with default value string allocation (line 203)
- **Expected Gain**: 20x faster sorting (O(n*m) → O(n log n)), elimination of exception handling overhead
- **Optimization Strategy**:
  - Replace RESOURCE_ORDER list with precomputed RESOURCE_PRIORITIES dictionary
  - Use dictionary comprehension: `{kind: i for i, kind in enumerate(RESOURCE_ORDER)}`
  - Eliminate exception handling with direct dict.get() with default
  - Cache unknown priority constant instead of len() calls

