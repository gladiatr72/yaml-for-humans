# TODO - YAML for Humans

## High Priority

### CLI constants consolidation
- [ ] Extract CLI magic numbers to constants (per CLAUDE.md requirements)
- [ ] Fix timeout mismatch: help text shows 500ms but DEFAULT_TIMEOUT_MS is 2000ms
- [ ] Create CLI constants namespace as specified in project instructions

## Medium Priority

### Code maintainability
- [ ] Add type hints throughout codebase to improve maintainability
- [ ] Consider using `typing.Protocol` for dumper interfaces


### I/O Performance
- [ ] Implement streaming for memory-efficient processing of large YAML files

## Low Priority

### Architecture enhancements
- [ ] Add plugin architecture for custom formatters
- [ ] Allow users to define custom priority key lists
- [ ] Consider configuration file support for default behaviors

### Performance optimizations - Comprehensive Analysis
- [ ] **CLI File Processing Batching** (Medium Impact)
  - Implement batch processing in `cli.py:190-324`
  - Cache format detection results to avoid repeated analysis
  - Use concurrent processing for independent file operations
- [ ] **Format Detection Optimization** (Low-Medium Impact)
  - Implement trie-based pattern matching for `_looks_like_json/_looks_like_yaml`
  - Use state machine for content type detection in `cli.py:436-563`
  - Cache detection results for repeated content patterns

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
