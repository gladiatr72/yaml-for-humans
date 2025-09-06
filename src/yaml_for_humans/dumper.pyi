"""
Type stubs for dumper module.
"""

from typing import Any, Union, IO, TextIO, Optional
from typing_extensions import TypeAlias

# Type aliases
YAMLObject: TypeAlias = Union[dict[str, Any], list[Any], str, int, float, bool, None]
StreamType: TypeAlias = Union[IO[str], TextIO]

def dump(
    data: YAMLObject,
    stream: StreamType,
    preserve_empty_lines: bool = ...,
    *,
    Dumper: Optional[type] = ...,
    default_flow_style: Optional[bool] = ...,
    indent: Optional[int] = ...,
    sort_keys: Optional[bool] = ...,
    **kwargs: Any,
) -> None:
    """
    Serialize Python object to YAML with human-friendly formatting.

    Args:
        data: Python object to serialize
        stream: File-like object to write to
        preserve_empty_lines: If True, preserve empty lines from FormattingAware objects
        **kwargs: Additional arguments passed to the dumper
    """
    ...

def dumps(
    data: YAMLObject,
    preserve_empty_lines: bool = ...,
    *,
    Dumper: Optional[type] = ...,
    default_flow_style: Optional[bool] = ...,
    indent: Optional[int] = ...,
    sort_keys: Optional[bool] = ...,
    **kwargs: Any,
) -> str:
    """
    Serialize Python object to YAML string with human-friendly formatting.

    Args:
        data: Python object to serialize
        preserve_empty_lines: If True, preserve empty lines from FormattingAware objects
        **kwargs: Additional arguments passed to the dumper

    Returns:
        YAML representation of the data
    """
    ...

def load_with_formatting(stream: Union[str, StreamType]) -> Any:
    """
    Load YAML with formatting metadata preservation.

    Args:
        stream: Input stream, file path string, or YAML string

    Returns:
        Python object with formatting metadata attached
    """
    ...
