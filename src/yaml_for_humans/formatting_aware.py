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

    def __init__(self):
        super().__init__()
        # Cache for memoized end line calculations
        self._end_line_cache = {}
        # Object pool for metadata to reduce allocations
        self._metadata_pool = []

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
        """Add formatting metadata to mapping nodes with optimized single-pass processing."""
        if not node.value:
            return

        # Pre-calculate all end lines in single pass to avoid redundant calculations
        end_lines = [self._get_node_end_line(value) for _, value in node.value]

        previous_end_line = node.start_mark.line - 1

        for i, ((key_node, value_node), current_end_line) in enumerate(
            zip(node.value, end_lines)
        ):
            current_start_line = key_node.start_mark.line

            # Process empty lines before current item
            if i > 0:  # Skip first item
                empty_lines = current_start_line - previous_end_line - 1
                if empty_lines > 0:
                    self._set_metadata(key_node, empty_lines_before=empty_lines)

            # Process structural empty lines after current item (combined with main loop)
            if i + 1 < len(node.value):
                next_key_node, _ = node.value[i + 1]
                next_start_line = next_key_node.start_mark.line
                empty_lines_after = next_start_line - current_end_line - 1

                if empty_lines_after > 0:
                    self._set_metadata(
                        next_key_node, empty_lines_before=empty_lines_after
                    )

            previous_end_line = current_end_line

    def _add_sequence_formatting_metadata(self, node):
        """Add formatting metadata to sequence nodes with optimized processing."""
        if not node.value:
            return

        # Pre-calculate all end lines in single pass
        end_lines = [self._get_node_end_line(item) for item in node.value]

        previous_end_line = node.start_mark.line - 1

        for i, (item_node, current_end_line) in enumerate(zip(node.value, end_lines)):
            current_start_line = item_node.start_mark.line

            if i > 0:  # Skip first item
                empty_lines = current_start_line - previous_end_line - 1
                if empty_lines > 0:
                    self._set_metadata(item_node, empty_lines_before=empty_lines)

            previous_end_line = current_end_line

    def _get_node_end_line(self, node):
        """Get the actual content end line of a node with caching."""
        node_id = id(node)
        if node_id not in self._end_line_cache:
            self._end_line_cache[node_id] = self._calculate_end_line(node)
        return self._end_line_cache[node_id]

    def _calculate_end_line(self, node):
        """Non-recursive end line calculation using iterative approach."""
        if isinstance(node, yaml.ScalarNode):
            return node.end_mark.line if node.end_mark else node.start_mark.line

        # Use iterative stack-based traversal instead of recursion
        stack = [node]
        max_end_line = node.start_mark.line

        while stack:
            current = stack.pop()
            if isinstance(current, yaml.ScalarNode):
                end_line = (
                    current.end_mark.line
                    if current.end_mark
                    else current.start_mark.line
                )
                max_end_line = max(max_end_line, end_line)
            elif isinstance(current, yaml.SequenceNode) and current.value:
                stack.extend(current.value)
            elif isinstance(current, yaml.MappingNode) and current.value:
                for key, value in current.value:
                    stack.append(value)
                    stack.append(key)

        return max_end_line

    def _get_metadata_object(self, **kwargs):
        """Get pooled metadata object to reduce allocations."""
        if self._metadata_pool:
            metadata = self._metadata_pool.pop()
            # Reset all attributes to defaults first
            metadata.empty_lines_before = 0
            metadata.empty_lines_after = 0
            # Set provided values
            for key, value in kwargs.items():
                setattr(metadata, key, value)
            return metadata
        return FormattingMetadata(**kwargs)

    def _set_metadata(self, node, **kwargs):
        """Efficiently set metadata on node."""
        if hasattr(node, "_formatting_metadata"):
            for key, value in kwargs.items():
                setattr(node._formatting_metadata, key, value)
        else:
            node._formatting_metadata = self._get_metadata_object(**kwargs)


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
