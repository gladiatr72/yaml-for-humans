# API Reference

## Single Document Functions

### `dumps(data, **kwargs)`
Serialize Python object to YAML string with human-friendly formatting.

**Parameters:**
- `data`: Python object to serialize
- `**kwargs`: Additional arguments passed to HumanFriendlyDumper

**Returns:** YAML string

### `dump(data, stream, **kwargs)`
Serialize Python object to YAML and write to stream.

**Parameters:**
- `data`: Python object to serialize  
- `stream`: File-like object to write to
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

### `HumanFriendlyEmitter`
Core emitter class that handles the sequence formatting logic.

### `MultiDocumentDumper`
Dumper for multiple YAML documents with human-friendly formatting.

### `KubernetesManifestDumper`
Specialized dumper for Kubernetes manifests with resource ordering.