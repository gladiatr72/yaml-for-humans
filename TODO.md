# TODO - YAML for Humans

## High Priority

### Fix version inconsistency
- [x] Synchronize version between `__init__.py` (1.0.3) and `pyproject.toml` (1.0.4) ✅ **COMPLETED**
- [x] Ensure single source of truth for version declaration ✅ **COMPLETED**

### Performance optimization - Priority key lookup
- [ ] Convert `PRIORITY_KEYS` list to set in `emitter.py:158` for O(1) lookups instead of O(n)
- [ ] Update `represent_mapping` method to use set lookup

### CLI constants consolidation
- [ ] Extract CLI magic numbers to constants (per CLAUDE.md requirements)
- [ ] Fix timeout mismatch: help text shows 500ms but DEFAULT_TIMEOUT_MS is 2000ms
- [ ] Create CLI constants namespace as specified in project instructions

## Medium Priority

### Code maintainability
- [ ] Add type hints throughout codebase to improve maintainability
- [ ] Consider using `typing.Protocol` for dumper interfaces

### Refactor duplicate code
- [ ] Extract file detection logic from CLI (`_looks_like_yaml`, `_is_valid_file_type`)
- [ ] Consolidate repeated YAML detection patterns in `cli.py:557-563`
- [ ] Create shared utilities module for file type detection

### I/O Performance
- [ ] Consider adding async I/O support for large file processing
- [ ] Implement streaming for memory-efficient processing of large YAML files

## Low Priority

### Architecture enhancements
- [ ] Add plugin architecture for custom formatters
- [ ] Allow users to define custom priority key lists
- [ ] Consider configuration file support for default behaviors

### Performance optimizations
- [ ] Optimize string operations in CLI for better performance
- [ ] Profile memory usage during large file processing
- [ ] Consider caching compiled regex patterns in CLI

### Documentation
- [ ] Add performance benchmarks to documentation
- [ ] Create migration guide from standard PyYAML
- [ ] Add more real-world examples for different use cases

## Technical Debt

### Code cleanup
- [ ] Review and optimize string concatenation patterns in CLI
- [ ] Consider using `pathlib.Path` consistently instead of `os.path`
- [ ] Evaluate if generator comprehensions can be used in more places

### Testing
- [ ] Add performance regression tests
- [ ] Consider property-based testing for edge cases
- [ ] Add benchmarks to CI pipeline

---

*Generated from repository review on 2025-09-06*