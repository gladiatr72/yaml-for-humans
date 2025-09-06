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

### Refactor duplicate code
- [ ] **Phase 2: File Detection Utilities** (Medium Impact)
  - Create `file_utils.py` module with format detection constants:
    - `YAML_EXTENSIONS = ('.yaml', '.yml')`
    - `JSON_EXTENSIONS = ('.json', '.jsonl')`
    - `SUPPORTED_EXTENSIONS = YAML_EXTENSIONS + JSON_EXTENSIONS`
  - Add `detect_file_format()` function to replace hardcoded extension checking
  - Add `_read_file_safely()` utility to consolidate file I/O patterns
  - Eliminates inconsistent extension checking across 4+ locations
- [ ] **Phase 3: Unified Document Processing** (Long-term Architecture)
  - Refactor to single `process_documents()` function handling all formats/sources
  - Consider Strategy Pattern or Document Processor Class for format dispatch
  - Single point of maintenance for all document processing logic

### I/O Performance
- [ ] Consider adding async I/O support for large file processing
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
