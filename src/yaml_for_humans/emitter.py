"""
Human-friendly PyYAML emitter with intelligent sequence formatting.

This module provides custom emitters that produce more readable YAML output by:
- Using indented sequences (dashes indented under parent containers)
- Placing strings on the same line as sequence dashes
- Separating complex structures on their own lines
- Prioritizing important keys in mappings
"""

import yaml
from yaml.emitter import Emitter
from yaml.events import (
    ScalarEvent,
    SequenceEndEvent,
    MappingStartEvent,
    MappingEndEvent,
    SequenceStartEvent,
)


class HumanFriendlyEmitter(Emitter):
    """
    Custom YAML emitter that produces human-friendly sequence formatting.

    Features:
    - Indented sequences (dashes indented under parent containers)
    - Inline strings: `- value` (compact format)
    - Multi-line objects: dash on separate line with indented content
    - Proper indentation hierarchy throughout
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_sequence_item = False

    def expect_block_sequence(self):
        """
        Override to force indented sequences instead of indentless ones.

        This is the key insight: PyYAML uses indentless sequences by default
        in mapping contexts, but human-friendly formatting needs indented sequences
        where dashes are indented under their parent containers.
        """
        self.increase_indent(flow=False, indentless=False)
        self.state = self.expect_first_block_sequence_item

    def expect_block_sequence_item(self, first=False):
        """
        Handle sequence items with intelligent formatting:
        - Scalar values (strings, numbers) on same line as dash
        - Empty mappings/sequences ({}, []) on same line as dash
        - Complex structures (non-empty mappings, nested sequences) on separate lines
        """
        if not first and isinstance(self.event, SequenceEndEvent):
            self._in_sequence_item = False
            self.indent = self.indents.pop()
            self.state = self.states.pop()
        else:
            # Write dash at current indent level
            self.write_indent()
            if isinstance(self.event, ScalarEvent):
                # For scalars, write "- " with exactly one space
                self.write_indicator("-", True, whitespace=False)
                self._in_sequence_item = False
            elif self._is_empty_container():
                # For empty containers, write "- " and keep inline
                self.write_indicator("-", True, whitespace=False)
                self._in_sequence_item = False
            else:
                # For complex structures, just write dash
                self.write_indicator("-", False, indention=False)
                # Complex structure: use separate line
                self.write_line_break()
                self._in_sequence_item = True

            self.states.append(self.expect_block_sequence_item)
            self.expect_node(sequence=True)

    def _is_empty_container(self):
        """
        Check if the current event is for an empty mapping or sequence.
        """
        if isinstance(self.event, MappingStartEvent):
            # Look ahead to see if the mapping is empty
            # We need to check if the next event is MappingEndEvent
            return (
                hasattr(self, "events")
                and len(self.events) > 0
                and isinstance(self.events[0], MappingEndEvent)
            )
        elif isinstance(self.event, SequenceStartEvent):
            # Look ahead to see if the sequence is empty
            return (
                hasattr(self, "events")
                and len(self.events) > 0
                and isinstance(self.events[0], SequenceEndEvent)
            )
        return False

    def expect_scalar(self):
        """
        Handle scalar values with proper sequence-aware indentation.
        """
        if self._in_sequence_item:
            # Ensure proper indentation for scalars following sequence dashes
            target_indent = self.indent + self.best_indent
            if self.column < target_indent:
                spaces_needed = target_indent - self.column
                self.stream.write(" " * spaces_needed)
                self.column = target_indent
                self.whitespace = True
            self._in_sequence_item = False

        super().expect_scalar()

    def expect_block_mapping(self):
        """
        Handle mappings with proper sequence context awareness.
        """
        if self._in_sequence_item:
            # Mapping within sequence: increase indent relative to dash
            self.increase_indent(flow=False, indentless=False)
            self._in_sequence_item = False
        else:
            # Standard mapping
            self.increase_indent(flow=False)

        self.state = self.expect_first_block_mapping_key

    def expect_block_mapping_simple_value(self):
        """
        Handle mapping values using default behavior for correct empty dict handling.

        The parent implementation correctly handles empty dictionaries inline
        while putting complex structures on new lines.
        """
        super().expect_block_mapping_simple_value()


class HumanFriendlyDumper(
    HumanFriendlyEmitter,
    yaml.serializer.Serializer,
    yaml.representer.Representer,
    yaml.resolver.Resolver,
):
    """
    Complete YAML dumper with human-friendly formatting and priority key ordering.

    Features:
    - Human-friendly sequence formatting from HumanFriendlyEmitter
    - Priority key ordering for container-related keys
    - Multiline string formatting using literal block scalars
    - Standard PyYAML serialization, representation, and resolution
    """

    # Container-related keys that should appear first in mappings
    PRIORITY_KEYS = [
        "name",
        "image",
        "imagePullPolicy",
        "env",
        "envFrom",
        "command",
        "args",
    ]

    def __init__(
        self,
        stream,
        default_style=None,
        default_flow_style=False,
        canonical=None,
        indent=None,
        width=None,
        allow_unicode=None,
        line_break=None,
        encoding=None,
        explicit_start=None,
        explicit_end=None,
        version=None,
        tags=None,
        sort_keys=True,
    ):
        """
        Initialize the human-friendly dumper with all PyYAML components.
        """
        HumanFriendlyEmitter.__init__(
            self,
            stream,
            canonical=canonical,
            indent=indent,
            width=width,
            allow_unicode=allow_unicode,
            line_break=line_break,
        )
        yaml.serializer.Serializer.__init__(
            self,
            encoding=encoding,
            explicit_start=explicit_start,
            explicit_end=explicit_end,
            version=version,
            tags=tags,
        )
        yaml.representer.Representer.__init__(
            self,
            default_style=default_style,
            default_flow_style=default_flow_style,
            sort_keys=sort_keys,
        )
        yaml.resolver.Resolver.__init__(self)

        # Register custom string representer for multiline formatting
        self.add_representer(str, self.represent_str)

    def represent_mapping(self, tag, mapping, flow_style=None):
        """
        Override to control key ordering with priority keys first.

        Args:
            tag: YAML tag for the mapping
            mapping: The mapping to represent
            flow_style: Flow style override

        Returns:
            Representation node with reordered keys
        """
        if not isinstance(mapping, dict):
            return super().represent_mapping(tag, mapping, flow_style)

        # Create ordered mapping with priority keys first
        ordered_mapping = {}

        # Add priority keys that exist in the mapping
        for priority_key in self.PRIORITY_KEYS:
            if priority_key in mapping:
                ordered_mapping[priority_key] = mapping[priority_key]

        # Add remaining keys in original order
        for key, value in mapping.items():
            if key not in self.PRIORITY_KEYS:
                ordered_mapping[key] = value

        return super().represent_mapping(tag, ordered_mapping, flow_style)

    def represent_str(self, dumper, data):
        """
        Override string representation to use literal block scalars for multiline strings.

        This method chooses the appropriate YAML scalar style:
        - Literal block scalar (|) for multiline strings with newlines
        - Default representation for single-line strings

        Args:
            dumper: The dumper instance (passed by PyYAML)
            data: The string data to represent

        Returns:
            ScalarNode with appropriate style for the string content
        """
        if "\n" in data:
            # Use literal block scalar for multiline strings
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        else:
            # Use default representation for single-line strings
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)
