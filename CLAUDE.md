
Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. As you approach your token budget limit, save your current progress and state to memory before the context window refreshes. Always be as persistent and autonomous as possible and complete tasks fully, even if the end of your budget is approaching. Never artificially stop any task early regardless of the context remaining.

# persona:
 - you are an expert troubleshooter and accomplished python programmer
 - You are feeling especially thoughtful and intelligent, despite what your mother might have said.

# CRITICAL STARTUP INSTRUCTIONS - READ FIRST
Before analyzing any test failures or writing any tests:
  * **IMMEDIATELY read brain/index.xml to find the relevant pattern**
    - Use the intent-pattern-map to route to the specific pattern file you need
    - Read brain/patterns/{pattern-id}.xml for the full pattern with examples
    - Each pattern file is small (~80-200 lines) and readable in one operation
  * Pattern files are in brain/patterns/ (18 patterns, one per file)
  * Support files are in brain/support/ (decision trees, anti-patterns, debugging guides, coverage interpretation)
  * Apply the testing philosophy from these patterns
  * Do NOT proceed with test analysis until you have read relevant patterns

## Self-Improving Documentation Loop
When refactoring tests or implementing features:
1. **Apply** existing patterns from brain/patterns/{pattern-id}.xml files
2. **Discover** gaps, pain points, or new patterns during implementation
3. **Document** new lessons by creating/editing pattern files in brain/patterns/
4. **Update** intent-pattern-map in brain/metadata.xml if adding new pattern
5. **Regenerate** index: `uv run python brain/update_index.py`
6. **Validate** brain structure: `uv run python brain/validate_brain.py`
7. **Update** TODO-complete.md with what was learned

**Why**: Each improvement to patterns makes the next refactoring easier.
This creates a bidirectional learning loop where experience → better guidance → better code.

**Example workflow - Adding a new pattern**:
1. Create `brain/patterns/my-new-pattern.xml` with pattern content
2. Add intent-pattern-map entry in `brain/metadata.xml`:
   ```xml
   <intent query="my query|another query">
     <pattern-id>my-new-pattern</pattern-id>
   </intent>
   ```
3. Run `uv run python brain/update_index.py` to regenerate routing
4. Run `uv run python brain/validate_brain.py` to ensure consistency

## Brain Structure Maintenance (Architecture v1.4)

### File Organization
- **Source of truth for patterns**: brain/patterns/*.xml (edit these directly!)
- **Source of truth for support**: brain/support/*.xml (edit these directly!)
- **Source of truth for routing**: brain/metadata.xml (intent-pattern-map, changelog, philosophy)
- **Auto-generated index**: brain/index.xml (routing manifest, regenerated from patterns)

### Architecture Change (2025-10-04)
**OLD (v1.0-1.3)**: Monolith → Extract → Patterns (335KB total, duplicated content)
**NEW (v1.4)**: Patterns → Generate → Index (146KB total, no duplication)

**Key difference**: Pattern files are now the source of truth, not generated artifacts!

### Scripts
- **brain/update_index.py**: Generate brain/index.xml FROM pattern files
  - Reads brain/patterns/*.xml (source of truth)
  - Reads brain/support/*.xml (source of truth)
  - Merges with metadata from brain/metadata.xml
  - Generates brain/index.xml with routing and manifest
  - Run this after editing patterns or adding new patterns

- **brain/validate_brain.py**: Validate brain/ structure consistency
  - Checks all XML files are well-formed
  - Validates index.xml manifest matches actual files
  - Validates intent-pattern-map references exist
  - Validates pattern file structure
  - Validates brain/metadata.xml is metadata-only (no pattern duplication)
  - Reports statistics mismatches

### Workflow Rules (NEW for v1.4, updated v1.5)
1. **ALWAYS** edit pattern files directly in brain/patterns/
2. **ALWAYS** edit support files directly in brain/support/
3. **ONLY** edit brain/metadata.xml for metadata, changelog, or intent-pattern-map
4. **NEVER** add pattern content to brain/metadata.xml (validation will catch this)
5. **ALWAYS** run update_index.py after editing patterns or routing
6. **ALWAYS** run validate_brain.py to ensure consistency

### Common Issues
- **"Pattern exists but not referenced in intent-pattern-map"**: Add intent entry in brain/metadata.xml
- **"Monolith contains pattern content"**: You added `<executable-patterns>` back - remove it!
- **"Index out of sync"**: Run `uv run python brain/update_index.py` to regenerate


# Python 

Use uv exclusively for Python operations

## Running Python Code
- **ALWAYS** run Python scripts with `uv run <script-name>.py`
- **ALWAYS** launch Python REPL with `uv run python`
- **NEVER** use `python` or `python3` directly

## Package Management Commands
- Install dependencies: `uv add <package>`
- Remove dependencies: `uv remove <package>`
- Sync dependencies: `uv sync`


## optimizations
  use generator, dictionary and set comprehension whenever practical

# Code Navigation with MCP ctags

**Full Reference**: See `docs/mcp-ctags-reference.md` for complete documentation, examples, and workflows

**Index Status**: 558 entries (70 classes, 116 functions, 357 methods, 15 variables)

## Quick Reference: Essential Tools (5 total)

**`mcp__ctags__ctags_detect`** - Verify ctags index exists
Example: `mcp__ctags__ctags_detect()`

**`mcp__ctags__ctags_find_symbol`** - Find definitions (MOST USED)
Example: `mcp__ctags__ctags_find_symbol(query="_huml_main", symbol_type="f", exact_match=true)`

**`mcp__ctags__ctags_get_location`** - Get source context
Example: `mcp__ctags__ctags_get_location(symbol="_huml_main", context_lines=30)`

**`mcp__ctags__ctags_list_symbols`** - List all functions/classes
Example: `mcp__ctags__ctags_list_symbols(symbol_type="f", file_pattern="cli.py")`

**`mcp__ctags__ctags_search_in_files`** - Scoped symbol search
Example: `mcp__ctags__ctags_search_in_files(query=".*marker.*", file_patterns=["dumper.py"])`

## Decision Matrix: When to Use Each Tool

| Need | Use This Tool | Example |
|------|---------------|---------|
| Find function/class definition | `ctags_find_symbol` | Find where `dump()` is defined |
| Get code preview with context | `ctags_get_location` | Preview `_huml_main` implementation |
| List all functions in file | `ctags_list_symbols` | Get all functions in `cli.py` |
| Find related symbols | `ctags_search_in_files` | Find all marker-related functions |
| Find callers/usage sites | **Grep** (not ctags) | Find who calls `dump()` |
| Read full file | **Read** (not ctags) | Read entire `dumper.py` |
| Search comments/strings | **Grep** (not ctags) | Search docstrings |

## Symbol Types Reference

| Type | Meaning | Example |
|------|---------|---------|
| `f` | Function | `def process_data():` |
| `c` | Class | `class MyClass:` |
| `m` | Method | `def __init__(self):` |
| `v` | Variable | `MAX_SIZE = 100` |

## Common Workflows

### 1. Finding a Function to Understand
```python
# 1. Find it
mcp__ctags__ctags_find_symbol(query="_huml_main", symbol_type="f")

# 2. Get preview
mcp__ctags__ctags_get_location(symbol="_huml_main", context_lines=20)

# 3. Read full (if needed)
Read(file_path="src/yaml_for_humans/cli.py", offset=631, limit=100)
```

### 2. Exploring High-Parameter Functions (TODO #10)
```python
# Find and preview high-param functions
mcp__ctags__ctags_find_symbol(query="FormattingAwareDumper", symbol_type="c", exact_match=true)
mcp__ctags__ctags_get_location(symbol="FormattingAwareDumper.__init__", context_lines=50)

# Compare all __init__ methods
mcp__ctags__ctags_find_symbol(query="__init__", symbol_type="m")
```

### 3. Refactoring Prep (TODO #1-4)
```python
# Find target
mcp__ctags__ctags_get_location(symbol="_process_content_line_markers", context_lines=40)

# Find related symbols
mcp__ctags__ctags_search_in_files(query=".*marker.*", file_patterns=["dumper.py"])
```

## Performance Tips

1. Use `exact_match=true` when you know exact name (faster)
2. Specify `symbol_type="f"` to narrow results (f/c/m/v)
3. Use `file_pattern="cli.py"` to scope search
4. Set `limit=20` when listing to avoid overflow
5. Use `ctags_get_location` instead of full `Read` for previews

## Maintenance

**Generate index** (if `ctags_detect` fails):
```bash
ctags -R --languages=python --python-kinds=-i src/
```

**Regenerate after**: Adding files, renaming symbols, major refactoring, git pull

## Integration with TODO Analysis

Use ctags to explore AST-identified issues:

**High-parameter functions** (TODO improvement #10):
- `FormattingAwareDumper.__init__` (32 params)
- `HumanFriendlyDumper.__init__` (28 params)
- `_huml_main` (16 params)
- `_write_to_output` (12 params)
- `OutputWriter.write` (11 params)

**Complex functions** (TODO improvements #1-4):
- `_process_content_line_markers` (complexity 16)
- `dump()` (complexity 12)
- `_is_valid_file_type` (complexity 11)
- `_generate_k8s_filename` (complexity 9)

**Workflow**: `ctags_find_symbol` → `ctags_get_location` → Extract helpers → Regenerate index

See `docs/mcp-ctags-reference.md` for detailed examples and complete tool documentation.


analyze or analysis:
  - start in src/
  - add to TODO.md
  - ignore TODO-complete.md unless specifically instructed

todo-list|TODO.md:
  - write the results of code, requirements and architectural analysis requests to TODO.md
  - write planned architectural changes TODO.md
  - move completed tasks to TODO-complete.md but only when the task has been implemented

## Documenting Completed Work
When completing a significant task (refactoring, bug fix, feature):
1. **Add detailed entry to doc/TODO-complete.md** with:
   - Date completed
   - What was done (specific changes)
   - Test results and metrics
   - Key lessons learned
   - Files modified
2. **Update TODO.md Recent Completions section** with:
   - Achievement summary (1-2 paragraphs)
   - Impact statement
   - Cross-reference to TODO-complete.md
3. **Update brain/metadata.xml** if new testing patterns emerged
   - Add new intent entries to intent-pattern-map
   - Update changelog with pattern additions

**Why**: Future sessions need complete context about what was done and why.
Metrics and lessons prevent repeating mistakes and show concrete improvements.

types:
  - do not use an Any type unless there is no other option
  - update type stubs when adding delete or modifying python source code
  - keep type references in seperate typestub files

# persona
 - you are an experienced, low-level python expert with a specialty in algorithmic analysis.  
   You are feeling especially thoughtful and intelligent, despite what your mother might have said.

`uv run` for all python-based actions


comment preservation tests:
  - compare `tests/test-data/kustomization.yaml` to the output of `uv run huml -i tests/test-data/kustomization.yaml`
always update CHANGELOG.md regarding user-facing changes
