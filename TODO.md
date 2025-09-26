# TODO - YAML for Humans

## Performance Optimization Opportunities

### High Priority - String Processing Bottlenecks

1. ~~**Optimize comment extraction loops** (formatting_aware.py:132-137)~~ ✅ **COMPLETED**
   - ~~Multiple `.strip()` calls per line in comment processing~~
   - ~~Cache stripped strings to avoid repeated operations~~
   - **Result**: Reduced from 4 to 1 strip() call per line (~75% improvement)

2. ~~**Fix JSON Lines detection inefficiency** (cli.py:462)~~ ✅ **COMPLETED**
   - ~~Double `.strip()` in list comprehension: `[line.strip() for line in text.split("\n") if line.strip()]`~~
   - ~~Use single strip with assignment~~
   - **Result**: Reduced from 2 to 1 strip() call per line (50% improvement)

### Medium Priority - I/O and Memory Patterns

3. ~~**Optimize stream processing I/O** (formatting_aware.py:109-112)~~ ✅ **COMPLETED**
   - ~~Current: seek(0) → read() → seek(current_pos) = 3 I/O operations~~
   - ~~Cache content on first read to avoid repeated stream operations~~
   - **Result**: Lazy loading with 75% I/O reduction for StringIO + 67% memory reduction (3x→1x peak usage)

4. **Batch file operations** (cli.py)
   - Multiple separate file reads for format detection + content reading
   - Combine sample read with full content read where possible
   - Estimated impact: Low-Medium (affects file processing)

5. **Pre-allocate comment extraction lists** (formatting_aware.py:374)
   - List comprehension creates new list on every call: `[line for line in ... if line.strip().startswith('#')]`
   - Pre-size based on estimated comment density
   - Estimated impact: Low (micro-optimization)

### Benchmarking and Validation

6. **Measure optimization impact**
   - Use `uv run ./benchmark.py` to establish baseline
   - Re-benchmark after each optimization
   - Document improvements in BENCHMARKS.md

7. **Compare against PyYAML performance**
   - Validate that optimizations don't reduce relative performance
   - Focus on real-world YAML files with comments and complex structures