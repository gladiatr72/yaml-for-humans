"""
Type stubs for CLI module.
"""

from typing import Optional, Any, Dict, List, Tuple
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessingContext:
    """Immutable context for processing operations."""
    unsafe_inputs: bool
    preserve_empty_lines: bool
    preserve_comments: bool

    @property
    def is_preservation_enabled(self) -> bool: ...

    @property
    def is_safe_mode(self) -> bool: ...

@dataclass(frozen=True)
class OutputContext:
    """Configuration for output operations."""
    indent: int
    preserve_empty_lines: bool
    preserve_comments: bool
    auto_create_dirs: bool

@dataclass(frozen=True)
class CliConfig:
    """Complete CLI configuration context."""
    indent: int
    timeout: int
    inputs: Optional[str]
    output: Optional[str]
    auto: bool
    processing: ProcessingContext

    @property
    def output_context(self) -> OutputContext: ...

class InputProcessor:
    """Handles document processing from various input sources."""
    def __init__(self, context: ProcessingContext) -> None: ...

def huml(
    indent: int = ...,
) -> None:
    """
    Convert YAML or JSON input to human-friendly YAML.

    Reads from stdin and writes to stdout with automatic format detection.

    Args:
        indent: Indentation level (default: 2)
    """
    ...

def _process_input_source(
    inputs: Optional[str], processor: InputProcessor, timeout: int
) -> Tuple[List[Any], List[Dict[str, Any]]]: ...

def _handle_output_generation(
    documents: List[Any],
    document_sources: List[Dict[str, Any]],
    config: CliConfig,
) -> None: ...

def _huml_main(
    config: Optional[CliConfig] = ...,
    # Legacy parameters for backwards compatibility
    indent: Optional[int] = ...,
    timeout: Optional[int] = ...,
    inputs: Optional[str] = ...,
    output: Optional[str] = ...,
    auto: Optional[bool] = ...,
    unsafe_inputs: Optional[bool] = ...,
    preserve_empty_lines: Optional[bool] = ...,
    preserve_comments: Optional[bool] = ...,
) -> None:
    """
    Main CLI functionality for processing YAML/JSON input with automatic format detection.

    Args:
        config: CliConfig object (preferred). If provided, other args ignored.
        **kwargs: Legacy individual parameters for backwards compatibility.
    """
    ...

def _looks_like_json(text: str) -> bool:
    """Simple heuristic to detect JSON input."""
    ...

def _is_multi_document_yaml(text: str) -> bool:
    """Check if text contains multi-document YAML."""
    ...

def _is_json_lines(text: str) -> bool:
    """Check if text is JSON Lines format."""
    ...

def _has_items_array(data: Any) -> bool:
    """Check if data has an 'items' array (typical of Kubernetes list objects)."""
    ...

def _generate_k8s_filename(
    document: Dict[str, Any],
    source_file: Optional[str] = ...,
    stdin_position: Optional[int] = ...,
    add_prefix: bool = ...,
) -> str:
    """
    Generate appropriate filename for Kubernetes resources.

    Args:
        document: YAML document (should have apiVersion, kind, metadata)
        source_file: Source file path for fallback naming
        stdin_position: Position in stdin for fallback naming
        add_prefix: If True, prepend 2-digit resource ordering prefix

    Returns:
        Generated filename with optional prefix
    """
    ...

def _read_stdin_with_timeout(timeout_ms: int = ...) -> str:
    """
    Read from stdin with a timeout.

    Args:
        timeout_ms: Timeout in milliseconds

    Returns:
        Input text from stdin

    Raises:
        TimeoutError: If timeout is exceeded
    """
    ...

def _write_to_output(
    documents: List[Any],
    output_path: str,
    auto: bool = ...,
    indent: int = ...,
    document_sources: Optional[List[Dict[str, Any]]] = ...,
    preserve_empty_lines: bool = ...,
    preserve_comments: bool = ...,
) -> None:
    """
    Write documents to output file or directory.

    DEPRECATED: This function is maintained for backwards compatibility.
    New code should use OutputWriter.write() directly with an OutputContext.

    Args:
        documents: List of parsed documents
        output_path: Output path
        auto: Whether to auto-create directories
        indent: YAML indentation level
        document_sources: Source information for each document
        preserve_empty_lines: Preserve empty lines from original YAML (default: True)
        preserve_comments: Preserve comments from original YAML (default: True)
    """
    ...
