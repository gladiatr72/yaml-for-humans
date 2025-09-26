#!/usr/bin/env python3
"""
Command-line interface for YAML for Humans.

Converts YAML or JSON input to human-friendly YAML output.
"""

import glob
import io
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol, TextIO

import yaml

from .document_processors import (
    process_items_array,
    process_json_lines,
    process_multi_document_yaml,
)
from .dumper import dumps, load_with_formatting

try:
    import click
except ImportError:
    click = None


DEFAULT_TIMEOUT_MS: int = 2000
DEFAULT_INDENT: int = 2
DEFAULT_PRESERVE_EMPTY_LINES: bool = True
DEFAULT_PRESERVE_COMMENTS: bool = True


@dataclass(frozen=True)
class ProcessingContext:
    """Immutable context for processing operations."""

    unsafe_inputs: bool = False
    preserve_empty_lines: bool = DEFAULT_PRESERVE_EMPTY_LINES
    preserve_comments: bool = DEFAULT_PRESERVE_COMMENTS

    def create_source_factory(self, base_info: dict) -> Callable[[], dict]:
        """Create source factory with counter for multi-document sources."""
        counter = [0]

        def factory():
            result = {**base_info}
            # For stdin, update position counter on each call
            if "stdin_position" in base_info:
                result["stdin_position"] = counter[0]
                counter[0] += 1
            return result

        return factory


class FilePathExpander:
    """Handles file path expansion with glob and directory support."""

    def expand_paths(self, inputs_str: str) -> list[str]:
        """Main entry point - expands comma-separated paths with glob and directory support."""
        raw_paths = [path.strip() for path in inputs_str.split(",")]
        expanded = []

        for path in raw_paths:
            if not path:
                continue
            expanded.extend(self._expand_single_path(path))

        return expanded

    def _expand_single_path(self, path: str) -> list[str]:
        """Expand a single path - handles directories, globs, and regular files."""
        if path.endswith(os.sep):
            return self._expand_directory(path)
        elif self._is_glob_pattern(path):
            return self._expand_glob(path)
        else:
            return self._expand_regular_file(path)

    def _expand_directory(self, dir_path: str) -> list[str]:
        """Expand directory to list of valid files."""
        dir_path = dir_path.rstrip(os.sep)
        expanded = []

        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for file_name in os.listdir(dir_path):
                full_path = os.path.join(dir_path, file_name)
                if os.path.isfile(full_path):
                    if _is_valid_file_type(full_path):
                        expanded.append(full_path)
                    else:
                        click.echo(
                            f"Skipping file with invalid format: {full_path}", err=True
                        )
        else:
            click.echo(f"Directory not found: {dir_path}", err=True)

        return expanded

    def _expand_glob(self, glob_pattern: str) -> list[str]:
        """Expand glob pattern to list of valid files."""
        expanded = []
        glob_matches = glob.glob(glob_pattern)

        if glob_matches:
            for match in sorted(glob_matches):
                if os.path.isfile(match):
                    if _is_valid_file_type(match):
                        expanded.append(match)
                    else:
                        click.echo(
                            f"Skipping file with invalid format: {match}", err=True
                        )
        else:
            click.echo(f"No files found matching pattern: {glob_pattern}", err=True)

        return expanded

    def _expand_regular_file(self, file_path: str) -> list[str]:
        """Handle regular file path."""
        if os.path.exists(file_path) and os.path.isfile(file_path):
            if _is_valid_file_type(file_path):
                return [file_path]
            else:
                click.echo(f"Skipping file with invalid format: {file_path}", err=True)
                return []
        else:
            click.echo(f"File not found: {file_path}", err=True)
            return []

    def _is_glob_pattern(self, path: str) -> bool:
        """Check if path contains glob pattern characters."""
        return any(char in path for char in ["*", "?", "["])


class FormatDetector:
    """Centralized format detection and processing."""

    def __init__(self, context: ProcessingContext):
        self.context = context

    def process_content(
        self, content: str, source_factory: Callable
    ) -> tuple[list[Any], list[dict]]:
        """Unified content processing with format detection."""
        if _looks_like_json(content):
            return self._process_json_content(content, source_factory)
        else:
            return self._process_yaml_content(content, source_factory)

    def _process_json_content(
        self, content: str, source_factory: Callable
    ) -> tuple[list[Any], list[dict]]:
        """Process JSON content with format-specific handling."""
        if _is_json_lines(content):
            return process_json_lines(content, source_factory)

        # This will raise json.JSONDecodeError if invalid, which should propagate up
        data = json.loads(content)
        if _has_items_array(data):
            return process_items_array(data, source_factory)

        return [data], [source_factory()]

    def _process_yaml_content(
        self, content: str, source_factory: Callable
    ) -> tuple[list[Any], list[dict]]:
        """Process YAML content with multi-document support."""
        if _is_multi_document_yaml(content):
            return process_multi_document_yaml(
                content,
                source_factory,
                unsafe=self.context.unsafe_inputs,
                preserve_empty_lines=self.context.preserve_empty_lines,
                _load_all_yaml_func=_load_all_yaml,
            )

        data = _load_yaml(
            content,
            unsafe=self.context.unsafe_inputs,
            preserve_empty_lines=self.context.preserve_empty_lines,
        )
        return [data], [source_factory()]


class InputProcessor:
    """Handles document processing from various input sources."""

    def __init__(self, context: ProcessingContext):
        self.context = context
        self.format_detector = FormatDetector(context)

    def process_files(self, inputs_str: str) -> tuple[list[Any], list[dict]]:
        """Process file inputs with path expansion and format detection."""
        expander = FilePathExpander()
        file_paths = expander.expand_paths(inputs_str)

        documents, sources = [], []
        for file_path in file_paths:
            docs, srcs = self._process_single_file(file_path)
            documents.extend(docs)
            sources.extend(srcs)

        return documents, sources

    def process_stdin(self, timeout: int) -> tuple[list[Any], list[dict]]:
        """Process stdin input with timeout and format detection."""
        input_text = _read_stdin_with_timeout(timeout).strip()

        if not input_text:
            raise ValueError("No input provided")

        # Create appropriate source factory for stdin
        # For multi-document cases, the processors will handle counter incrementation
        source_factory = self.context.create_source_factory({"stdin_position": 0})

        return self.format_detector.process_content(input_text, source_factory)

    def _process_single_file(self, file_path: str) -> tuple[list[Any], list[dict]]:
        """Process individual file with error handling."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                return [], []

            source_factory = self.context.create_source_factory(
                {"file_path": file_path}
            )
            return self.format_detector.process_content(content, source_factory)

        except FileNotFoundError:
            click.echo(f"Error: File not found: {file_path}", err=True)
            return [], []
        except json.JSONDecodeError as e:
            click.echo(f"Error: Failed to parse {file_path}: {e}", err=True)
            return [], []
        except yaml.YAMLError as e:
            click.echo(f"Error: Failed to parse {file_path}: {e}", err=True)
            return [], []
        except Exception as e:
            click.echo(f"Error: Failed to read {file_path}: {e}", err=True)
            return [], []


@dataclass(frozen=True)
class OutputContext:
    """Configuration for output operations."""

    indent: int = DEFAULT_INDENT
    preserve_empty_lines: bool = DEFAULT_PRESERVE_EMPTY_LINES
    preserve_comments: bool = DEFAULT_PRESERVE_COMMENTS
    auto_create_dirs: bool = False


class OutputStrategy(Protocol):
    """Strategy interface for different output modes."""

    def write_documents(
        self, documents: list[Any], sources: list[dict], context: OutputContext
    ) -> None:
        """Write documents using the specific output strategy."""
        ...


class DirectoryOutputWriter:
    """Handles writing multiple documents to directory with individual files."""

    def __init__(self, dir_path: Path):
        self.dir_path = dir_path
        self._filename_cache: set[str] = set()

    def write_documents(
        self, documents: list[Any], sources: list[dict], context: OutputContext
    ) -> None:
        """Write documents to individual files in directory."""
        self._ensure_directory_exists(context.auto_create_dirs)

        if len(documents) == 1:
            self._write_single_document(
                documents[0], sources[0] if sources else {}, context
            )
        else:
            self._write_multiple_documents(documents, sources, context)

    def _ensure_directory_exists(self, auto_create: bool) -> None:
        """Ensure target directory exists."""
        if not self.dir_path.exists():
            if auto_create:
                self.dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {self.dir_path}", file=sys.stderr)
            else:
                print(
                    f"Error: Directory does not exist: {self.dir_path}", file=sys.stderr
                )
                sys.exit(1)

    def _write_single_document(
        self, document: Any, source: dict, context: OutputContext
    ) -> None:
        """Write single document to file."""
        filename = self._generate_unique_filename(document, source)
        file_path = self.dir_path / filename
        self._write_yaml_file(file_path, document, context)

    def _write_multiple_documents(
        self, documents: list[Any], sources: list[dict], context: OutputContext
    ) -> None:
        """Write multiple documents with O(1) filename conflict resolution."""
        for i, doc in enumerate(documents):
            source = sources[i] if sources and i < len(sources) else {}
            filename = self._generate_unique_filename(doc, source, i)
            file_path = self.dir_path / filename
            self._write_yaml_file(file_path, doc, context)

    def _generate_unique_filename(
        self, document: Any, source: dict, index: int = 0
    ) -> str:
        """Generate unique filename avoiding O(n²) filesystem checks."""
        # Check if this is a Kubernetes manifest to enable prefix ordering
        is_k8s_manifest = isinstance(document, dict) and "kind" in document

        base_filename = _generate_k8s_filename(
            document,
            source_file=source.get("file_path"),
            stdin_position=source.get("stdin_position"),
            add_prefix=is_k8s_manifest,
        )

        # Use cache to avoid filesystem checks for known filenames
        if base_filename not in self._filename_cache:
            # Check if file actually exists on first encounter
            if not (self.dir_path / base_filename).exists():
                self._filename_cache.add(base_filename)
                return base_filename

        # Generate numbered variant
        counter = 1
        base_name = base_filename.replace(".yaml", "")
        while True:
            candidate = f"{base_name}-{counter}.yaml"
            if candidate not in self._filename_cache:
                # Double-check filesystem for safety
                if not (self.dir_path / candidate).exists():
                    self._filename_cache.add(candidate)
                    return candidate
            counter += 1

    def _write_yaml_file(
        self, file_path: Path, document: Any, context: OutputContext
    ) -> None:
        """Write single document to YAML file."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                dumps(
                    document,
                    indent=context.indent,
                    preserve_empty_lines=context.preserve_empty_lines,
                    preserve_comments=context.preserve_comments,
                )
            )


class FileOutputWriter:
    """Handles writing documents to single file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def write_documents(
        self, documents: list[Any], sources: list[dict], context: OutputContext
    ) -> None:
        """Write documents to single file."""
        self._ensure_parent_dirs_exist(context.auto_create_dirs)

        with open(self.file_path, "w", encoding="utf-8") as f:
            if len(documents) > 1:
                self._write_multi_document_yaml(f, documents, context)
            else:
                self._write_single_document_yaml(f, documents[0], context)

    def _ensure_parent_dirs_exist(self, auto_create: bool) -> None:
        """Ensure parent directories exist."""
        if auto_create and not self.file_path.parent.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Created parent directories for: {self.file_path}", file=sys.stderr)

    def _write_multi_document_yaml(
        self, file_handle: TextIO, documents: list[Any], context: OutputContext
    ) -> None:
        """Write multiple documents to single file."""
        from .multi_document import dumps_all

        file_handle.write(dumps_all(documents, indent=context.indent))

    def _write_single_document_yaml(
        self, file_handle: TextIO, document: Any, context: OutputContext
    ) -> None:
        """Write single document to file."""
        file_handle.write(
            dumps(
                document,
                indent=context.indent,
                preserve_empty_lines=context.preserve_empty_lines,
                preserve_comments=context.preserve_comments,
            )
        )


class OutputWriter:
    """Main output coordination class with strategy pattern."""

    @staticmethod
    def create_writer(output_path: str) -> OutputStrategy:
        """Factory method to create appropriate output strategy."""
        if output_path.endswith(os.sep):
            return DirectoryOutputWriter(Path(output_path.rstrip(os.sep)))
        else:
            return FileOutputWriter(Path(output_path))

    @staticmethod
    def write(
        documents: list[Any],
        sources: list[dict],
        output_path: str,
        indent: int = DEFAULT_INDENT,
        preserve_empty_lines: bool = DEFAULT_PRESERVE_EMPTY_LINES,
        preserve_comments: bool = DEFAULT_PRESERVE_COMMENTS,
        auto: bool = False,
    ) -> None:
        """Main entry point replacing _write_to_output."""
        context = OutputContext(
            indent=indent,
            preserve_empty_lines=preserve_empty_lines,
            preserve_comments=preserve_comments,
            auto_create_dirs=auto,
        )

        writer = OutputWriter.create_writer(output_path)
        writer.write_documents(documents, sources, context)


def _load_yaml(
    content: str, unsafe: bool = False, preserve_empty_lines: bool = False
) -> Any:
    """Load YAML content using safe or unsafe loader."""
    if preserve_empty_lines and not unsafe:
        # Use formatting-aware loader for empty line preservation
        # Note: unsafe mode not supported with formatting-aware loading
        return load_with_formatting(content)
    elif unsafe:
        return yaml.load(content, Loader=yaml.Loader)
    else:
        # Use key-preserving loader to prevent 'on'/'off'/'yes'/'no' -> boolean conversion
        from .dumper import _load_yaml_safe_keys

        return _load_yaml_safe_keys(content)


def _load_all_yaml(
    content: str, unsafe: bool = False, preserve_empty_lines: bool = False
) -> Iterator[Any]:
    """Load all YAML documents using safe or unsafe loader."""
    # Note: Empty line preservation not yet supported for multi-document YAML
    # TODO: Implement multi-document formatting-aware loading
    if unsafe:
        return yaml.load_all(content, Loader=yaml.Loader)
    else:
        return yaml.safe_load_all(content)


def _check_cli_dependencies() -> None:
    """Check if CLI dependencies are available."""
    if click is None:
        print("Error: CLI functionality requires the 'cli' extra.", file=sys.stderr)
        print("Install with: uv add yaml-for-humans[cli]", file=sys.stderr)
        print("Or using pip: pip install yaml-for-humans[cli]", file=sys.stderr)
        sys.exit(1)


def _read_stdin_with_timeout(timeout_ms: int = DEFAULT_TIMEOUT_MS) -> str:
    """
    Read from stdin with a timeout.

    Args:
        timeout_ms: Timeout in milliseconds (default: 50ms)

    Returns:
        str: Input text from stdin

    Raises:
        TimeoutError: If no input is received within the timeout period
    """
    import select

    timeout_sec = timeout_ms / 1000.0

    # Use select() for efficient I/O multiplexing instead of threads
    # Fall back to threading if stdin doesn't have a file descriptor (e.g., in tests)
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)

        if not ready:
            raise TimeoutError(f"No input received within {timeout_ms}ms")

        return sys.stdin.read()
    except (io.UnsupportedOperation, AttributeError):
        # Fallback to thread-based approach for environments without real stdin
        import threading

        input_data = []
        exception_data = []

        def read_input():
            try:
                data = sys.stdin.read()
                input_data.append(data)
            except Exception as e:
                exception_data.append(e)

        thread = threading.Thread(target=read_input)
        thread.daemon = True
        thread.start()
        thread.join(timeout_sec)

        if thread.is_alive():
            raise TimeoutError(f"No input received within {timeout_ms}ms")

        if exception_data:
            raise exception_data[0]

        if not input_data:
            raise TimeoutError(f"No input received within {timeout_ms}ms")

        return input_data[0]


def _process_input_source(
    inputs: str | None, processor: InputProcessor, timeout: int
) -> tuple[list[Any], list[dict]]:
    """
    Process input from files or stdin.

    Returns:
        Tuple of (documents, document_sources)

    Raises:
        Various exceptions that should be handled by caller
    """
    if inputs:
        return processor.process_files(inputs)
    else:
        # Read from stdin with timeout handling
        try:
            return processor.process_stdin(timeout)
        except TimeoutError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError:
            # Re-raise to be caught by outer exception handler
            raise
        except yaml.YAMLError:
            # Re-raise to be caught by outer exception handler
            raise
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def _handle_output_generation(
    documents: list[Any],
    document_sources: list[dict],
    output: str | None,
    auto: bool,
    indent: int,
    preserve_empty_lines: bool,
    preserve_comments: bool = DEFAULT_PRESERVE_COMMENTS,
) -> None:
    """
    Handle output generation - either to file/directory or stdout.
    """
    if output:
        # Write to file/directory
        OutputWriter.write(
            documents=documents,
            sources=document_sources,
            output_path=output,
            indent=indent,
            preserve_empty_lines=preserve_empty_lines,
            preserve_comments=preserve_comments,
            auto=auto,
        )
    else:
        # Write to stdout (existing behavior)
        if len(documents) > 1:
            from .multi_document import dumps_all

            output_str = dumps_all(documents, indent=indent)
        else:
            output_str = dumps(
                documents[0],
                indent=indent,
                preserve_empty_lines=preserve_empty_lines,
                preserve_comments=preserve_comments,
            )
        print(output_str, end="")


def _huml_main(
    indent: int = DEFAULT_INDENT,
    timeout: int = DEFAULT_TIMEOUT_MS,
    inputs: str | None = None,
    output: str | None = None,
    auto: bool = False,
    unsafe_inputs: bool = False,
    preserve_empty_lines: bool = DEFAULT_PRESERVE_EMPTY_LINES,
    preserve_comments: bool = DEFAULT_PRESERVE_COMMENTS,
) -> None:
    """
    Convert YAML or JSON input to human-friendly YAML.

    Reads from stdin and writes to stdout.

    Security:
        By default, uses yaml.SafeLoader for parsing YAML input.
        Use --unsafe-inputs to enable yaml.Loader which allows
        arbitrary Python object instantiation (use with caution).
    """
    _check_cli_dependencies()

    try:
        # Create processing context and processor
        context = ProcessingContext(
            unsafe_inputs=unsafe_inputs,
            preserve_empty_lines=preserve_empty_lines,
            preserve_comments=preserve_comments,
        )
        processor = InputProcessor(context)

        # Process input from files or stdin
        documents, document_sources = _process_input_source(inputs, processor, timeout)

        # Handle case where no documents were processed
        if len(documents) == 0:
            if inputs:
                # When using --inputs flag, we might have no valid files
                # This is not necessarily an error, just no output
                return
            else:
                print("Error: No documents to process", file=sys.stderr)
                sys.exit(1)

        # Handle output generation
        _handle_output_generation(
            documents,
            document_sources,
            output,
            auto,
            indent,
            preserve_empty_lines,
            preserve_comments,
        )

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML input - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _looks_like_json(text: str) -> bool:
    """Simple heuristic to detect JSON input."""
    text = text.strip()
    return (text.startswith("{") and text.endswith("}")) or (
        text.startswith("[") and text.endswith("]")
    )


def _is_multi_document_yaml(text: str) -> bool:
    """Check if text contains multi-document YAML."""
    # Look for document separator at start of line
    lines = text.split("\n")
    # Multi-document if we have at least one separator
    # Or if we have multiple separators anywhere in the text
    separator_count = sum(1 for line in lines if line.strip() == "---")
    return separator_count > 0


def _is_json_lines(text: str) -> bool:
    """Check if text is in JSON Lines format (one JSON object per line)."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Must have more than one line with content
    if len(lines) <= 1:
        return False

    # Each non-empty line should look like JSON
    return all(_looks_like_json(line) for line in lines)


def _has_items_array(data: Any) -> bool:
    """Check if JSON data has an 'items' array that should be processed as separate documents."""
    if not isinstance(data, dict):
        return False

    # Check if there's an 'items' key with an array value
    items = data.get("items")
    if not isinstance(items, list):
        return False

    # Only treat as multi-document if items contains objects (not just primitives)
    if not items:
        return False

    # At least one item should be a dict/object to warrant document separation
    return any(isinstance(item, dict) for item in items)


def _generate_k8s_filename(
    document, source_file=None, stdin_position=None, add_prefix=False
):
    """Generate a filename for a Kubernetes manifest document.

    Args:
        document: Kubernetes resource dictionary
        source_file: Original source file path for fallback naming
        stdin_position: Position when reading from stdin
        add_prefix: If True, prepend 2-digit resource ordering prefix

    Returns:
        str: Generated filename with optional prefix
    """
    if not isinstance(document, dict):
        # Fallback naming logic
        if source_file:
            # Use original source filename without extension
            import os

            base_name = os.path.splitext(os.path.basename(source_file))[0]
            return f"{base_name}.yaml"
        elif stdin_position is not None:
            return f"stdin-{stdin_position}.yaml"
        else:
            return "document.yaml"

    # Extract Kubernetes manifest fields
    kind = document.get("kind", "")
    doc_type = document.get("type", "")
    metadata = document.get("metadata", {})
    name = metadata.get("name", "") if isinstance(metadata, dict) else ""

    # Build filename parts
    parts = [value.lower() for value in [kind, doc_type, name] if value]

    # If we have no identifying information, use fallback naming
    if not parts:
        if source_file:
            # Use original source filename without extension
            import os

            base_name = os.path.splitext(os.path.basename(source_file))[0]
            return f"{base_name}.yaml"
        elif stdin_position is not None:
            return f"stdin-{stdin_position}.yaml"
        else:
            return "document.yaml"

    base_filename = f"{'-'.join(parts)}.yaml"

    # Add resource ordering prefix if requested
    if add_prefix and kind:
        from .multi_document import get_k8s_resource_prefix

        prefix = get_k8s_resource_prefix(document)
        return f"{prefix}-{base_filename}"

    return base_filename


def _is_valid_file_type(file_path):
    """Check if file has a valid JSON or YAML extension, or try to detect format from content."""
    # Check common extensions first
    if file_path.lower().endswith((".json", ".yaml", ".yml", ".jsonl")):
        # Still need to check if file is empty or readable
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample = f.read(1024).strip()
                if not sample:
                    return False
            return True
        except (IOError, UnicodeDecodeError, PermissionError):
            return False

    # For files without clear extensions, try to peek at content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read first few lines to detect format
            sample = f.read(1024).strip()
            if not sample:
                return False
            # Simple heuristics for format detection
            return _looks_like_json(sample) or _looks_like_yaml(sample)
    except (IOError, UnicodeDecodeError, PermissionError):
        return False


def _looks_like_yaml(text):
    """Simple heuristic to detect YAML input."""
    text = text.strip()
    # Common YAML patterns
    yaml_indicators = [
        ":",  # key-value pairs
        "- ",  # list items
        "---",  # document separator
        "...",  # document end
    ]
    return any(
        indicator in text for indicator in yaml_indicators
    ) and not _looks_like_json(text)


def _write_to_output(
    documents,
    output_path,
    auto=False,
    indent=DEFAULT_INDENT,
    document_sources=None,
    preserve_empty_lines=DEFAULT_PRESERVE_EMPTY_LINES,
    preserve_comments=DEFAULT_PRESERVE_COMMENTS,
):
    """Write documents to the specified output path using OutputWriter architecture."""
    OutputWriter.write(
        documents=documents,
        sources=document_sources or [],
        output_path=output_path,
        indent=indent,
        preserve_empty_lines=preserve_empty_lines,
        preserve_comments=preserve_comments,
        auto=auto,
    )


def huml():
    """CLI entry point - uses click for argument parsing if available."""
    _check_cli_dependencies()

    # Use click for proper CLI argument parsing
    @click.command()
    @click.option(
        "--indent",
        default=DEFAULT_INDENT,
        type=int,
        help=f"Indentation level (default: {DEFAULT_INDENT})",
    )
    @click.option(
        "--timeout",
        "-t",
        default=DEFAULT_TIMEOUT_MS,
        type=int,
        envvar=["HUML_STDIN_TIMEOUT", "HUML_TIMEOUT_STDIN"],
        help=f"Stdin timeout in milliseconds (default: {DEFAULT_TIMEOUT_MS})",
    )
    @click.option(
        "--inputs",
        "-i",
        type=str,
        help="Comma-delimited list of JSON/YAML file paths to process",
    )
    @click.option(
        "--output",
        "-o",
        type=str,
        help="Output file or directory path. If ends with os.sep, treated as directory.",
    )
    @click.option(
        "--auto",
        is_flag=True,
        help="Automatically create output directories if they don't exist",
    )
    @click.option(
        "--unsafe-inputs",
        "-u",
        is_flag=True,
        help="Use unsafe YAML loader (yaml.Loader) instead of safe loader (default: false, uses yaml.SafeLoader)",
    )
    @click.option(
        "--no-preserve",
        "-P",
        is_flag=True,
        default=False,
        help="Disable preservation of empty lines and comments from original YAML",
    )
    @click.version_option()
    def cli_main(indent, timeout, inputs, output, auto, unsafe_inputs, no_preserve):
        """
        Convert YAML or JSON input to human-friendly YAML.

        Reads from stdin and writes to stdout.

        \b
        Security:
          By default, uses yaml.SafeLoader for parsing YAML input.
          Use --unsafe-inputs to enable yaml.Loader which allows
          arbitrary Python object instantiation (use with caution).
        """
        _huml_main(
            indent,
            timeout,
            inputs,
            output,
            auto,
            unsafe_inputs,
            not no_preserve,
            not no_preserve,
        )

    cli_main()


if __name__ == "__main__":
    huml()
