"""
Formatting-aware emitter that preserves empty lines using metadata.

This extends the HumanFriendlyEmitter to inject empty lines based on
formatting metadata captured during parsing.
"""

import yaml
import hashlib
import json

from .emitter import HumanFriendlyEmitter
from .formatting_aware import FormattingAwareDict, FormattingAwareList


class FormattingAwareEmitter(HumanFriendlyEmitter):
    """
    Emitter that uses the HumanFriendlyEmitter as base.

    The actual empty line logic is handled by the FormattingAwareDumper's
    representer which injects empty line markers.
    """

    def __init__(self, *args, preserve_empty_lines=True, preserve_comments=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.preserve_empty_lines = preserve_empty_lines
        self.preserve_comments = preserve_comments


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
    PRIORITY_KEYS = frozenset(
        [
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
    )

    # Priority ordering for efficient single-pass sorting
    PRIORITY_ORDER = {
        "apiVersion": 0,
        "kind": 1,
        "metadata": 2,
        "name": 3,
        "image": 4,
        "imagePullPolicy": 5,
        "env": 6,
        "envFrom": 7,
        "command": 8,
        "args": 9,
    }

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
        preserve_comments=False,
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
            preserve_comments=preserve_comments,
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

        # Storage for content marker data (for post-processing)
        self._content_markers = {}

        # Register custom representers
        self.add_representer(str, self.represent_str)
        self.add_representer(FormattingAwareDict, self.represent_formatting_aware_dict)
        self.add_representer(FormattingAwareList, self.represent_formatting_aware_list)

    def open(self):
        """Override to store content markers when dumping starts."""
        # Store markers in thread-local storage when dumping starts
        try:
            from .dumper import _store_content_markers
            _store_content_markers(self._content_markers)
        except ImportError:
            pass  # Avoid circular import issues
        return super().open()

    def represent_mapping(self, tag, mapping, flow_style=None):
        """Override to control key ordering with priority keys first."""
        # Handle FormattingAwareDict specially to preserve metadata
        if isinstance(mapping, FormattingAwareDict):
            # Don't reorder keys for FormattingAwareDict to preserve formatting
            return super().represent_mapping(tag, mapping, flow_style)

        if not isinstance(mapping, dict):
            return super().represent_mapping(tag, mapping, flow_style)

        # Single-pass sorting with priority-aware key function (only for regular dicts)
        def get_sort_key(item):
            key = item[0]
            return self.PRIORITY_ORDER.get(key, 999)

        ordered_items = sorted(mapping.items(), key=get_sort_key)
        ordered_mapping = dict(ordered_items)

        return super().represent_mapping(tag, ordered_mapping, flow_style)

    def represent_formatting_aware_dict(self, dumper, data):
        """Represent FormattingAwareDict with unified content line preservation."""
        if not self.preserve_empty_lines and not self.preserve_comments:
            # Just represent as regular dict if line preservation is disabled
            return self.represent_mapping("tag:yaml.org,2002:map", dict(data))

        # Create a mapping with unified content line markers
        items = []

        for key, value in data.items():
            formatting = data._get_key_formatting(key)

            if formatting.empty_lines_before:
                # Filter content based on preserve settings
                filtered_lines = []
                for line in formatting.lines_before_raw:
                    if line == "":  # Empty line
                        if self.preserve_empty_lines:
                            filtered_lines.append(line)
                    elif line.startswith("#"):  # Comment
                        if self.preserve_comments:
                            filtered_lines.append(line)

                if filtered_lines:
                    # Create a unique marker for this content block
                    content_data = json.dumps(filtered_lines, separators=(',', ':'))
                    content_hash = hashlib.md5(content_data.encode()).hexdigest()[:8]
                    content_marker = f"__CONTENT_LINES_{content_hash}__"
                    # Store the mapping for post-processing
                    self._content_markers[content_hash] = filtered_lines
                    items.append((content_marker, None))

            # Handle inline comments
            if formatting.eol_comment and self.preserve_comments:
                # Create a marker key that includes the original key and inline comment marker
                inline_comment_hash = hashlib.md5(formatting.eol_comment.encode()).hexdigest()[:8]
                inline_marker = f"__INLINE_COMMENT_{inline_comment_hash}__"
                # Store the original key and comment for post-processing
                self._content_markers[inline_comment_hash] = {
                    'key': key,
                    'comment': formatting.eol_comment
                }
                # Use a composite key that will be processed later
                composite_key = f"{key}{inline_marker}"
                items.append((composite_key, value))
            else:
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
