"""
Formatting-aware YAML components for preserving empty lines.

This module implements Option 1 - capturing formatting metadata during PyYAML parsing
and preserving it through to output generation.
"""

import yaml
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.resolver import Resolver


class FormattingMetadata:
    """Stores formatting information for YAML nodes."""

    def __init__(self, empty_lines_before=0, empty_lines_after=0):
        self.empty_lines_before = empty_lines_before
        self.empty_lines_after = empty_lines_after

    def __repr__(self):
        return f"FormattingMetadata(before={self.empty_lines_before}, after={self.empty_lines_after})"


class FormattingAwareComposer(Composer):
    """Composer that captures empty line information in nodes."""

    def compose_mapping_node(self, anchor):
        """Compose mapping node with empty line metadata."""
        node = super().compose_mapping_node(anchor)
        self._add_mapping_formatting_metadata(node)
        return node

    def compose_sequence_node(self, anchor):
        """Compose sequence node with empty line metadata."""
        node = super().compose_sequence_node(anchor)
        self._add_sequence_formatting_metadata(node)
        return node

    def _add_mapping_formatting_metadata(self, node):
        """Add formatting metadata to mapping nodes."""
        if not node.value:
            return

        # Calculate empty lines between mapping items
        previous_end_line = node.start_mark.line - 1

        for i, (key_node, value_node) in enumerate(node.value):
            current_start_line = key_node.start_mark.line

            if i > 0:  # Skip first item
                empty_lines = current_start_line - previous_end_line - 1
                if empty_lines > 0:
                    key_node._formatting_metadata = FormattingMetadata(
                        empty_lines_before=empty_lines
                    )

            # Update previous end line based on value node
            previous_end_line = self._get_node_end_line(value_node)

            # Check for empty lines after this key-value pair (structural empty lines)
            # This handles empty lines that appear after sequences/mappings end
            self._check_structural_empty_lines_after(key_node, value_node, i, node)

    def _check_structural_empty_lines_after(
        self, key_node, value_node, index, parent_node
    ):
        """Check for structural empty lines after sequences/mappings within a parent mapping."""
        # Only check if there's a next mapping item to compare against
        if index + 1 < len(parent_node.value):
            next_key_node, next_value_node = parent_node.value[index + 1]

            # Get the actual content end line of the current value
            value_end_line = self._get_node_end_line(value_node)

            # Get the start line of the next key
            next_start_line = next_key_node.start_mark.line

            # Calculate empty lines between the end of this value and start of next key
            empty_lines_after = next_start_line - value_end_line - 1

            if empty_lines_after > 0:
                # Store as empty_lines_before for the next key (this is how we preserve it)
                if hasattr(next_key_node, "_formatting_metadata"):
                    # Add to existing metadata
                    next_key_node._formatting_metadata.empty_lines_before = (
                        empty_lines_after
                    )
                else:
                    # Create new metadata
                    next_key_node._formatting_metadata = FormattingMetadata(
                        empty_lines_before=empty_lines_after
                    )

    def _add_sequence_formatting_metadata(self, node):
        """Add formatting metadata to sequence nodes."""
        if not node.value:
            return

        # Calculate empty lines between sequence items
        previous_end_line = node.start_mark.line - 1

        for i, item_node in enumerate(node.value):
            current_start_line = item_node.start_mark.line

            if i > 0:  # Skip first item
                empty_lines = current_start_line - previous_end_line - 1
                if empty_lines > 0:
                    item_node._formatting_metadata = FormattingMetadata(
                        empty_lines_before=empty_lines
                    )

            # Update previous end line
            previous_end_line = self._get_node_end_line(item_node)

    def _get_node_end_line(self, node):
        """Get the actual content end line of a node, not the structural end line."""
        # For scalar nodes, use the end mark directly
        if isinstance(node, yaml.ScalarNode):
            return node.end_mark.line if node.end_mark else node.start_mark.line

        # For sequence nodes, find the last item's content end line
        elif isinstance(node, yaml.SequenceNode):
            if not node.value:
                return node.start_mark.line
            # Recursively get the end line of the last item
            last_item = node.value[-1]
            return self._get_node_end_line(last_item)

        # For mapping nodes, find the last value's content end line
        elif isinstance(node, yaml.MappingNode):
            if not node.value:
                return node.start_mark.line
            # Get the last key-value pair and find the value's end line
            last_key, last_value = node.value[-1]
            return self._get_node_end_line(last_value)

        # Fallback to start line for unknown node types
        else:
            return node.start_mark.line


class FormattingAwareConstructor(SafeConstructor):
    """Constructor that preserves formatting metadata in Python objects."""

    def construct_mapping(self, node, deep=False):
        """Construct mapping with preserved formatting metadata."""
        formatting_dict = FormattingAwareDict()

        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None,
                None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark,
            )

        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            value = self.construct_object(value_node, deep=deep)
            formatting_dict[key] = value

            # Transfer formatting metadata if present
            if hasattr(key_node, "_formatting_metadata"):
                formatting_dict._set_key_formatting(key, key_node._formatting_metadata)

        return formatting_dict

    def construct_sequence(self, node, deep=False):
        """Construct sequence with preserved formatting metadata."""
        formatting_list = FormattingAwareList()

        if not isinstance(node, yaml.SequenceNode):
            raise yaml.constructor.ConstructorError(
                None,
                None,
                "expected a sequence node, but found %s" % node.id,
                node.start_mark,
            )

        for i, item_node in enumerate(node.value):
            value = self.construct_object(item_node, deep=deep)
            formatting_list.append(value)

            # Transfer formatting metadata if present
            if hasattr(item_node, "_formatting_metadata"):
                formatting_list._set_item_formatting(i, item_node._formatting_metadata)

        return formatting_list


class FormattingAwareDict(dict):
    """Dictionary subclass that stores formatting metadata for keys."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key_formatting = {}

    def _set_key_formatting(self, key, formatting):
        """Set formatting metadata for a key."""
        self._key_formatting[key] = formatting

    def _get_key_formatting(self, key):
        """Get formatting metadata for a key."""
        return self._key_formatting.get(key, FormattingMetadata())

    def __setitem__(self, key, value):
        """Override to maintain formatting metadata when items are reassigned."""
        super().__setitem__(key, value)
        # Keep existing formatting metadata if key already exists

    def __delitem__(self, key):
        """Override to clean up formatting metadata."""
        super().__delitem__(key)
        self._key_formatting.pop(key, None)


class FormattingAwareList(list):
    """List subclass that stores formatting metadata for items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_formatting = {}

    def _set_item_formatting(self, index, formatting):
        """Set formatting metadata for an item."""
        self._item_formatting[index] = formatting

    def _get_item_formatting(self, index):
        """Get formatting metadata for an item."""
        return self._item_formatting.get(index, FormattingMetadata())

    def append(self, value):
        """Override to maintain formatting metadata indices."""
        super().append(value)
        # Note: formatting metadata indices need to be managed carefully
        # when list is modified after construction


class FormattingAwareLoader(
    yaml.reader.Reader,
    yaml.scanner.Scanner,
    yaml.parser.Parser,
    FormattingAwareComposer,
    FormattingAwareConstructor,
    Resolver,
):
    """Complete loader that preserves formatting information."""

    def __init__(self, stream):
        yaml.reader.Reader.__init__(self, stream)
        yaml.scanner.Scanner.__init__(self)
        yaml.parser.Parser.__init__(self)
        FormattingAwareComposer.__init__(self)
        FormattingAwareConstructor.__init__(self)
        Resolver.__init__(self)


# Register custom constructors
FormattingAwareLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    FormattingAwareConstructor.construct_mapping,
)

FormattingAwareLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    FormattingAwareConstructor.construct_sequence,
)
