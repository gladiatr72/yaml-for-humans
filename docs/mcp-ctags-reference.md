# MCP ctags Reference Guide

Complete reference for using MCP (Model Context Protocol) ctags server for code navigation in yaml-for-humans project.

**Index Status**: 558 entries (70 classes, 116 functions, 357 methods, 15 variables)

---

## Table of Contents
1. [Available Tools](#available-tools)
2. [Workflow Examples](#workflow-examples)
3. [Best Practices](#best-practices)
4. [Performance Tips](#performance-tips)
5. [Maintaining ctags Index](#maintaining-ctags-index)

---

## Available Tools

### 1. `mcp__ctags__ctags_detect`
**Purpose**: Detect and validate ctags file in working directory

**Parameters**:
- `working_dir` (optional): Directory to search in (defaults to current directory)

**Example**:
```python
mcp__ctags__ctags_detect()
# Returns: {"found": true, "file_path": "/path/to/tags", "total_entries": 558, ...}
```

**When to use**:
- Before using other ctags tools
- To verify ctags index is up to date
- After running ctags generation commands

**Returns**:
- `found`: boolean
- `file_path`: path to tags file
- `format`: ctags format (exuberant, universal, etc.)
- `total_entries`: total number of symbols
- `symbol_types`: breakdown by type (f, c, m, v)
- `valid`: whether tags file is valid

---

### 2. `mcp__ctags__ctags_find_symbol`
**Purpose**: Find symbols by name or pattern (MOST COMMONLY USED)

**Parameters**:
- `query` (required): Symbol name or regex pattern to search for
- `symbol_type` (optional): Type of symbol - "f" (function), "c" (class), "m" (method), "v" (variable), or "all" (default)
- `file_pattern` (optional): Regex pattern to filter files
- `exact_match` (optional): Whether to match exact symbol name (default: false)
- `case_sensitive` (optional): Whether search is case sensitive (default: false)
- `working_dir` (optional): Directory containing tags file

**Examples**:
```python
# Find function by name (case-insensitive partial match)
mcp__ctags__ctags_find_symbol(query="process_content")

# Find exact class name
mcp__ctags__ctags_find_symbol(query="FormattingAwareDumper", symbol_type="c", exact_match=true)

# Find all functions in cli.py
mcp__ctags__ctags_find_symbol(query=".*", symbol_type="f", file_pattern="cli.py")

# Find methods containing "init"
mcp__ctags__ctags_find_symbol(query="init", symbol_type="m")

# Find all helper functions (start with underscore)
mcp__ctags__ctags_find_symbol(query="_.*", symbol_type="f")

# Find specific private method
mcp__ctags__ctags_find_symbol(query="_process_content_line_markers", symbol_type="f", exact_match=true)
```

**When to use**:
- Finding function/class definitions quickly
- Locating where symbols are defined
- Searching for similar function names
- Exploring unfamiliar codebases

**Advantages over grep**:
- Understands code structure (not just text matching)
- Distinguishes between functions, classes, methods, variables
- More precise results (no false positives from comments/strings)
- Respects symbol boundaries (won't match partial strings)

**Returns** (list of matches):
- `symbol`: symbol name
- `type`: symbol type (f, c, m, v)
- `file`: file path
- `pattern`: search pattern
- `line_number`: line number (if available)
- `scope`: scope information (if available)

---

### 3. `mcp__ctags__ctags_list_symbols`
**Purpose**: List all symbols of a specific type

**Parameters**:
- `symbol_type` (required): "f" (function), "c" (class), "m" (method), or "v" (variable)
- `file_pattern` (optional): Regex pattern to filter files
- `limit` (optional): Maximum results to return (default: 100)
- `working_dir` (optional): Directory containing tags file

**Examples**:
```python
# List all classes in the project
mcp__ctags__ctags_list_symbols(symbol_type="c")

# List all functions in dumper.py
mcp__ctags__ctags_list_symbols(symbol_type="f", file_pattern="dumper.py")

# List first 50 methods
mcp__ctags__ctags_list_symbols(symbol_type="m", limit=50)

# List all functions in cli module
mcp__ctags__ctags_list_symbols(symbol_type="f", file_pattern="cli.py")

# Get comprehensive class inventory
mcp__ctags__ctags_list_symbols(symbol_type="c", limit=200)
```

**When to use**:
- Getting overview of all functions/classes in codebase
- Analyzing code structure
- Finding all methods in a module
- Code inventory/auditing
- Understanding module architecture

**Returns** (list of symbols):
Same format as `ctags_find_symbol`

---

### 4. `mcp__ctags__ctags_get_location`
**Purpose**: Get file location and source context for a symbol

**Parameters**:
- `symbol` (required): Exact symbol name to locate
- `context_lines` (optional): Number of context lines around symbol (default: 10)
- `working_dir` (optional): Directory containing tags file

**Examples**:
```python
# Get location and 10 lines of context
mcp__ctags__ctags_get_location(symbol="_process_content_line_markers")

# Get more context (30 lines)
mcp__ctags__ctags_get_location(symbol="dump", context_lines=30)

# Get minimal context (5 lines)
mcp__ctags__ctags_get_location(symbol="_huml_main", context_lines=5)

# Preview function implementation
mcp__ctags__ctags_get_location(symbol="_extract_k8s_parts", context_lines=20)

# Check method signature
mcp__ctags__ctags_get_location(symbol="FormattingAwareDumper.__init__", context_lines=15)
```

**When to use**:
- Getting quick preview of function implementation
- Understanding function context without opening file
- Verifying which definition you found (when multiple exist)
- Rapid code review
- Checking function signatures

**Returns**:
- `found`: boolean
- `symbol`: symbol name
- `type`: symbol type
- `file`: file path
- `line_number`: exact line number
- `context`: source code with surrounding lines
- `target_line`: the line containing the symbol definition

**Note**: Context lines show code before and after the symbol definition, making it easy to understand the function's purpose without reading the full file.

---

### 5. `mcp__ctags__ctags_search_in_files`
**Purpose**: Search for symbols within specific files or patterns

**Parameters**:
- `query` (required): Symbol name or pattern
- `file_patterns` (required): List of file path patterns
- `symbol_types` (optional): List of symbol types to include
- `case_sensitive` (optional): Case sensitive search (default: false)
- `working_dir` (optional): Directory containing tags file

**Examples**:
```python
# Search for "init" in specific files
mcp__ctags__ctags_search_in_files(
    query="init",
    file_patterns=["cli.py", "dumper.py"]
)

# Search for functions only in test files
mcp__ctags__ctags_search_in_files(
    query="test_.*",
    file_patterns=["tests/*.py"],
    symbol_types=["f"]
)

# Find all marker-related symbols in dumper.py
mcp__ctags__ctags_search_in_files(
    query=".*marker.*",
    file_patterns=["dumper.py"],
    symbol_types=["f", "m"]
)

# Search for config-related classes in multiple files
mcp__ctags__ctags_search_in_files(
    query=".*Config.*",
    file_patterns=["cli.py", "dumper.py", "formatting_aware.py"],
    symbol_types=["c"]
)
```

**When to use**:
- Scoped symbol search in specific modules
- Finding related symbols across multiple files
- Targeted code exploration
- Refactoring specific subsystems
- Analyzing feature implementation across files

**Returns**:
Dictionary mapping file patterns to matching symbols

---

## Workflow Examples

### Example 1: Finding a Function to Understand
```python
# 1. Find the function
mcp__ctags__ctags_find_symbol(query="_huml_main", symbol_type="f")
# Returns: cli.py:631

# 2. Get implementation with context
mcp__ctags__ctags_get_location(symbol="_huml_main", context_lines=20)
# Shows function signature and first 20 lines

# 3. Read full implementation if needed
Read(file_path="src/yaml_for_humans/cli.py", offset=631, limit=100)
```

**Use case**: Understanding the main CLI entry point before refactoring

---

### Example 2: Exploring High-Parameter Functions (from AST analysis)

The AST performance analysis identified functions with excessive parameters (7-32 params). Use ctags to explore them:

```python
# Find FormattingAwareDumper class (32 parameters in __init__)
mcp__ctags__ctags_find_symbol(query="FormattingAwareDumper", symbol_type="c", exact_match=true)

# Get its __init__ method with context
mcp__ctags__ctags_get_location(symbol="FormattingAwareDumper.__init__", context_lines=50)

# Find all __init__ methods in project to compare parameter counts
mcp__ctags__ctags_find_symbol(query="__init__", symbol_type="m")

# Explore other high-parameter functions
mcp__ctags__ctags_find_symbol(query="_huml_main", symbol_type="f")
mcp__ctags__ctags_get_location(symbol="_huml_main", context_lines=30)

mcp__ctags__ctags_find_symbol(query="_write_to_output", symbol_type="f")
mcp__ctags__ctags_get_location(symbol="_write_to_output", context_lines=25)
```

**Use case**: Investigating TODO improvement #10 (extract configuration dataclasses)

---

### Example 3: Analyzing Helper Functions

```python
# List all helper functions (starting with underscore) in cli.py
mcp__ctags__ctags_find_symbol(query="_.*", symbol_type="f", file_pattern="cli.py")

# Get implementation of specific helper
mcp__ctags__ctags_get_location(symbol="_extract_k8s_parts", context_lines=15)

# Find all helpers in dumper.py
mcp__ctags__ctags_find_symbol(query="_.*", symbol_type="f", file_pattern="dumper.py")

# Compare helper naming patterns across files
mcp__ctags__ctags_search_in_files(
    query="_.*",
    file_patterns=["cli.py", "dumper.py", "emitter.py"],
    symbol_types=["f"]
)
```

**Use case**: Understanding helper function organization before extracting pure functions (TODO improvements #1-#4)

---

### Example 4: Refactoring Support

Before refactoring `_process_content_line_markers` (TODO improvement #1):

```python
# Find the target function
mcp__ctags__ctags_find_symbol(query="_process_content_line_markers", symbol_type="f", exact_match=true)

# Get full implementation with context
mcp__ctags__ctags_get_location(symbol="_process_content_line_markers", context_lines=40)

# Find all related marker functions
mcp__ctags__ctags_search_in_files(
    query=".*marker.*",
    file_patterns=["dumper.py"],
    symbol_types=["f", "m"]
)

# List all functions in dumper.py to understand context
mcp__ctags__ctags_list_symbols(symbol_type="f", file_pattern="dumper.py")
```

**Use case**: Gathering context before extracting pure helpers from complex function

---

### Example 5: Understanding Class Hierarchy

```python
# List all classes
mcp__ctags__ctags_list_symbols(symbol_type="c")

# Find specific class
mcp__ctags__ctags_find_symbol(query="FormattingAwareComposer", symbol_type="c", exact_match=true)

# Get class definition with context
mcp__ctags__ctags_get_location(symbol="FormattingAwareComposer", context_lines=25)

# Find all methods in the class
mcp__ctags__ctags_find_symbol(query="FormattingAwareComposer\\..*", symbol_type="m")
```

**Use case**: Understanding class structure before modifications

---

### Example 6: Test Exploration

```python
# Find all test functions
mcp__ctags__ctags_find_symbol(query="test_.*", symbol_type="f", file_pattern="tests/")

# Find specific test class
mcp__ctags__ctags_find_symbol(query="TestCLIFunctionality", symbol_type="c", exact_match=true)

# Get test implementation
mcp__ctags__ctags_get_location(symbol="test_stdin_timeout_function_exists", context_lines=15)

# Find all tests in specific file
mcp__ctags__ctags_list_symbols(symbol_type="f", file_pattern="test_cli.py")
```

**Use case**: Understanding test coverage and finding test patterns

---

## Best Practices

### When to Use ctags vs. Other Tools

**Use ctags (`mcp__ctags__*`) when**:
- ✅ Finding function/class definitions by name
- ✅ Getting symbol locations with context
- ✅ Exploring code structure (all functions in a file)
- ✅ Understanding unfamiliar codebase quickly
- ✅ Symbol-aware search (functions vs variables vs classes)
- ✅ Checking function signatures
- ✅ Getting quick code previews

**Use Grep when**:
- ✅ Searching for string patterns in comments/docstrings
- ✅ Finding usage sites (callers of a function)
- ✅ Searching across all file types (not just code)
- ✅ Pattern matching in non-code content
- ✅ Finding string literals
- ✅ Searching in configuration files

**Use Read when**:
- ✅ You already know the file and line number
- ✅ Reading large sections of a specific file
- ✅ Examining configuration files or data files
- ✅ Reading entire modules sequentially
- ✅ Reading non-Python files

**Use Glob when**:
- ✅ Finding files by name pattern
- ✅ Getting list of all files in directory
- ✅ File-level operations
- ✅ Directory traversal

### Symbol Type Reference

| Type | Symbol | Example |
|------|--------|---------|
| `f` | Function | `def process_data():` |
| `c` | Class | `class MyClass:` |
| `m` | Method | `def __init__(self):` |
| `v` | Variable | `MAX_SIZE = 100` |

---

## Performance Tips

### 1. Use `exact_match=true` for Known Symbols
```python
# Faster - exact match
mcp__ctags__ctags_find_symbol(query="_huml_main", exact_match=true)

# Slower - regex matching
mcp__ctags__ctags_find_symbol(query="_huml_main")
```

### 2. Specify `symbol_type` to Narrow Results
```python
# Faster - only searches functions
mcp__ctags__ctags_find_symbol(query="process", symbol_type="f")

# Slower - searches all symbol types
mcp__ctags__ctags_find_symbol(query="process")
```

### 3. Use `file_pattern` to Scope Search
```python
# Faster - scoped to one file
mcp__ctags__ctags_find_symbol(query="dump", file_pattern="dumper.py")

# Slower - searches all files
mcp__ctags__ctags_find_symbol(query="dump")
```

### 4. Set `limit` When Listing Symbols
```python
# Returns first 20 (fast)
mcp__ctags__ctags_list_symbols(symbol_type="m", limit=20)

# Returns all methods (potentially slow)
mcp__ctags__ctags_list_symbols(symbol_type="m", limit=1000)
```

### 5. Use `ctags_get_location` Instead of Full File Reads
```python
# Faster - only reads relevant section
mcp__ctags__ctags_get_location(symbol="dump", context_lines=15)

# Slower - reads entire file
Read(file_path="src/yaml_for_humans/dumper.py")
```

### 6. Combine Tools Efficiently
```python
# Efficient workflow:
# 1. Find with ctags (precise)
result = mcp__ctags__ctags_find_symbol(query="_process_content_line_markers", exact_match=true)

# 2. Get context with ctags (quick preview)
mcp__ctags__ctags_get_location(symbol="_process_content_line_markers", context_lines=20)

# 3. Only use Read if you need full implementation
# Read(file_path=result['file'], offset=result['line'], limit=100)
```

---

## Maintaining ctags Index

### Generating the Index

**Initial generation**:
```bash
# For Python projects
ctags -R --languages=python --python-kinds=-i src/

# Include tests
ctags -R --languages=python --python-kinds=-i src/ tests/
```

**Command breakdown**:
- `-R`: Recursive
- `--languages=python`: Python only
- `--python-kinds=-i`: Exclude imports (cleaner index)
- `src/`: Source directory

### When to Regenerate

**Regenerate ctags after**:
- ✅ Adding new files
- ✅ Renaming functions/classes
- ✅ Major refactoring
- ✅ Pulling updates from git
- ✅ Adding new methods to classes
- ✅ Deleting files

### Verifying Index Status

```python
# Check if index exists and is valid
mcp__ctags__ctags_detect()

# Expected output:
{
  "found": true,
  "file_path": "/path/to/tags",
  "format": "exuberant",
  "total_entries": 558,
  "symbol_types": {
    "c": 70,    # 70 classes
    "f": 116,   # 116 functions
    "m": 357,   # 357 methods
    "v": 15     # 15 variables
  },
  "valid": true
}
```

### Troubleshooting

**If `ctags_detect` fails**:
1. Check if `tags` file exists: `ls -la tags`
2. Regenerate: `ctags -R --languages=python --python-kinds=-i src/`
3. Verify: `mcp__ctags__ctags_detect()`

**If results seem outdated**:
1. Check file modification time: `stat tags`
2. Regenerate index
3. Test with known symbols

**If getting no results**:
1. Verify symbol exists: `grep "symbol_name" tags`
2. Check file is indexed: `grep "filename" tags`
3. Try partial match: `exact_match=false`

---

## Integration with TODO Analysis

The AST performance analysis (TODO.xml) identified several optimization opportunities. Use ctags to explore them:

### High-Parameter Functions (TODO Improvement #10)

```python
# FormattingAwareDumper.__init__ (32 parameters)
mcp__ctags__ctags_find_symbol(query="FormattingAwareDumper", symbol_type="c", exact_match=true)
mcp__ctags__ctags_get_location(symbol="FormattingAwareDumper.__init__", context_lines=50)

# HumanFriendlyDumper.__init__ (28 parameters)
mcp__ctags__ctags_find_symbol(query="HumanFriendlyDumper", symbol_type="c", exact_match=true)
mcp__ctags__ctags_get_location(symbol="HumanFriendlyDumper.__init__", context_lines=40)

# _huml_main (16 parameters)
mcp__ctags__ctags_find_symbol(query="_huml_main", symbol_type="f", exact_match=true)
mcp__ctags__ctags_get_location(symbol="_huml_main", context_lines=30)

# _write_to_output (12 parameters)
mcp__ctags__ctags_find_symbol(query="_write_to_output", symbol_type="f", exact_match=true)
mcp__ctags__ctags_get_location(symbol="_write_to_output", context_lines=25)

# OutputWriter.write (11 parameters)
mcp__ctags__ctags_find_symbol(query="OutputWriter", symbol_type="c", exact_match=true)
mcp__ctags__ctags_get_location(symbol="OutputWriter.write", context_lines=20)
```

### Complex Functions (TODO Improvements #1-#4)

```python
# Improvement #1: _process_content_line_markers (complexity 16)
mcp__ctags__ctags_get_location(symbol="_process_content_line_markers", context_lines=40)

# Improvement #2: dump() function (complexity 12)
mcp__ctags__ctags_find_symbol(query="^dump$", symbol_type="f", exact_match=true)
mcp__ctags__ctags_get_location(symbol="dump", context_lines=30)

# Improvement #3: _is_valid_file_type (complexity 11)
mcp__ctags__ctags_get_location(symbol="_is_valid_file_type", context_lines=25)

# Improvement #4: _generate_k8s_filename (complexity 9)
mcp__ctags__ctags_get_location(symbol="_generate_k8s_filename", context_lines=30)
```

### Workflow for Refactoring

1. **Find target function**: Use `ctags_find_symbol` with exact match
2. **Get context**: Use `ctags_get_location` with 30-40 context lines
3. **Find related symbols**: Use `ctags_search_in_files` for related functions
4. **Understand dependencies**: Use `Grep` to find callers
5. **Extract helpers**: Create new functions (regenerate ctags after)
6. **Verify changes**: Use `ctags_find_symbol` to find new helpers

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Find function | `mcp__ctags__ctags_find_symbol(query="name", symbol_type="f")` |
| Find class | `mcp__ctags__ctags_find_symbol(query="Name", symbol_type="c")` |
| Get preview | `mcp__ctags__ctags_get_location(symbol="name", context_lines=20)` |
| List all functions | `mcp__ctags__ctags_list_symbols(symbol_type="f")` |
| List all classes | `mcp__ctags__ctags_list_symbols(symbol_type="c")` |
| Search in file | `mcp__ctags__ctags_find_symbol(query=".*", file_pattern="file.py")` |
| Verify index | `mcp__ctags__ctags_detect()` |
| Generate index | `ctags -R --languages=python --python-kinds=-i src/` |

---

## Summary

**ctags is best for**: Finding definitions, exploring structure, getting quick previews
**ctags is NOT for**: Finding usage/callers (use Grep), reading full files (use Read)

**Workflow**: `find_symbol` → `get_location` → `Read` (if needed)

**Performance**: Use `exact_match`, `symbol_type`, `file_pattern` to optimize searches

**Maintenance**: Regenerate after adding/renaming symbols

**Integration**: Essential for TODO improvements #1-4 and #10 (refactoring work)
