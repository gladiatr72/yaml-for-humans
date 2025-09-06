"""
Document processing functions for YAML for Humans.

This module consolidates duplicate document processing logic that was
previously scattered across the CLI module in multiple locations.
"""

import json
import sys
from typing import List, Dict, Any, Callable


def process_json_lines(
    content: str, source_info_factory: Callable[[], Dict[str, Any]]
) -> tuple[List[Any], List[Dict[str, Any]]]:
    """
    Process JSON Lines format content (one JSON object per line).

    Args:
        content: The JSON Lines content to process
        source_info_factory: Function that creates source info for each document

    Returns:
        Tuple of (documents, source_info_list)

    Raises:
        SystemExit: If JSON parsing fails
    """
    documents = []
    document_sources = []

    for line_num, line in enumerate(content.split("\n"), 1):
        line = line.strip()
        if line:
            try:
                data = json.loads(line)
                documents.append(data)
                document_sources.append(source_info_factory())
            except json.JSONDecodeError as e:
                source_info = source_info_factory()
                if "file_path" in source_info:
                    print(
                        f"Error: Invalid JSON on line {line_num} in {source_info['file_path']}: {e}",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"Error: Invalid JSON on line {line_num}: {e}",
                        file=sys.stderr,
                    )
                sys.exit(1)

    return documents, document_sources


def process_multi_document_yaml(
    content: str,
    source_info_factory: Callable[[], Dict[str, Any]],
    unsafe: bool = False,
    preserve_empty_lines: bool = False,
    _load_all_yaml_func: Callable = None,
) -> tuple[List[Any], List[Dict[str, Any]]]:
    """
    Process multi-document YAML content.

    Args:
        content: The multi-document YAML content to process
        source_info_factory: Function that creates source info for each document
        unsafe: Whether to use unsafe YAML loading
        preserve_empty_lines: Whether to preserve empty lines in YAML
        _load_all_yaml_func: Function to load all YAML documents (injected for testing)

    Returns:
        Tuple of (documents, source_info_list)
    """
    if _load_all_yaml_func is None:
        from .cli import _load_all_yaml

        _load_all_yaml_func = _load_all_yaml

    docs = list(
        _load_all_yaml_func(
            content,
            unsafe=unsafe,
            preserve_empty_lines=preserve_empty_lines,
        )
    )

    # Filter out None/empty documents
    docs = [doc for doc in docs if doc is not None]
    document_sources = [source_info_factory() for _ in docs]

    return docs, document_sources


def process_items_array(
    data: Dict[str, Any], source_info_factory: Callable[[], Dict[str, Any]]
) -> tuple[List[Any], List[Dict[str, Any]]]:
    """
    Process JSON data with an 'items' array, treating each item as a separate document.

    Args:
        data: JSON data containing an 'items' array
        source_info_factory: Function that creates source info for each document

    Returns:
        Tuple of (documents, source_info_list) where documents is the items array
    """
    items = data["items"]
    document_sources = [source_info_factory() for _ in items]

    return items, document_sources
