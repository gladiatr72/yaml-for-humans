# API Reference

## Single Document Functions

### `dumps(data, **kwargs)`
Serialize Python object to YAML string with human-friendly formatting.

**Parameters:**
- `data`: Python object to serialize
- `preserve_empty_lines` (bool): Preserve empty lines from FormattingAware objects (default: True)
- `preserve_comments` (bool): Preserve comments from FormattingAware objects (default: True)
- `**kwargs`: Additional arguments passed to HumanFriendlyDumper

**Returns:** YAML string

**Performance Notes:**
- Basic mode (no preservation): ~7% overhead vs PyYAML
- With formatting preservation: ~2x overhead vs PyYAML
- Recent optimizations reduced string processing overhead by ~75% and memory usage by ~67%

### `load_with_formatting(stream)`
Load YAML with formatting metadata preservation for comments and empty lines.

**Parameters:**
- `stream`: Input stream, file path string, or YAML string content

**Returns:** Python object with formatting metadata attached (FormattingAwareDict/List)

**Features:**
- Preserves comments (both standalone and end-of-line)
- Preserves blank line spacing
- Uses lazy loading for optimal memory usage
- Optimized I/O with 75% reduction for StringIO streams

**Example:**
```python
# Load from file path
data = load_with_formatting('config.yaml')

# Load from YAML string  
data = load_with_formatting('key: value\n\nother: data')

# Load from file stream
with open('config.yaml', 'r') as f:
    data = load_with_formatting(f)

# Use with full formatting preservation (default)
output = dumps(data)  # preserves comments and empty lines

# Use with selective preservation
output = dumps(data, preserve_comments=True, preserve_empty_lines=False)
output = dumps(data, preserve_comments=False, preserve_empty_lines=True)

# Disable preservation for maximum performance
output = dumps(data, preserve_comments=False, preserve_empty_lines=False)
```

### `dump(data, stream, **kwargs)`
Serialize Python object to YAML and write to stream.

**Parameters:**
- `data`: Python object to serialize
- `stream`: File-like object to write to
- `preserve_empty_lines` (bool): Preserve empty lines from FormattingAware objects (default: True)
- `preserve_comments` (bool): Preserve comments from FormattingAware objects (default: True)
- `**kwargs`: Additional arguments passed to HumanFriendlyDumper

## Multi-Document Functions

### `dumps_all(documents, **kwargs)`
Serialize multiple Python objects to multi-document YAML string.

**Parameters:**
- `documents`: Iterable of Python objects to serialize
- `**kwargs`: Additional arguments (explicit_start, explicit_end, etc.)

**Returns:** Multi-document YAML string

### `dump_all(documents, stream, **kwargs)`
Serialize multiple Python objects to multi-document YAML stream.

### `dumps_kubernetes_manifests(manifests, **kwargs)`
Serialize Kubernetes manifests with automatic resource ordering.

**Parameters:**
- `manifests`: Iterable of Kubernetes resource objects
- `**kwargs`: Additional arguments (sort_resources=True by default)

**Returns:** Ordered multi-document YAML string

### `dump_kubernetes_manifests(manifests, stream, **kwargs)`
Serialize Kubernetes manifests to stream with resource ordering.

## Classes

### `HumanFriendlyDumper`
Complete YAML dumper class with human-friendly formatting.

**Priority Keys:** The following keys appear first in mappings when present:
- `apiVersion`, `kind`, `metadata` (Kubernetes resource identification)
- `name`, `image`, `imagePullPolicy` (Container identification)  
- `env`, `envFrom`, `command`, `args` (Container configuration)

### `HumanFriendlyEmitter`
Core emitter class that handles the sequence formatting logic.

### `MultiDocumentDumper`
Dumper for multiple YAML documents with human-friendly formatting.

### `KubernetesManifestDumper`
Specialized dumper for Kubernetes manifests with resource ordering.

### `FormattingAwareDict`
Dictionary subclass that stores formatting metadata for empty line and comment preservation.

**Methods:**
- `_get_key_formatting(key)`: Get formatting metadata for a specific key
- `_set_key_formatting(key, formatting)`: Set formatting metadata for a key
- `_get_key_comments(key)`: Get comment metadata for a specific key
- `_set_key_comments(key, comment_metadata)`: Set comment metadata for a key

### `FormattingAwareList`
List subclass that stores formatting metadata for empty line and comment preservation.

**Methods:**
- `_get_item_formatting(index)`: Get formatting metadata for a specific item
- `_set_item_formatting(index, formatting)`: Set formatting metadata for an item
- `_get_item_comments(index)`: Get comment metadata for a specific item
- `_set_item_comments(index, comment_metadata)`: Set comment metadata for an item

### `FormattingAwareLoader`
Complete YAML loader that preserves formatting information during parsing.

**Features:**
- Captures comments (standalone and end-of-line)
- Captures empty lines between mapping keys and sequence items
- Handles complex nested structures (sequences within mappings)
- Creates FormattingAwareDict and FormattingAwareList objects with metadata
- Uses lazy loading for optimal memory usage (67% reduction)
- Optimized I/O operations (75% reduction for StringIO streams)

## CLI Options

### Formatting Preservation
The CLI preserves comments and empty lines by default. Use flags to control preservation behavior:

**Flags:**
- `--preserve-comments` / `--no-preserve-comments` (default: preserve enabled)
- `--preserve-empty-lines` / `--no-preserve-empty-lines` (default: preserve enabled)

**Examples:**
```bash
# Default behavior (preserves comments and empty lines)
cat kustomization.yaml | huml

# Disable all preservation for maximum performance
cat kustomization.yaml | huml --no-preserve-comments --no-preserve-empty-lines

# Preserve only comments
cat kustomization.yaml | huml --preserve-comments --no-preserve-empty-lines

# Preserve only empty lines
cat kustomization.yaml | huml --no-preserve-comments --preserve-empty-lines
```

### Security Options

The command-line interface supports both safe and unsafe YAML loading:

**Safe Loading (Default):**
- Uses `yaml.SafeLoader` 
- Prevents arbitrary Python object instantiation
- Rejects YAML with Python-specific tags like `!!python/dict`
- Recommended for untrusted input

**Unsafe Loading (`--unsafe-inputs`):**
- Uses `yaml.Loader`
- Allows arbitrary Python object instantiation
- Processes Python-specific YAML tags
- **Use with caution** - only for trusted input

**Example:**
```bash
# Safe (default) - will reject Python objects
cat untrusted.yaml | huml

# Unsafe - allows Python objects
cat trusted-with-python-objects.yaml | huml --unsafe-inputs
```

## Performance Optimization

### Recent Performance Improvements

YAML for Humans has been optimized for better performance while maintaining functionality:

**String Processing Optimizations:**
- 75% reduction in string operations during comment extraction
- Eliminated redundant `.strip()` calls in parsing loops
- Optimized JSON Lines format detection

**Memory Usage Optimizations:**
- 67% reduction in peak memory usage (3x → 1x file size)
- Lazy loading for raw YAML content
- Efficient StringIO handling with `getvalue()` method

**I/O Optimizations:**
- 75% reduction in I/O operations for StringIO streams
- Minimized file seek operations
- Cached content reading where possible

### Performance Characteristics

**Basic Mode (no preservation):**
- ~7% overhead vs PyYAML
- Suitable for high-performance scenarios
- Maintains human-friendly formatting

**With Formatting Preservation:**
- ~2x overhead vs PyYAML (significantly reduced from pre-optimization)
- Preserves comments and blank lines
- Reasonable trade-off for human-readable output

### Benchmarking

Use the included benchmark script to measure performance on your system:

```bash
# Run comprehensive performance benchmark
uv run python3 benchmark.py

# Results include:
# - PyYAML vs YAML4Humans comparison
# - Formatting preservation impact analysis
# - Optimization effectiveness demonstration
```

### Performance Recommendations

**For High-Performance Applications:**
```python
# Disable preservation for maximum speed
output = dumps(data, preserve_comments=False, preserve_empty_lines=False)
```

**For Balanced Performance:**
```python
# Use selective preservation
output = dumps(data, preserve_comments=True, preserve_empty_lines=False)
# or
output = dumps(data, preserve_comments=False, preserve_empty_lines=True)
```

**For Human-Readable Output:**
```python
# Full preservation (default)
output = dumps(data)  # preserves both comments and empty lines
```