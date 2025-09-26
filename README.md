# YAML for Humans

Human-friendly YAML formatting for PyYAML that makes YAML more readable and intuitive.

## Features

- **Comment preservation**: Keeps original YAML comments (both standalone and end-of-line)
- **Empty line preservation**: Maintains empty lines from original YAML for better readability
- **Intelligent sequence formatting**: Strings on same line as dash (`- value`), objects on separate lines
- **Indented sequences**: Dashes are properly indented under their parent containers
- **Priority key ordering**: Important keys like `name`, `image`, `command` appear first in mappings
- **Multi-document support**: Handle multiple YAML documents with proper `---` separators
- **Kubernetes manifest ordering**: Automatic resource ordering following best practices
- **High performance**: Optimized with 75% faster string processing and 67% less memory usage
- **Valid YAML output**: All generated YAML passes standard YAML validation
- **Drop-in replacement**: Compatible with existing PyYAML code

## Quick Start

```python
from yaml_for_humans import dumps, dump, load_with_formatting

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

# Or load existing YAML with formatting preservation (comments + empty lines)
formatted_data = load_with_formatting('existing-config.yaml')
preserved_output = dumps(formatted_data)  # Preserves comments and empty lines by default
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
2. **Priority key ordering**: Important keys (`apiVersion`, `kind`, `metadata`, `name`, `image`, `imagePullPolicy`, `env`, `envFrom`, `command`, `args`) appear first
3. **Smart formatting**: Complex objects use separate lines, simple strings stay inline
4. **Consistent indentation**: Maintains visual hierarchy throughout the document

## Comment and Formatting Preservation

YAML for Humans preserves comments and empty lines from the original YAML to maintain document structure and readability:

```python
from yaml_for_humans import load_with_formatting, dumps

# Load YAML file with comments and empty lines
yaml_content = '''# Application Configuration
app_name: web-service
version: 2.1.0

# Network Configuration
port: 8080
debug: false

# Database Settings
database:
  host: localhost  # Production host
  port: 5432
'''

data = load_with_formatting(yaml_content)

# Preserve original formatting (default behavior)
preserved_output = dumps(data)
print("With formatting preservation:")
print(preserved_output)

# Disable preservation for compact output
compact_output = dumps(data, preserve_comments=False, preserve_empty_lines=False)
print("\nCompact output:")
print(compact_output)
```

**With formatting preservation:**
```yaml
# Application Configuration
app_name: web-service
version: 2.1.0

# Network Configuration
port: 8080
debug: false

# Database Settings
database:
  host: localhost  # Production host
  port: 5432
```

**Compact output:**
```yaml
app_name: web-service
version: 2.1.0
port: 8080
debug: false
database:
  host: localhost
  port: 5432
```

This feature is especially useful for:
- **Configuration files** where comments explain complex settings
- **Kustomization files** where empty lines separate different resource types and configurations
- **Kubernetes manifests** where comments document resource purposes
- **CI/CD pipelines** where comments explain workflow stages

### Performance Options

Choose the right balance of features vs. performance:

```python
# Maximum performance (~7% overhead vs PyYAML)
output = dumps(data, preserve_comments=False, preserve_empty_lines=False)

# Balanced performance (preserve comments only)
output = dumps(data, preserve_comments=True, preserve_empty_lines=False)

# Full preservation (default, ~2x overhead vs PyYAML)
output = dumps(data)  # preserves both comments and empty lines
```

## Installation

Install the core library:
```bash
uv add yaml-for-humans
```

Or install with CLI support:
```bash
uv add yaml-for-humans[cli]
```

Then import and use:

```python
from yaml_for_humans import dumps, dump, load_with_formatting
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

# Custom stdin timeout (default: 2000ms)
cat config.yaml | huml --timeout 100

# Use unsafe YAML loader (allows arbitrary Python objects - use with caution)
cat config-with-python-objects.yaml | huml --unsafe-inputs

# Process JSON Lines format (one JSON object per line)
cat logs.jsonl | huml

# Handle Kubernetes API responses with items arrays
kubectl get deployments -o json | huml  # Automatically splits items into documents

# Process file inputs instead of stdin
huml --inputs config.yaml,deploy.json

# Process multiple files with glob patterns
huml --inputs "*.json,configs/*.yaml"

# Preserve formatting (default behavior)
cat config.yaml | huml

# Disable formatting preservation for maximum performance
cat config.yaml | huml --no-preserve-comments --no-preserve-empty-lines

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
- `-t, --timeout INTEGER`: Stdin timeout in milliseconds (default: 2000)
- `-u, --unsafe-inputs`: Use unsafe YAML loader (allows arbitrary Python objects, use with caution)
- `--preserve-comments / --no-preserve-comments`: Preserve comments from original YAML (default: preserve)
- `--preserve-empty-lines / --no-preserve-empty-lines`: Preserve empty lines from original YAML (default: preserve)
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

## Performance

YAML for Humans is optimized for both performance and readability:

- **Basic mode**: Only ~7% overhead vs PyYAML while maintaining human-friendly formatting
- **With formatting preservation**: ~2x overhead vs PyYAML for full comment and empty line preservation
- **Recent optimizations**: 75% faster string processing, 67% less memory usage
- **Smart defaults**: Preserves formatting by default, but easily configurable for performance-critical applications

## API Reference

For detailed API documentation, see [API.md](API.md).

