"""
Type stubs for document_processors module.
"""

from typing import Any, Dict, List, Callable, Optional, Tuple

def process_json_lines(
    content: str, source_info_factory: Callable[[], Dict[str, Any]]
) -> Tuple[List[Any], List[Dict[str, Any]]]:
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
    ...

def process_multi_document_yaml(
    content: str,
    source_info_factory: Callable[[], Dict[str, Any]],
    unsafe: bool = ...,
    preserve_empty_lines: bool = ...,
    _load_all_yaml_func: Optional[Callable[..., Any]] = ...,
) -> Tuple[List[Any], List[Dict[str, Any]]]:
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
    ...

def process_items_array(
    data: Dict[str, Any], source_info_factory: Callable[[], Dict[str, Any]]
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """
    Process JSON data with an 'items' array, treating each item as a separate document.

    Args:
        data: JSON data containing an 'items' array
        source_info_factory: Function that creates source info for each document

    Returns:
        Tuple of (documents, source_info_list) where documents is the items array
    """
    ...
