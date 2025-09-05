"""
Formatting-aware emitter that preserves empty lines using metadata.

This extends the HumanFriendlyEmitter to inject empty lines based on
formatting metadata captured during parsing.
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

from .emitter import HumanFriendlyEmitter
from .formatting_aware import FormattingAwareDict, FormattingAwareList


class FormattingAwareEmitter(HumanFriendlyEmitter):
    """
    Emitter that uses the HumanFriendlyEmitter as base.

    The actual empty line logic is handled by the FormattingAwareDumper's
    representer which injects empty line markers.
    """

    def __init__(self, *args, preserve_empty_lines=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.preserve_empty_lines = preserve_empty_lines


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

    # Container-related keys that should appear first in mappings
    PRIORITY_KEYS = [
        "apiVersion",
        "kind",
        "metadata",
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
        preserve_empty_lines=True,
    ):
        """Initialize the formatting-aware dumper."""
        FormattingAwareEmitter.__init__(
            self,
            stream,
            canonical=canonical,
            indent=indent,
            width=width,
            allow_unicode=allow_unicode,
            line_break=line_break,
            preserve_empty_lines=preserve_empty_lines,
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

        # Register custom representers
        self.add_representer(str, self.represent_str)
        self.add_representer(FormattingAwareDict, self.represent_formatting_aware_dict)
        self.add_representer(FormattingAwareList, self.represent_formatting_aware_list)

    def represent_mapping(self, tag, mapping, flow_style=None):
        """Override to control key ordering with priority keys first."""
        # Handle FormattingAwareDict specially to preserve metadata
        if isinstance(mapping, FormattingAwareDict):
            # Don't reorder keys for FormattingAwareDict to preserve formatting
            return super().represent_mapping(tag, mapping, flow_style)

        if not isinstance(mapping, dict):
            return super().represent_mapping(tag, mapping, flow_style)

        # Create ordered mapping with priority keys first (only for regular dicts)
        priority_items = {
            key: mapping[key] for key in self.PRIORITY_KEYS if key in mapping
        }

        remaining_items = {
            key: value
            for key, value in mapping.items()
            if key not in self.PRIORITY_KEYS
        }

        ordered_mapping = {**priority_items, **remaining_items}

        return super().represent_mapping(tag, ordered_mapping, flow_style)

    def represent_formatting_aware_dict(self, dumper, data):
        """Represent FormattingAwareDict with empty line preservation."""
        if not self.preserve_empty_lines:
            # Just represent as regular dict if empty line preservation is disabled
            return self.represent_mapping("tag:yaml.org,2002:map", dict(data))

        # Create a mapping with empty line markers
        items = []

        for key, value in data.items():
            formatting = data._get_key_formatting(key)

            if formatting.empty_lines_before > 0:
                # Insert a special marker for empty lines
                empty_line_marker = f"__EMPTY_LINES_{formatting.empty_lines_before}__"
                items.append((empty_line_marker, None))

            items.append((key, value))

        return self.represent_mapping("tag:yaml.org,2002:map", items)

    def represent_formatting_aware_list(self, dumper, data):
        """Represent FormattingAwareList as a normal sequence."""
        # TODO: Implement sequence empty line preservation
        return self.represent_sequence("tag:yaml.org,2002:seq", list(data))

    def represent_str(self, dumper, data):
        """Override string representation to use literal block scalars for multiline strings."""
        if "\n" in data:
            # Use literal block scalar for multiline strings
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        else:
            # Use default representation for single-line strings
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)
