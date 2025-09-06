"""
Type stubs for formatting_emitter module.
"""

from typing import Any, Dict, List, Optional, Union, IO, TextIO, Tuple
import yaml
from .emitter import HumanFriendlyEmitter

class FormattingAwareEmitter(HumanFriendlyEmitter):
    """
    Emitter that uses the HumanFriendlyEmitter as base.

    The actual empty line logic is handled by the FormattingAwareDumper's
    representer which injects empty line markers.
    """

    preserve_empty_lines: bool

    def __init__(
        self,
        stream: Union[IO[str], TextIO],
        canonical: Optional[bool] = ...,
        indent: Optional[int] = ...,
        width: Optional[int] = ...,
        allow_unicode: Optional[bool] = ...,
        line_break: Optional[str] = ...,
        preserve_empty_lines: bool = ...,
    ) -> None: ...

class FormattingAwareDumper(
    FormattingAwareEmitter,
    yaml.serializer.Serializer,
    yaml.representer.Representer,
    yaml.resolver.Resolver,
):
    """
    Complete YAML dumper with empty line preservation.

    Combines FormattingAwareEmitter with the existing HumanFriendlyDumper
    functionality for priority key ordering and multiline string formatting.
    """

    PRIORITY_KEYS: List[str]
    preserve_empty_lines: bool

    def __init__(
        self,
        stream: Union[IO[str], TextIO],
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
        preserve_empty_lines: bool = ...,
    ) -> None: ...
    def represent_mapping(
        self,
        tag: str,
        mapping: Any,
        flow_style: Optional[bool] = ...,
    ) -> yaml.MappingNode: ...
    def represent_formatting_aware_dict(
        self,
        dumper: "FormattingAwareDumper",
        data: Any,
    ) -> yaml.MappingNode: ...
    def represent_formatting_aware_list(
        self,
        dumper: "FormattingAwareDumper",
        data: Any,
    ) -> yaml.SequenceNode: ...
