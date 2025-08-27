#!/usr/bin/env python3
"""
Command-line interface for YAML for Humans.

Converts YAML or JSON input to human-friendly YAML output.
"""

import sys
import json
import yaml
from .dumper import dumps

try:
    import click
except ImportError:
    click = None


def _check_cli_dependencies():
    """Check if CLI dependencies are available."""
    if click is None:
        print("Error: CLI functionality requires the 'cli' extra.", file=sys.stderr)
        print("Install with: uv add yaml-for-humans[cli]", file=sys.stderr)
        print("Or using pip: pip install yaml-for-humans[cli]", file=sys.stderr)
        sys.exit(1)


def _read_stdin_with_timeout(timeout_ms=50):
    """
    Read from stdin with a timeout.

    Args:
        timeout_ms: Timeout in milliseconds (default: 50ms)

    Returns:
        str: Input text from stdin

    Raises:
        TimeoutError: If no input is received within the timeout period
    """
    import threading

    timeout_sec = timeout_ms / 1000.0

    input_data = []
    exception_data = []

    def read_input():
        try:
            data = sys.stdin.read()
            input_data.append(data)
        except Exception as e:
            exception_data.append(e)

    # Start reading in a separate thread
    thread = threading.Thread(target=read_input)
    thread.daemon = True
    thread.start()
    thread.join(timeout_sec)

    if thread.is_alive():
        # Thread is still running, meaning no input was received
        raise TimeoutError(f"No input received within {timeout_ms}ms")

    if exception_data:
        raise exception_data[0]

    if not input_data:
        raise TimeoutError(f"No input received within {timeout_ms}ms")

    return input_data[0]


def _huml_main(
    indent=2,
    format="auto",
    timeout=50,
    inputs=None,
    output=None,
    auto=False,
):
    """
    Convert YAML or JSON input to human-friendly YAML.

    Reads from stdin and writes to stdout.

    Examples:
        cat config.yaml | huml
        echo '{"name": "web", "ports": [80, 443]}' | huml -f json
        kubectl get deployment -o yaml | huml
    """
    _check_cli_dependencies()

    try:
        documents = []
        document_sources = []  # Track source info for each document

        # Handle --inputs flag (process files)
        if inputs:
            file_paths = [path.strip() for path in inputs.split(",")]

            for file_path in file_paths:
                if not file_path:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read().strip()

                    if not file_content:
                        continue

                    # Determine file format from extension or content
                    if file_path.lower().endswith(".json"):
                        # Check for JSON Lines format (multiple JSON objects, one per line)
                        if _is_json_lines(file_content):
                            for line_num, line in enumerate(
                                file_content.split("\n"), 1
                            ):
                                line = line.strip()
                                if line:
                                    try:
                                        data = json.loads(line)
                                        documents.append(data)
                                        document_sources.append(
                                            {"file_path": file_path}
                                        )
                                    except json.JSONDecodeError as e:
                                        print(
                                            f"Error: Invalid JSON on line {line_num} in {file_path}: {e}",
                                            file=sys.stderr,
                                        )
                                        sys.exit(1)
                            continue
                        else:
                            data = json.loads(file_content)
                            # Check if JSON has an 'items' array that should be processed as separate documents
                            if _has_items_array(data):
                                items = data["items"]
                                # Add each item as a separate document
                                documents.extend(items)
                                document_sources.extend(
                                    [{"file_path": file_path}] * len(items)
                                )
                                continue
                    elif file_path.lower().endswith((".yaml", ".yml")):
                        # Always check for multi-document YAML (detect automatically)
                        if _is_multi_document_yaml(file_content):
                            docs = list(yaml.safe_load_all(file_content))
                            # Filter out None/empty documents
                            docs = [doc for doc in docs if doc is not None]
                            documents.extend(docs)
                            document_sources.extend(
                                [{"file_path": file_path}] * len(docs)
                            )
                            continue
                        else:
                            data = yaml.safe_load(file_content)
                    else:
                        # Auto-detect format for files without clear extensions
                        if _looks_like_json(file_content):
                            if _is_json_lines(file_content):
                                for line_num, line in enumerate(
                                    file_content.split("\n"), 1
                                ):
                                    line = line.strip()
                                    if line:
                                        try:
                                            data = json.loads(line)
                                            documents.append(data)
                                            document_sources.append(
                                                {"file_path": file_path}
                                            )
                                        except json.JSONDecodeError as e:
                                            print(
                                                f"Error: Invalid JSON on line {line_num} in {file_path}: {e}",
                                                file=sys.stderr,
                                            )
                                            sys.exit(1)
                                continue
                            else:
                                data = json.loads(file_content)
                                # Check if JSON has an 'items' array that should be processed as separate documents
                                if _has_items_array(data):
                                    items = data["items"]
                                    # Add each item as a separate document
                                    documents.extend(items)
                                    document_sources.extend(
                                        [{"file_path": file_path}] * len(items)
                                    )
                                    continue
                        else:
                            if _is_multi_document_yaml(file_content):
                                docs = list(yaml.safe_load_all(file_content))
                                docs = [doc for doc in docs if doc is not None]
                                documents.extend(docs)
                                document_sources.extend(
                                    [{"file_path": file_path}] * len(docs)
                                )
                                continue
                            else:
                                data = yaml.safe_load(file_content)

                    documents.append(data)
                    document_sources.append({"file_path": file_path})

                except FileNotFoundError:
                    print(f"Error: File not found: {file_path}", file=sys.stderr)
                    sys.exit(1)
                except (json.JSONDecodeError, yaml.YAMLError) as e:
                    print(f"Error: Failed to parse {file_path}: {e}", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"Error: Failed to read {file_path}: {e}", file=sys.stderr)
                    sys.exit(1)

        else:
            # Read input from stdin with timeout
            try:
                input_text = _read_stdin_with_timeout(timeout).strip()
            except TimeoutError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

            if not input_text:
                print("Error: No input provided", file=sys.stderr)
                sys.exit(1)

            # Parse input based on format with auto-detection
            if format == "json" or (format == "auto" and _looks_like_json(input_text)):
                # Check for JSON Lines format (multiple JSON objects, one per line)
                if _is_json_lines(input_text):
                    for line_num, line in enumerate(input_text.split("\n"), 1):
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                documents.append(data)
                                document_sources.append(
                                    {"stdin_position": len(documents) - 1}
                                )
                            except json.JSONDecodeError as e:
                                print(
                                    f"Error: Invalid JSON on line {line_num}: {e}",
                                    file=sys.stderr,
                                )
                                sys.exit(1)
                else:
                    data = json.loads(input_text)
                    # Check if JSON has an 'items' array that should be processed as separate documents
                    if _has_items_array(data):
                        items = data["items"]
                        # Add each item as a separate document
                        documents.extend(items)
                        document_sources.extend(
                            [{"stdin_position": i} for i in range(len(items))]
                        )
                    else:
                        documents.append(data)
                        document_sources.append({"stdin_position": 0})
            elif format == "yaml" or format == "auto":
                # Auto-detect multi-document YAML (like file processing does)
                if _is_multi_document_yaml(input_text):
                    docs = list(yaml.safe_load_all(input_text))
                    # Filter out None/empty documents
                    docs = [doc for doc in docs if doc is not None]
                    documents.extend(docs)
                    document_sources.extend(
                        [{"stdin_position": i} for i in range(len(docs))]
                    )
                else:
                    data = yaml.safe_load(input_text)
                    documents.append(data)
                    document_sources.append({"stdin_position": 0})
            else:
                print("Error: Unable to determine input format", file=sys.stderr)
                sys.exit(1)

        # Handle output
        if len(documents) == 0:
            print("Error: No documents to process", file=sys.stderr)
            sys.exit(1)

        if output:
            # Write to file/directory
            _write_to_output(documents, output, auto, indent, document_sources)
        else:
            # Write to stdout (existing behavior)
            if len(documents) > 1:
                from .multi_document import dumps_all

                output_str = dumps_all(documents, indent=indent)
            else:
                output_str = dumps(documents[0], indent=indent)

            print(output_str, end="")

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML input - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _looks_like_json(text):
    """Simple heuristic to detect JSON input."""
    text = text.strip()
    return (text.startswith("{") and text.endswith("}")) or (
        text.startswith("[") and text.endswith("]")
    )


def _is_multi_document_yaml(text):
    """Check if text contains multi-document YAML."""
    # Look for document separator at start of line
    lines = text.split("\n")
    separator_count = 0
    for line in lines:
        if line.strip() == "---":
            separator_count += 1

    # Multi-document if we have at least one separator
    # Or if we have multiple separators anywhere in the text
    return separator_count > 0


def _is_json_lines(text):
    """Check if text is in JSON Lines format (one JSON object per line)."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Must have more than one line with content
    if len(lines) <= 1:
        return False

    # Each non-empty line should look like JSON
    for line in lines:
        if not (_looks_like_json(line)):
            return False

    return True


def _has_items_array(data):
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


def _generate_k8s_filename(document, source_file=None, stdin_position=None):
    """Generate a filename for a Kubernetes manifest document."""
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
    parts = []
    if kind:
        parts.append(kind.lower())
    if doc_type:
        parts.append(doc_type.lower())
    if name:
        parts.append(name.lower())

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

    return f"{'-'.join(parts)}.yaml"


def _write_to_output(
    documents, output_path, auto=False, indent=2, document_sources=None
):
    """Write documents to the specified output path."""
    import os
    from pathlib import Path

    # Determine if output is a directory
    is_directory = output_path.endswith(os.sep)

    if is_directory:
        # Handle directory output
        dir_path = Path(output_path.rstrip(os.sep))

        # Check if directory exists
        if not dir_path.exists():
            if auto:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}", file=sys.stderr)
            else:
                print(f"Error: Directory does not exist: {dir_path}", file=sys.stderr)
                sys.exit(1)

        # Write each document to its own file
        if len(documents) == 1:
            # Single document
            source_info = document_sources[0] if document_sources else {}
            filename = _generate_k8s_filename(
                documents[0],
                source_file=source_info.get("file_path"),
                stdin_position=source_info.get("stdin_position"),
            )
            file_path = dir_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(dumps(documents[0], indent=indent))
        else:
            # Multiple documents - each gets its own file
            for i, doc in enumerate(documents):
                source_info = (
                    document_sources[i]
                    if document_sources and i < len(document_sources)
                    else {}
                )
                filename = _generate_k8s_filename(
                    doc,
                    source_file=source_info.get("file_path"),
                    stdin_position=source_info.get("stdin_position"),
                )
                # If filename conflicts, add index
                file_path = dir_path / filename
                counter = 1
                while file_path.exists():
                    base_name = filename.replace(".yaml", "")
                    file_path = dir_path / f"{base_name}-{counter}.yaml"
                    counter += 1

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(dumps(doc, indent=indent))
    else:
        # Handle single file output
        file_path = Path(output_path)

        # Create parent directories if needed
        if auto and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Created parent directories for: {file_path}", file=sys.stderr)

        # Write all documents to single file
        with open(file_path, "w", encoding="utf-8") as f:
            if len(documents) > 1:
                from .multi_document import dumps_all

                f.write(dumps_all(documents, indent=indent))
            else:
                f.write(dumps(documents[0], indent=indent))


def huml():
    """CLI entry point - uses click for argument parsing if available."""
    _check_cli_dependencies()

    # Use click for proper CLI argument parsing
    @click.command()
    @click.option(
        "--indent", default=2, type=int, help="Indentation level (default: 2)"
    )
    @click.option(
        "--format",
        "-f",
        type=click.Choice(["yaml", "json", "auto"]),
        default="auto",
        help="Input format (default: auto-detect)",
    )
    @click.option(
        "--timeout",
        "-t",
        default=50,
        type=int,
        help="Stdin timeout in milliseconds (default: 50)",
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
    @click.version_option()
    def cli_main(indent, format, timeout, inputs, output, auto):
        """
        Convert YAML or JSON input to human-friendly YAML.

        Reads from stdin and writes to stdout.

        Examples:
            cat config.yaml | huml
            echo '{"name": "web", "ports": [80, 443]}' | huml -f json
            kubectl get deployment -o yaml | huml
        """
        _huml_main(indent, format, timeout, inputs, output, auto)

    cli_main()


if __name__ == "__main__":
    huml()
