# Test Data Files

This directory contains various test data files that demonstrate the different input formats supported by yaml-for-humans CLI.

## File Types and Examples

### Single Document YAML Files
- **`whee.yaml`** - Single Kubernetes Deployment manifest (existing)
- **`docker-compose.json`** - Docker Compose configuration as JSON (single document)
- **`primitive-items.json`** - JSON with items array containing primitives (should not split)

### Multi-Document YAML Files  
- **`gotk-components.yaml`** - Large Flux GitOps Toolkit components (37 documents)
- **`multi-service.yaml`** - Multiple Kubernetes Service definitions
- **`ci-pipeline.yaml`** - Multiple GitHub Actions workflow definitions
- **`configs.yaml`** - Application configurations for different environments

### JSON with Items Arrays (Multi-Document)
- **`k8s-list.json`** - Kubernetes List resource with Service, Deployment, and ConfigMap
- **`flux-deployments.json`** - Flux deployment resources (existing)

### JSON Lines Format (Multi-Document)
- **`users.jsonl`** - User records, one JSON object per line
- **`logs.jsonl`** - Application log entries, one JSON object per line

## Testing the Files

You can test any of these files with the CLI:

```bash
# Single document processing
python -m yaml_for_humans.cli --inputs tests/test-data/whee.yaml

# Multi-document YAML (auto-detected)
python -m yaml_for_humans.cli --inputs tests/test-data/gotk-components.yaml

# JSON with items array (auto-splits)
python -m yaml_for_humans.cli --inputs tests/test-data/k8s-list.json

# JSON Lines format (auto-splits) 
python -m yaml_for_humans.cli --inputs tests/test-data/users.jsonl

# Multiple files at once
python -m yaml_for_humans.cli --inputs "tests/test-data/k8s-list.json,tests/test-data/configs.yaml"

# JSON with primitive items (stays single document)
python -m yaml_for_humans.cli --inputs tests/test-data/primitive-items.json
```

## Expected Behavior

### Single Document Output
Files that produce single YAML documents (no `---` separators):
- `whee.yaml`
- `docker-compose.json` 
- `primitive-items.json`

### Multi-Document Output
Files that produce multiple YAML documents (with `---` separators):
- `gotk-components.yaml` (37 documents)
- `multi-service.yaml` (3 documents)
- `ci-pipeline.yaml` (3 documents) 
- `configs.yaml` (3 documents)
- `k8s-list.json` (3 documents from items array)
- `users.jsonl` (4 documents, one per line)
- `logs.jsonl` (4 documents, one per line)

## Format Detection

The CLI automatically detects:
- **YAML files** with `---` separators → Multi-document YAML processing
- **JSON files** with `items` array of objects → Split into separate documents
- **JSON files** with `items` array of primitives → Single document
- **JSON Lines files** (`.jsonl` or multiple JSON objects on separate lines) → Multi-document
- **Regular JSON/YAML** → Single document