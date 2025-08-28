# YAML for Humans

Human-friendly YAML formatting for PyYAML that makes YAML more readable and intuitive.

## Features

- **Intelligent sequence formatting**: Strings on same line as dash (`- value`), objects on separate lines
- **Indented sequences**: Dashes are properly indented under their parent containers
- **Priority key ordering**: Important keys like `name`, `image`, `command` appear first in mappings
- **Multi-document support**: Handle multiple YAML documents with proper `---` separators
- **Kubernetes manifest ordering**: Automatic resource ordering following best practices
- **Valid YAML output**: All generated YAML passes standard YAML validation
- **Drop-in replacement**: Compatible with existing PyYAML code

## Quick Start

```python
from yaml_for_humans import dumps, dump

# Your data
data = {
    'containers': [
        {
            'ports': [8080, 9090],
            'name': 'web-server',  # name will appear first
            'image': 'nginx:latest',
            'command': ['/bin/sh', '-c', 'nginx -g "daemon off;"']
        }
    ]
}

# Generate human-friendly YAML
yaml_output = dumps(data)
print(yaml_output)
```

Output:
```yaml
containers:
  -
    name: web-server          # Priority keys first
    image: nginx:latest
    command:
      - /bin/sh               # Strings inline with dash
      - -c
      - nginx -g "daemon off;"
    ports:
      - 8080
      - 9090
```

## Comparison with Standard PyYAML

### Standard PyYAML Output
```yaml
containers:
- command:
  - /bin/sh
  - -c
  - nginx -g "daemon off;"
  image: nginx:latest
  name: web-server
  ports:
  - 8080
  - 9090
```

### YAML for Humans Output
```yaml
containers:
  -
    name: web-server
    image: nginx:latest
    command:
      - /bin/sh
      - -c
      - nginx -g "daemon off;"
    ports:
      - 8080
      - 9090
```

## Key Differences

1. **Indented sequences**: Dashes are indented under parent containers for better hierarchy visualization
2. **Priority key ordering**: Container-related keys (`name`, `image`, `imagePullPolicy`, `env`, `envFrom`, `command`, `args`) appear first
3. **Smart formatting**: Complex objects use separate lines, simple strings stay inline
4. **Consistent indentation**: Maintains visual hierarchy throughout the document

## Installation

Install the core library:
```bash
uv add yaml-for-humans
```

Or install with CLI support:
```bash
uv add yaml-for-humans[cli]
```

### Development Installation

For development, install in editable mode:
```bash
# Install the package in editable mode
uv pip install -e .

# Or with CLI dependencies for development
uv pip install -e .[cli]
```


Then import and use:

```python
from yaml_for_humans import dumps, dump
```

## Command Line Interface (Optional)

The `huml` command-line utility converts YAML or JSON input to human-friendly YAML. It accepts input through stdin pipes or file processing:

```bash
# Convert JSON to human-friendly YAML
echo '{"name": "web", "ports": [80, 443]}' | huml

# Process existing YAML files
cat config.yaml | huml

# Use with kubectl
kubectl get deployment -o yaml | huml

# Process multi-document YAML (auto-detected)
cat manifests.yaml | huml

# Process JSON input (automatic detection)
echo '{"containers": [...]}' | huml

# Custom indentation
cat config.yaml | huml --indent 4

# Custom stdin timeout (default: 50ms)
cat config.yaml | huml --timeout 100

# Process JSON Lines format (one JSON object per line)
cat logs.jsonl | huml

# Handle Kubernetes API responses with items arrays
kubectl get deployments -o json | huml  # Automatically splits items into documents

# Process file inputs instead of stdin
huml --inputs config.yaml,deploy.json

# Process multiple files with glob patterns  
huml --inputs "*.json,configs/*.yaml"

# Process all files in a directory (add trailing slash)
huml --inputs /path/to/configs/

# Mix glob patterns, directories, and explicit files
huml --inputs "*.json,/configs/,specific.yaml"

# Output to file or directory
kubectl get all -o json | huml --output ./k8s-resources/
```

### Stdin Input Handling

The CLI automatically detects input format and handles:

- **JSON objects**: Single objects or arrays
- **JSON Lines**: Multiple JSON objects, one per line  
- **YAML documents**: Single or multi-document with `---` separators
- **Kubernetes API responses**: Objects with `items` arrays are split into separate documents
- **Format detection**: Automatic detection based on content analysis

### CLI Options

- `-i, --inputs TEXT`: Comma-delimited list of JSON/YAML file paths to process. Supports:
  - Explicit file paths: `config.yaml,deploy.json`
  - Glob patterns: `*.json,configs/*.yaml`
  - Directories: `/path/to/directory/` (must end with `/`)
  - Mixed combinations: `*.json,/configs/,specific.yaml`
- `-o, --output TEXT`: Output file or directory path (if ends with `/`, treated as directory)
- `--auto`: Automatically create output directories if they don't exist
- `--indent INTEGER`: Indentation level (default: 2)
- `-t, --timeout INTEGER`: Stdin timeout in milliseconds (default: 50)
- `--help`: Show help message
- `--version`: Show version information

#### Input Processing Behavior

- **File Globbing**: Patterns like `*.json` and `configs/*.yaml` are expanded to match files
- **Directory Processing**: Paths ending with `/` process all valid JSON/YAML files in the directory
- **Invalid File Handling**: Files that can't be parsed or aren't JSON/YAML are skipped with warnings
- **Robust Processing**: Processing continues even if some files fail, reporting errors but not stopping
- **Format Detection**: Files are validated based on extension (`.json`, `.yaml`, `.yml`, `.jsonl`) and content analysis

## Multi-Document Support

### Basic Multi-Document Usage

```python
from yaml_for_humans import dumps_all, dump_all

documents = [
    {'config': {'version': '1.0', 'features': ['auth', 'logging']}},
    {'services': [{'name': 'web', 'image': 'nginx'}]},
    {'metadata': {'created': '2025-01-01'}}
]

# Generate multi-document YAML
yaml_output = dumps_all(documents)
print(yaml_output)
```

Output:
```yaml
config:
  version: '1.0'
  features:
    - auth
    - logging

---
services:
  -
    name: web
    image: nginx

---
metadata:
  created: '2025-01-01'
```

### Kubernetes Manifests

```python
from yaml_for_humans import dumps_kubernetes_manifests

manifests = [
    {'apiVersion': 'apps/v1', 'kind': 'Deployment', ...},
    {'apiVersion': 'v1', 'kind': 'Service', ...},
    {'apiVersion': 'v1', 'kind': 'ConfigMap', ...},
    {'apiVersion': 'v1', 'kind': 'Namespace', ...}
]

# Automatically orders resources: Namespace, ConfigMap, Service, Deployment
ordered_yaml = dumps_kubernetes_manifests(manifests)
```

## API Reference

For detailed API documentation, see [API.md](API.md).

## Testing

Run the test suite with pytest:

```bash
uv run pytest tests/ -v
```

### Test Coverage

- **Unit tests**: Core emitter functionality, key ordering, YAML validity
- **Integration tests**: Real-world examples including Kubernetes manifests, Docker Compose files, CI/CD pipelines
- **Round-trip tests**: Ensure generated YAML can be parsed back correctly

## Examples

Run the example scripts to see the formatting in action:

```bash
uv run python examples/kubernetes_example.py
uv run python examples/docker_compose_example.py
uv run python examples/multi_document_example.py
uv run python examples/kubernetes_manifests_example.py
```

The examples demonstrate:
- Kubernetes deployments with priority key ordering
- Docker Compose files with intelligent sequence formatting
- Multi-document YAML with proper separators
- Kubernetes manifest ordering and resource prioritization

