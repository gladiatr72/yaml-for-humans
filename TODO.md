# Whitespace Detection and Preservation Analysis

## Current Implementation Status

The yaml-for-humans codebase already has sophisticated whitespace handling through three main approaches:

### 1. **FormattingAwareLoader System** (src/yaml_for_humans/formatting_aware.py:1-283)
**Current Capabilities:**
- Automatically detects empty lines during YAML parsing
- Stores metadata in `FormattingMetadata` objects with `empty_lines_before` counts
- Uses optimized `FormattingAwareComposer` that calculates line positions during parse
- Tracks whitespace for both mappings and sequences
- Preserves metadata through `FormattingAwareDict` and `FormattingAwareList` containers

**Detection Method:**
- Line-by-line analysis during PyYAML parsing phase
- Caches end-line calculations for performance (`_end_line_cache`)
- Non-recursive iterative traversal for deep structures
- Pre-calculates all end lines in single pass to avoid redundant calculations

### 2. **FormattingAwareDumper System** (src/yaml_for_humans/formatting_emitter.py:1-174)
**Current Capabilities:**
- Renders preserved whitespace using special markers (`__EMPTY_LINES_N__`)
- Post-processes output to convert markers to actual newlines
- Maintains human-friendly formatting while preserving original structure
- Thread-safe buffer pooling for performance optimization

### 3. **Convenience Functions** (src/yaml_for_humans/dumper.py:1-286)
**Current Capabilities:**
- `load_with_formatting()` - automatically loads with whitespace metadata
- `dumps(preserve_empty_lines=True)` - renders with preserved whitespace
- Regex-based marker processing for efficient empty line injection
- Auto-detection of file paths vs YAML content

## Automatic Detection Strategies

Based on the codebase analysis, here are the options for automatic whitespace detection and preservation:

### **Option 1: Enhance Current Detection (Recommended)**
**Implementation:** Extend existing `FormattingAwareComposer`
**Benefits:**
- Builds on proven, optimized foundation
- Already handles complex YAML structures
- Performance-optimized with caching and pooling

**Enhancements:**
```python
# Pattern detection in FormattingAwareComposer
def _detect_whitespace_patterns(self, node):
    """Detect structural whitespace patterns automatically."""
    patterns = {
        'section_separators': self._detect_section_breaks(node),
        'logical_groupings': self._detect_logical_groups(node),
        'hierarchy_spacing': self._detect_hierarchy_spacing(node)
    }
    return patterns

def _detect_section_breaks(self, node):
    """Detect empty lines that separate logical sections."""
    # Kubernetes manifest sections (metadata, spec, status)
    # Kustomization sections (resources, images, patches)
    # CI pipeline sections (jobs, steps, triggers)

def _detect_logical_groups(self, node):
    """Detect empty lines that group related items."""
    # Container definitions in pods
    # Resource groupings in kustomizations
    # Job groupings in CI workflows
```

### **Option 2: Heuristic-Based Auto-Detection**
**Implementation:** Pattern recognition during parsing
**Benefits:**
- Intelligent preservation without manual tagging
- Context-aware whitespace decisions

**Detection Heuristics:**
- **Kubernetes Resources:** Empty lines between `apiVersion/kind/metadata` and `spec`
- **Kustomization Files:** Empty lines between `resources`, `images`, `patches` sections
- **CI Pipelines:** Empty lines between job definitions and workflow sections
- **Container Configs:** Empty lines between container definitions
- **List Groupings:** Empty lines that separate semantic groups in sequences

### **Option 3: Smart Default Preservation**
**Implementation:** Conservative whitespace preservation with intelligent filtering

```python
def smart_preserve_whitespace(content):
    """Apply intelligent whitespace preservation based on content analysis."""
    detected_type = detect_yaml_type(content)  # k8s, kustomization, ci, generic

    if detected_type == 'kubernetes':
        return preserve_k8s_whitespace_patterns(content)
    elif detected_type == 'kustomization':
        return preserve_kustomization_patterns(content)
    elif detected_type == 'ci_pipeline':
        return preserve_ci_patterns(content)
    else:
        return preserve_structural_whitespace(content)
```

### **Option 4: Learning-Based Detection**
**Implementation:** Analyze common whitespace patterns in target domains
**Benefits:**
- Adapts to user/domain preferences
- Improves over time

**Pattern Learning:**
- Analyze existing well-formatted YAML in domain (K8s, CI/CD, etc.)
- Extract common whitespace patterns
- Apply statistical models to determine "good" vs "noise" whitespace
- Build domain-specific preservation rules

### **Option 5: Configurable Detection Rules**
**Implementation:** User-defined rules for whitespace preservation

```python
whitespace_rules = {
    'preserve_section_breaks': True,      # Empty lines between major sections
    'preserve_list_groupings': True,      # Empty lines in sequence groupings
    'preserve_single_lines': False,       # Don't preserve isolated single empty lines
    'min_group_size': 2,                  # Only preserve if groups ≥ 2 items
    'kubernetes_sections': True,          # Special handling for K8s manifests
    'max_consecutive': 2,                 # Limit consecutive empty lines
}
```

## Recommended Implementation Approach

### **Phase 1: Enhanced Current System**
1. **Extend FormattingAwareComposer:** Add pattern detection methods
2. **Smart Defaults:** Implement heuristic-based detection for common YAML types
3. **Preserve Existing API:** Maintain backward compatibility with current `preserve_empty_lines` flag

### **Phase 2: Intelligent Auto-Detection**
1. **Content Analysis:** Add YAML type detection (K8s, Kustomization, CI, etc.)
2. **Pattern Recognition:** Implement domain-specific whitespace preservation rules
3. **Configuration Options:** Allow users to customize detection behavior

### **Phase 3: Advanced Features**
1. **Learning System:** Analyze user preferences and common patterns
2. **Performance Optimization:** Further optimize detection algorithms
3. **IDE Integration:** Provide real-time whitespace suggestions

## Key Insights from Codebase

1. **Performance Focus:** Current implementation uses caching, pooling, and optimized algorithms
2. **Modularity:** Clean separation between detection (Composer), storage (FormattingAware classes), and rendering (Emitter)
3. **Proven Foundation:** Existing system handles complex cases like nested structures, multi-document YAML
4. **Test Coverage:** Comprehensive tests including edge cases and domain-specific examples (tests/test_empty_line_preservation.py:1-157)

The codebase is well-positioned for enhanced automatic whitespace detection while maintaining its performance and reliability characteristics.