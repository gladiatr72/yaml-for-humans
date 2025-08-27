"""
Type stubs for CLI module.
"""

from typing import Literal

def huml(
    indent: int = ...,
    format: Literal["yaml", "json", "auto"] = ...,
) -> None:
    """
    Convert YAML or JSON input to human-friendly YAML.

    Reads from stdin and writes to stdout.

    Args:
        indent: Indentation level (default: 2)
        format: Input format (default: auto-detect)
    """
    ...

def _looks_like_json(text: str) -> bool:
    """Simple heuristic to detect JSON input."""
    ...
