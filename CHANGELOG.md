# Changelog

All notable changes to yaml-for-humans will be documented in this file.

## [1.0.2] - 2025-01-03

### Changed
- Improved CLI help formatting with better examples and security information
- Enhanced CLI documentation with more comprehensive usage examples

## [1.0.1] - 2025-01-03

### Added
- CLI support for unsafe YAML loading with `--unsafe-inputs` / `-u` flag
- Security options allowing choice between `yaml.SafeLoader` (default) and `yaml.Loader`
- Utility functions `_load_yaml()` and `_load_all_yaml()` for configurable loading
- Enhanced priority key ordering with `apiVersion`, `kind`, and `metadata` keys

### Changed
- Updated priority keys list to include Kubernetes resource identification keys
- All YAML loading in CLI now uses configurable loader based on safety flag
- Improved documentation with security warnings and usage examples

### Security
- Default behavior remains safe (uses `yaml.SafeLoader`)
- Unsafe loading requires explicit opt-in with `--unsafe-inputs` flag
- Added comprehensive documentation about security implications

## [1.0.0] - 2025-01-XX

### Added
- Initial release of human-friendly YAML formatting
- `HumanFriendlyEmitter` class with intelligent sequence formatting
- `HumanFriendlyDumper` class with priority key ordering
- Single document functions: `dump()` and `dumps()`
- Multi-document support with `dump_all()` and `dumps_all()`
- Kubernetes manifest dumper with resource ordering
- `KubernetesManifestDumper` class for specialized K8s handling
- Comprehensive test suite with unit and integration tests
- Support for mixed content sequences (strings inline, objects multiline)
- Priority key ordering for container-related keys
- Examples for single documents, multi-documents, and Kubernetes manifests

### Features
- **Smart sequence formatting**: Automatically detects content type and formats appropriately
- **Indented sequences**: Dashes are properly indented under parent containers
- **Priority key ordering**: Important keys like `name`, `image`, `command` appear first
- **Multi-document support**: Handle multiple YAML documents with proper `---` separators
- **Kubernetes resource ordering**: Automatic ordering following deployment best practices
- **Valid YAML output**: All generated YAML passes standard validation
- **Backward compatibility**: Drop-in replacement for standard PyYAML dumpers

### Multi-Document Features
- **Document separation**: Proper `---` separators between documents
- **Resource ordering**: Kubernetes resources ordered by dependency (Namespace → ConfigMap → Service → Deployment)
- **Flexible options**: Support for explicit end markers (`...`) and custom indentation
- **Performance optimized**: Efficient handling of large manifest files

### Technical Details
- Overrides PyYAML's `expect_block_sequence()` to force indented sequences
- Uses event-driven detection to determine inline vs multiline formatting  
- Implements custom `represent_mapping()` for key ordering
- Maintains proper indentation hierarchy throughout nested structures
- Multi-document handling through `MultiDocumentDumper` class
- Kubernetes resource prioritization via configurable ordering rules