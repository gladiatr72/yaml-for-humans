"""
Type stubs for emitter module.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    IO,
    TextIO,
    Tuple,
)
from typing_extensions import TypeAlias
import yaml
from yaml.emitter import Emitter

# Type aliases for common YAML types
YAMLObject: TypeAlias = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
StreamType: TypeAlias = Union[IO[str], TextIO]

class HumanFriendlyEmitter(Emitter):
    """
    Custom YAML emitter that produces human-friendly sequence formatting.
    """

    def __init__(
        self,
        stream: StreamType,
        canonical: Optional[bool] = ...,
        indent: Optional[int] = ...,
        width: Optional[int] = ...,
        allow_unicode: Optional[bool] = ...,
        line_break: Optional[str] = ...,
    ) -> None: ...
    def expect_block_sequence(self) -> None:
        """Override to force indented sequences instead of indentless ones."""
        ...

    def expect_block_sequence_item(self, first: bool = ...) -> None:
        """Handle sequence items with intelligent formatting."""
        ...

    def expect_scalar(self) -> None:
        """Handle scalar values with proper sequence-aware indentation."""
        ...

    def expect_block_mapping(self) -> None:
        """Handle mappings with proper sequence context awareness."""
        ...

    def expect_block_mapping_simple_value(self) -> None:
        """Handle mapping values using default behavior for correct empty dict handling."""
        ...

class HumanFriendlyDumper(
    HumanFriendlyEmitter,
    yaml.serializer.Serializer,
    yaml.representer.Representer,
    yaml.resolver.Resolver,
):
    """
    Complete YAML dumper with human-friendly formatting and priority key ordering.
    """

    PRIORITY_KEYS: List[str]

    def __init__(
        self,
        stream: StreamType,
        default_style: Optional[str] = ...,
        default_flow_style: Optional[bool] = ...,
        canonical: Optional[bool] = ...,
        indent: Optional[int] = ...,
        width: Optional[int] = ...,
        allow_unicode: Optional[bool] = ...,
        line_break: Optional[str] = ...,
        encoding: Optional[str] = ...,
        explicit_start: Optional[bool] = ...,
        explicit_end: Optional[bool] = ...,
        version: Optional[Tuple[int, int]] = ...,
        tags: Optional[Dict[str, str]] = ...,
        sort_keys: Optional[bool] = ...,
    ) -> None: ...
    def represent_mapping(
        self,
        tag: str,
        mapping: Any,
        flow_style: Optional[bool] = ...,
    ) -> yaml.MappingNode: ...
