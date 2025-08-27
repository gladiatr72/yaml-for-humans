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
        **kwargs: Additional arguments passed to HumanFriendlyDumper
    """
    ...

def dumps(
    data: YAMLObject,
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
        **kwargs: Additional arguments passed to HumanFriendlyDumper

    Returns:
        YAML representation of the data
    """
    ...
