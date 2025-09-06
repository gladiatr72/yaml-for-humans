"""
Type stubs for formatting_aware module.
"""

from typing import Any, Dict, List, Optional, Union, IO, TextIO
import yaml
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.resolver import Resolver

class FormattingMetadata:
    """Stores formatting information for YAML nodes."""

    empty_lines_before: int
    empty_lines_after: int

    def __init__(
        self, empty_lines_before: int = ..., empty_lines_after: int = ...
    ) -> None: ...
    def __repr__(self) -> str: ...

class FormattingAwareComposer(Composer):
    """Composer that captures empty line information in nodes."""

    def compose_mapping_node(self, anchor: Optional[str]) -> yaml.MappingNode: ...  # type: ignore[override]
    def compose_sequence_node(self, anchor: Optional[str]) -> yaml.SequenceNode: ...  # type: ignore[override]

class FormattingAwareConstructor(SafeConstructor):
    """Constructor that creates FormattingAware containers."""

    def construct_mapping(  # type: ignore[override]
        self, node: yaml.MappingNode, deep: bool = ...
    ) -> "FormattingAwareDict": ...
    def construct_sequence(
        self, node: yaml.SequenceNode, deep: bool = ...
    ) -> "FormattingAwareList": ...

class FormattingAwareDict(Dict[str, Any]):
    """Dictionary that preserves formatting metadata."""

    _formatting_metadata: Optional[FormattingMetadata]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class FormattingAwareList(List[Any]):
    """List that preserves formatting metadata."""

    _formatting_metadata: Optional[FormattingMetadata]

    def __init__(self, *args: Any) -> None: ...

class FormattingAwareLoader(
    FormattingAwareConstructor,
    FormattingAwareComposer,
    yaml.loader.SafeLoader,
    Resolver,
):
    """YAML loader that captures formatting metadata."""

    def __init__(self, stream: Union[str, bytes, IO[str], IO[bytes]]) -> None: ...
