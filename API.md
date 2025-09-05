# API Reference

## Single Document Functions

### `dumps(data, **kwargs)`
Serialize Python object to YAML string with human-friendly formatting.

**Parameters:**
- `data`: Python object to serialize
- `preserve_empty_lines` (bool): Preserve empty lines from FormattingAware objects (default: False)
- `**kwargs`: Additional arguments passed to HumanFriendlyDumper

**Returns:** YAML string

### `load_with_formatting(stream)`
Load YAML with formatting metadata preservation for empty line handling.

**Parameters:**
- `stream`: Input stream, file path string, or YAML string content

**Returns:** Python object with formatting metadata attached (FormattingAwareDict/List)

**Example:**
```python
# Load from file path
data = load_with_formatting('config.yaml')

# Load from YAML string  
data = load_with_formatting('key: value\n\nother: data')

# Load from file stream
with open('config.yaml', 'r') as f:
    data = load_with_formatting(f)

# Use with empty line preservation
output = dumps(data, preserve_empty_lines=True)
```

### `dump(data, stream, **kwargs)`
Serialize Python object to YAML and write to stream.

**Parameters:**
- `data`: Python object to serialize  
- `stream`: File-like object to write to
- `preserve_empty_lines` (bool): Preserve empty lines from FormattingAware objects (default: False)
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
Dictionary subclass that stores formatting metadata for empty line preservation.

**Methods:**
- `_get_key_formatting(key)`: Get formatting metadata for a specific key
- `_set_key_formatting(key, formatting)`: Set formatting metadata for a key

### `FormattingAwareList`  
List subclass that stores formatting metadata for empty line preservation.

**Methods:**
- `_get_item_formatting(index)`: Get formatting metadata for a specific item
- `_set_item_formatting(index, formatting)`: Set formatting metadata for an item

### `FormattingAwareLoader`
Complete YAML loader that preserves formatting information during parsing.

**Features:**
- Captures empty lines between mapping keys and sequence items
- Handles complex nested structures (sequences within mappings)
- Creates FormattingAwareDict and FormattingAwareList objects with metadata

## CLI Options

### Empty Line Preservation
The CLI preserves empty lines from original YAML by default:

**Flag:** `--preserve-empty-lines/--no-preserve-empty-lines` (default: true)

**Examples:**
```bash
# Preserve empty lines (default behavior)
cat kustomization.yaml | huml

# Disable empty line preservation  
cat kustomization.yaml | huml --no-preserve-empty-lines
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