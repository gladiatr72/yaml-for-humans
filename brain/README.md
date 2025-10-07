# Brain - Testing Knowledge Base (Modular)

This directory contains the refactored testing knowledge base from `doc/claude-test-brain.xml`, split into granular files for easy access within LLM context limits.

## Structure

```
brain/
├── index.xml                    # Router with intent-pattern-map
├── patterns/                    # 16 pattern files (one per pattern)
│   ├── async-test-basic.xml
│   ├── async-mock-pattern.xml
│   ├── concurrency-test-pattern.xml
│   ├── async-generator-pattern.xml
│   ├── async-context-manager-pattern.xml
│   ├── integration-test-pattern.xml
│   ├── fixture-pattern.xml
│   ├── async-fixture-pattern.xml
│   ├── factory-fixture-pattern.xml
│   ├── fake-service-pattern.xml
│   ├── validate-before-implement-pattern.xml
│   ├── intentional-failure-test-pattern.xml
│   ├── log-level-management-pattern.xml
│   ├── test-refactoring-pattern.xml
│   ├── pure-function-extraction-pattern.xml
│   └── parameterized-test-pattern.xml
├── support/                     # 6 support files
│   ├── decision-trees.xml       # Mock vs fake decisions
│   ├── anti-patterns.xml        # What NOT to do
│   ├── test-smell-detection.xml # Proactive anti-pattern detection
│   ├── debugging-guide.xml      # Symptom→cause→fix mappings
│   ├── quick-reference.xml      # Fast lookups
│   └── metadata.xml             # Commands, imports, exemplars
└── refactor_brain.py            # Extraction script
```

## Usage

### For LLMs (Claude Code)

1. **Find the pattern you need:**
   - Read `brain/index.xml`
   - Use the `intent-pattern-map` to match your query to a pattern-id

2. **Read the specific pattern:**
   - Read `brain/patterns/{pattern-id}.xml`
   - Each file is ~80-200 lines, readable in one operation
   - Contains complete executable examples

3. **Access support content:**
   - Decision trees: `brain/support/decision-trees.xml`
   - Anti-patterns: `brain/support/anti-patterns.xml`
   - Debugging: `brain/support/debugging-guide.xml`
   - Quick ref: `brain/support/quick-reference.xml`
   - Metadata: `brain/support/metadata.xml`

### Regenerating After Updates

When `doc/claude-test-brain.xml` is updated with new patterns:

```bash
uv run python brain/refactor_brain.py
```

This will re-extract all patterns and support files, preserving the modular structure.

## Statistics

- **Original file:** 102.1 KB (~29K tokens, unreadable in single operation)
- **Extracted files:** 105.9 KB across 23 files
- **Average pattern:** 3.9 KB (~79 lines per pattern)
- **All files:** Valid XML, well-formed

## Benefits

✓ **Granular access** - Read only the pattern you need
✓ **Fast lookup** - Intent-map routes queries to specific files
✓ **Context-friendly** - Each file well under 25K token limit
✓ **Maintainable** - One pattern per file, easy to update
✓ **Automated** - Regenerate anytime with the extraction script
✓ **Complete** - Full examples with critical rules and anti-patterns

## Design Philosophy

This structure implements **Option 3** from the refactoring plan:
- Maximum modularity
- One pattern per file
- Easy navigation via index.xml routing
- Support files separated from pattern files
- Automated extraction maintains consistency
