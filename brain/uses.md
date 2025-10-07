# Brain System Usage Guide

**Last Updated**: 2025-10-04
**Architecture Version**: 1.4 (Patterns-first)

This document explains how the brain/ system is used in practice by Claude Code to provide accurate, context-aware testing guidance.

---

## Table of Contents

1. [Overview](#overview)
2. [How Claude Uses brain/](#how-claude-uses-brain)
3. [Complete Usage Example](#complete-usage-example)
4. [Workflow Patterns](#workflow-patterns)
5. [Benefits Demonstrated](#benefits-demonstrated)
6. [Common Usage Scenarios](#common-usage-scenarios)

---

## Overview

The brain/ system is a **just-in-time knowledge retrieval** system that enables Claude Code to:

- **Parse user intent** from natural language questions
- **Route to relevant patterns** using the intent-pattern-map
- **Load specific pattern files** on demand (not all patterns at once)
- **Apply proven solutions** from real refactoring sessions
- **Provide complete examples** with context and anti-patterns

### Architecture (v1.4)

```
User Question
     ↓
Intent Recognition (parse keywords)
     ↓
brain/index.xml (routing table)
     ↓
brain/patterns/{pattern-id}.xml (specific pattern)
     ↓
Apply Pattern (with examples)
     ↓
Concrete Implementation
```

### Efficiency

| Approach | Context Loaded | Accuracy |
|----------|---------------|----------|
| **Without brain/** | Guess or load 103KB monolith | Variable |
| **With brain/** | Load 1-3 pattern files (~5-10KB) | High (proven patterns) |

---

## How Claude Uses brain/

### Step-by-Step Process

#### 1. **Intent Recognition**

When a user asks a question, Claude identifies key intent keywords:

**Example queries and keywords**:
- "How do I test an async function?" → `test async`
- "Should I use a mock or fake?" → `mock vs fake`
- "Test my Click CLI command" → `test CLI`
- "Validation function returns tuple" → `validation dataclass`

#### 2. **Index Lookup**

Read `brain/index.xml` to find the `<intent-pattern-map>` routing:

```xml
<intent query="test CLI|test click command|test typer|CLI testing|command line test">
  <pattern-id>cli-testing-pattern</pattern-id>
  <must-have>Extract business logic from CLI framework</must-have>
  <philosophy>Test business logic, not framework integration</philosophy>
</intent>
```

**Query matching**: The pipe-separated queries use OR logic - any match triggers the pattern.

#### 3. **Pattern Retrieval**

Read the specific pattern file from `brain/patterns/{pattern-id}.xml`:

```bash
# Claude reads only this file (not all 18 patterns)
brain/patterns/cli-testing-pattern.xml
```

Pattern files contain:
- **When to use** this pattern
- **Why** it's the right approach
- **Complete working examples** (before/after refactoring)
- **Anti-patterns** (what NOT to do)
- **Test examples** (copy-paste ready)

#### 4. **Related Pattern Loading**

If the pattern references other patterns, load those too:

```
cli-testing-pattern.xml
  ↓ references
validation-dataclass-pattern.xml
```

**Typical load**: 1-3 pattern files per user question

#### 5. **Apply and Respond**

Generate response with:
- Explanation of the pattern
- Before/after code examples
- Working test code
- Rationale for approach

---

## Complete Usage Example

Let's walk through a realistic scenario from user question → pattern application.

### **Scenario: User Asks About Testing a CLI Command**

#### **User Request**
> "I need to test the `purge` CLI command. It takes a repository name and a --dry-run flag. How should I test this?"

---

### **Step 1: Intent Recognition**

Claude parses the request and identifies keywords:
- ✅ **"test"** + **"CLI command"** → Matches pattern routing
- ✅ **"repository name"** + **"flag"** → CLI parameters
- ✅ Need testing strategy for Click/Typer command

---

### **Step 2: Query brain/index.xml**

Claude reads the index to find the routing:

```xml
<!-- From brain/index.xml -->
<intent query="test CLI|test click command|test typer|CLI testing|command line test">
  <pattern-id>cli-testing-pattern</pattern-id>
  <must-have>Extract business logic from CLI framework</must-have>
  <must-have>Pure validation functions returning dataclasses</must-have>
  <philosophy>Test business logic, not framework integration</philosophy>
</intent>
```

**Match found**: `pattern-id: cli-testing-pattern`

---

### **Step 3: Read the Specific Pattern**

Claude reads `brain/patterns/cli-testing-pattern.xml`:

**Key information extracted**:

```python
# BEFORE: Monolithic Click command (untestable without CliRunner)
@click.command()
def purge(ctx, repository_name, all, dry_run):
    # Validation mixed with business logic
    if not repository_name and not all:
        progress_reporter.error("Must specify either a repository name or -A/--all")
        sys.exit(1)

    # Business logic buried in CLI command
    try:
        purge_service = ECRPurgeService(...)
        result = purge_service.purge(...)
    except Exception as e:
        progress_reporter.error(str(e))
        sys.exit(1)

# PROBLEM: Cannot test validation or business logic without CliRunner
```

```python
# AFTER: Extracted helpers with thin Click shell

@dataclass
class PurgeOptions:
    """Validated purge operation parameters."""
    repository_name: Optional[str]
    all_repositories: bool
    dry_run: bool

def _validate_purge_options(...) -> PurgeOptions:
    """Validate purge options and return structured config.

    PURE FUNCTION: No I/O, easily testable.
    """
    if not repository_name and not all_repositories:
        raise ValueError("Must specify either a repository name or -A/--all")

    return PurgeOptions(...)

@click.command()
def purge(repository_name, all, dry_run):
    """Purge images from ECR repositories.

    THIN SHELL: Only orchestration, no business logic.
    """
    try:
        options = _validate_purge_options(...)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    _execute_purge(options)
```

**Test examples**:

```python
class TestValidatePurgeOptions:
    """Pure function tests - no Click, no CliRunner."""

    def test_valid_single_repository(self):
        options = _validate_purge_options(
            repository_name='my-repo',
            all_repositories=False,
            dry_run=True,
        )

        assert options.repository_name == 'my-repo'
        assert options.dry_run is True

    def test_error_neither_repo_nor_all(self):
        with pytest.raises(ValueError, match="Must specify either"):
            _validate_purge_options(
                repository_name=None,
                all_repositories=False,
            )
```

---

### **Step 4: Identify Related Patterns**

The cli-testing-pattern references **validation-dataclass-pattern** in its must-have requirements.

Claude reads `brain/patterns/validation-dataclass-pattern.xml` for additional context:

**Key insight from related pattern**:

```python
# ANTI-PATTERN: Returns tuple (error-prone)
def validate_options(...):
    return (repo_name, all_repos, region, keep, dry)

# Usage - unclear, easy to get wrong
r, a, reg, keep, dry = validate_options(...)  # Which is which?

# BEST PRACTICE: Returns dataclass
@dataclass
class PurgeOptions:
    repository_name: Optional[str]
    all_repositories: bool
    region: Optional[str]
    dry_run: bool

def validate_options(...) -> PurgeOptions:
    return PurgeOptions(...)

# Usage - type-safe, IDE autocomplete
opts = validate_options(...)
service.purge(opts.repository_name)  # Clear!
```

---

### **Step 5: Apply Patterns and Respond**

Claude generates a comprehensive response:

**Response structure**:

1. **Recommendation**: "Don't test the Click framework - test the business logic!"
2. **Refactoring guidance**: Extract validation to pure function
3. **Code examples**: Before/after refactoring with dataclass
4. **Test implementation**: Complete test class with multiple test cases
5. **Rationale**: Why this approach (no CliRunner, fast, maintainable)
6. **Coverage breakdown**: What to test and how

**Result**: User gets a complete, proven solution with working code examples in seconds.

---

## Workflow Patterns

### **Pattern 1: Single Intent Match**

```
User: "How do I test an async function?"
  ↓
Intent: "test async function"
  ↓
Index: async-test-basic
  ↓
Load: brain/patterns/async-test-basic.xml
  ↓
Response: Complete example with @pytest.mark.asyncio
```

**Files loaded**: 1 pattern file (~5KB)

---

### **Pattern 2: Decision Tree Routing**

```
User: "Should I mock this service or use a fake?"
  ↓
Intent: "mock vs fake"
  ↓
Index: decision-tree-id="mock-vs-fake-decision"
  ↓
Load: brain/support/decision-trees.xml
  ↓
Response: Decision tree with conditions and actions
```

**Files loaded**: 1 support file (~7KB)

---

### **Pattern 3: Multi-Pattern Composition**

```
User: "Test CLI command with validation"
  ↓
Intent: "test CLI"
  ↓
Index: cli-testing-pattern
  ↓
Load: brain/patterns/cli-testing-pattern.xml
  ↓ (references validation pattern)
Load: brain/patterns/validation-dataclass-pattern.xml
  ↓
Response: CLI testing + dataclass validation combined
```

**Files loaded**: 2 pattern files (~10KB)

---

### **Pattern 4: Debugging Assistance**

```
User: "My async test hangs forever"
  ↓
Intent: "test hangs"
  ↓
Index: debugging-id="common-async-failures"
  ↓
Load: brain/support/debugging-guide.xml
  ↓
Response: Symptom → Cause → Fix breakdown
```

**Files loaded**: 1 support file (~8KB)

---

## Benefits Demonstrated

### **1. Efficiency**

| Metric | Without brain/ | With brain/ |
|--------|---------------|-------------|
| **Context loaded** | 103KB (entire monolith) or guessing | 5-10KB (1-3 files) |
| **Response time** | Slow (search monolith) or variable | Fast (direct routing) |
| **Accuracy** | Variable (generic advice) | High (codebase-specific) |
| **Token usage** | High (large context) | Low (small context) |

### **2. Accuracy**

✅ **Proven patterns**: All examples from real refactoring sessions
✅ **Anti-patterns included**: Shows what NOT to do
✅ **Context-aware**: Specific to this codebase (pytest-asyncio, Click, etc.)
✅ **Complete examples**: Copy-paste ready, not pseudocode

### **3. Maintainability**

✅ **Single source of truth**: Patterns in brain/patterns/
✅ **Easy to update**: Edit pattern file, regenerate index
✅ **Version controlled**: Git tracks pattern changes
✅ **Self-documenting**: Each pattern explains when/why/how

### **4. Discoverability**

✅ **Natural language queries**: User doesn't need to know pattern names
✅ **Multiple query variations**: "test CLI" OR "CLI testing" OR "test click"
✅ **Intent-based routing**: Matches user intent, not exact keywords
✅ **100% pattern coverage**: All 18 patterns have intent-map entries

---

## Common Usage Scenarios

### **Scenario 1: Writing Tests**

**Most common use case** - User needs to write a test for some code.

**Example queries**:
- "How do I test this async function?"
- "Write a test for concurrent execution"
- "Test this async generator"
- "How to test fixtures?"

**Patterns used**:
- `async-test-basic`
- `concurrency-test-pattern`
- `async-generator-pattern`
- `fixture-pattern` / `async-fixture-pattern`

**Outcome**: User gets working test code with proper decorators, imports, and structure.

---

### **Scenario 2: Choosing Testing Strategy**

User is unsure whether to use mocks, fakes, or integration tests.

**Example queries**:
- "Should I mock this or use a fake?"
- "When should I use integration tests?"
- "Mock vs fake for my own service?"

**Patterns used**:
- `mock-vs-fake-decision` (decision tree)
- `fake-service-pattern`
- `integration-test-pattern`

**Outcome**: User gets decision tree → specific recommendation → implementation example.

---

### **Scenario 3: Refactoring Tests**

User has brittle, mock-heavy tests that break on every refactor.

**Example queries**:
- "My tests are too brittle, always breaking"
- "Too many mocks in my tests"
- "How to make tests less fragile?"

**Patterns used**:
- `test-refactoring-pattern`
- `pure-function-extraction-pattern`
- `integration-test-pattern`

**Outcome**: User learns to extract pure functions, replace mocks with integration tests.

---

### **Scenario 4: Debugging Test Failures**

User's test is failing with a confusing error.

**Example queries**:
- "My async test hangs forever"
- "TypeError: object Mock can't be used in 'await'"
- "Test passes but shouldn't"

**Patterns used**:
- `debugging-guide.xml` (support file)
- `anti-patterns.xml` (support file)
- Specific pattern (e.g., `async-mock-pattern`)

**Outcome**: User gets symptom → cause → fix explanation with corrected code.

---

### **Scenario 5: Implementing New Features**

User needs to implement a feature and wants to know the testable pattern.

**Example queries**:
- "How to make this CLI command testable?"
- "Validation function that's easy to test"
- "Parameterized test for multiple cases"

**Patterns used**:
- `cli-testing-pattern`
- `validation-dataclass-pattern`
- `parameterized-test-pattern`

**Outcome**: User gets refactoring guidance + implementation + test examples.

---

## Usage Statistics

Based on validation results (2025-10-04):

| Category | Count | Details |
|----------|-------|---------|
| **Pattern files** | 18 | All patterns in brain/patterns/ |
| **Support files** | 7 | Decision trees, anti-patterns, debugging |
| **Intent-map entries** | 18 | 100% coverage (all patterns discoverable) |
| **Total size** | 146KB | Patterns + support + index + metadata |
| **Typical query load** | 5-10KB | 1-3 pattern files per question |

### **Pattern Usage Frequency** (Estimated)

| Pattern | Frequency | Category |
|---------|-----------|----------|
| `async-test-basic` | Very High | Most common async test questions |
| `async-mock-pattern` | High | Common "Mock not awaitable" errors |
| `cli-testing-pattern` | Medium | CLI command refactoring |
| `integration-test-pattern` | Medium | When to skip mocks |
| `fixture-pattern` | Medium | Test setup/reusability |
| `concurrency-test-pattern` | Low | Specialized async scenarios |
| `fake-service-pattern` | Low | Advanced testing technique |

---

## Insights for Pattern Authors

When creating or updating patterns, follow these principles learned from usage:

### **1. Use Natural Language in Intent Queries**

```xml
<!-- GOOD: How developers actually ask -->
<intent query="test CLI|test click command|CLI testing|command line test">

<!-- BAD: Too formal, misses common phrases -->
<intent query="CLI unit testing pattern">
```

### **2. Include Anti-Patterns**

Users learn faster when shown what NOT to do:

```python
# ANTI-PATTERN: Mock not awaitable
mock_service.async_method = Mock(return_value=result)  # FAILS

# CORRECT: Use AsyncMock
mock_service.async_method = AsyncMock(return_value=result)  # WORKS
```

### **3. Provide Complete Examples**

Not pseudocode - actual runnable code:

```python
# COMPLETE (Good)
import pytest
from unittest.mock import AsyncMock
from src.services import MyService

@pytest.mark.asyncio
async def test_my_function():
    service = MyService()
    result = await service.process()
    assert result.success is True

# INCOMPLETE (Bad)
def test_my_function():
    # ... test here
    assert something
```

### **4. Explain the "Why"**

Every pattern should have:
- **When**: What triggers using this pattern
- **Why**: Why this approach is better than alternatives
- **What-breaks**: Common mistakes and their consequences

### **5. Cross-Reference Related Patterns**

```xml
<must-have>Pure validation functions returning dataclasses</must-have>
<!-- This signals Claude to also load validation-dataclass-pattern -->
```

---

## Future Enhancements

Potential improvements to the brain/ system:

1. **Usage analytics**: Track which patterns are accessed most often
2. **Pattern versioning**: Track pattern evolution over time
3. **Example curation**: Highlight best examples from test suite
4. **Coverage mapping**: Link patterns to actual test files as references
5. **Query expansion**: Auto-suggest related patterns based on user context

---

## Conclusion

The brain/ system transforms Claude Code's testing assistance from **generic advice** to **codebase-specific proven patterns**.

### **Key Takeaways**

✅ **Just-in-time retrieval**: Only load what's needed (5-10KB vs 103KB)
✅ **Intent-based routing**: Natural language queries → specific patterns
✅ **Proven solutions**: All examples from real refactoring sessions
✅ **100% coverage**: All 18 patterns have discoverability via intent-map
✅ **Maintenance efficiency**: Edit patterns directly, regenerate index

### **The Brain Workflow in One Sentence**

> User asks question → Claude routes via index → Loads specific pattern(s) → Applies proven solution → User gets working code

**Result**: Faster, more accurate, more contextual testing assistance for the ecreshore codebase.

---

**Version**: 1.0
**Architecture**: v1.4 (Patterns-first)
**Last Updated**: 2025-10-04
**Maintained by**: Refactoring sessions and continuous improvement loop
