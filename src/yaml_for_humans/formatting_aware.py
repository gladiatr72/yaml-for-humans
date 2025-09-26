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
    """Stores formatting information for YAML nodes.

    empty_lines_before now stores actual line content (empty lines and comments)
    as a List[str] where each string is either "" (empty line) or "# comment".
    For backward compatibility, it returns an int when accessed if there are only empty lines.
    """

    def __init__(self, empty_lines_before=None, empty_lines_after=0, eol_comment=None):
        # Handle backward compatibility: int -> List[str] conversion
        if isinstance(empty_lines_before, int):
            self._lines_before = [""] * empty_lines_before
        elif empty_lines_before is None:
            self._lines_before = []
        else:
            self._lines_before = empty_lines_before
        self.empty_lines_after = empty_lines_after
        self.eol_comment = eol_comment  # End-of-line comment

    @property
    def empty_lines_before(self):
        """Backward compatible property that returns int if only empty lines, List[str] if comments present."""
        # If all lines are empty (no comments), return count for backward compatibility
        if all(line == "" for line in self._lines_before):
            return len(self._lines_before)
        # If there are comments, return the full list
        return self._lines_before

    @empty_lines_before.setter
    def empty_lines_before(self, value):
        """Setter to maintain backward compatibility."""
        if isinstance(value, int):
            self._lines_before = [""] * value
        elif isinstance(value, list):
            self._lines_before = value
        else:
            raise ValueError(f"empty_lines_before must be int or List[str], got {type(value)}")

    @property
    def empty_lines_before_count(self):
        """Return count of empty lines only."""
        return sum(1 for line in self._lines_before if line == "")

    @property
    def lines_before_raw(self):
        """Get the raw List[str] content (for internal use)."""
        return self._lines_before

    def __repr__(self):
        return f"FormattingMetadata(before={len(self._lines_before)} lines, after={self.empty_lines_after})"


class CommentMetadata:
    """Stores comment information extracted from FormattingMetadata."""

    def __init__(self, comments_before=None, eol_comment=None):
        self.comments_before = comments_before or []
        self.eol_comment = eol_comment  # End-of-line comment (not implemented yet)

    def has_comments(self):
        """Return True if there are any comments."""
        return len(self.comments_before) > 0 or self.eol_comment is not None

    def __repr__(self):
        before_text = ', '.join(self.comments_before[:2])  # Show first 2 comments
        if len(self.comments_before) > 2:
            before_text += '...'
        eol_text = str(self.eol_comment) if self.eol_comment else 'None'
        return f"CommentMetadata(before=[{before_text}], eol={eol_text})"


class FormattingAwareComposer(Composer):
    """Composer that captures empty line and comment information in nodes."""

    def __init__(self):
        super().__init__()
        # Cache for memoized end line calculations
        self._end_line_cache = {}
        # Object pool for metadata to reduce allocations
        self._metadata_pool = []
        # Lazy loading for raw YAML lines
        self._raw_lines = None
        self._stream = None

    def _initialize_raw_lines(self, stream):
        """Initialize lazy loading for raw YAML lines."""
        if self._stream is not None:
            return

        # Store stream reference for lazy loading
        self._stream = stream
        self._raw_lines = None  # Will be loaded on first access

    def _ensure_raw_lines(self):
        """Ensure raw lines are loaded, return True if successful."""
        if self._raw_lines is not None:
            return True

        if self._stream is None:
            return False

        # Handle different stream types
        if isinstance(self._stream, str):
            # String input
            content = self._stream
        else:
            # File-like object
            try:
                if hasattr(self._stream, 'getvalue'):
                    # StringIO-like objects - efficient access
                    content = self._stream.getvalue()
                else:
                    # Regular file objects - minimize I/O
                    current_pos = self._stream.tell()
                    self._stream.seek(0)
                    content = self._stream.read()
                    self._stream.seek(current_pos)
            except (AttributeError, OSError):
                # If seek/tell not available, fall back to empty behavior
                self._raw_lines = []
                return True

        # Split into lines for comment extraction
        self._raw_lines = content.splitlines()
        return True

    def _extract_lines_before(self, start_line, previous_end_line):
        """Extract lines (empty lines and comments) between two content lines."""
        if not self._ensure_raw_lines():
            # Fallback to old behavior if raw lines not available
            empty_count = max(0, start_line - previous_end_line - 1)
            return [""] * empty_count

        lines_content = []

        # Extract lines between previous_end_line and start_line
        for line_num in range(previous_end_line + 1, start_line):
            if 0 <= line_num < len(self._raw_lines):
                line = self._raw_lines[line_num]
                stripped = line.strip()
                if stripped.startswith('#'):
                    # This is a comment line
                    lines_content.append(stripped)
                elif stripped == "":
                    # This is an empty line
                    lines_content.append("")
                # Otherwise, this is a content line - skip it (don't add to formatting)

        return lines_content

    def _extract_inline_comment(self, node):
        """Extract inline comment from the end of a node's line."""
        if not self._ensure_raw_lines() or not hasattr(node, 'end_mark') or node.end_mark is None:
            return None

        line_num = node.end_mark.line
        end_column = node.end_mark.column

        if 0 <= line_num < len(self._raw_lines):
            line = self._raw_lines[line_num]
            # Check if there's content after the node's end position
            remaining_content = line[end_column:].strip()
            if remaining_content.startswith('#'):
                return remaining_content  # Return the full comment including #

        return None

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

        # Determine if this is a root-level mapping by checking column position
        # Root mappings start at column 0, nested ones are indented
        is_root_mapping = node.start_mark.column == 0
        previous_end_line = -1 if is_root_mapping else node.start_mark.line - 2

        for i, ((key_node, value_node), current_end_line) in enumerate(
            zip(node.value, end_lines)
        ):
            current_start_line = key_node.start_mark.line

            # Process lines (empty lines and comments) before current item
            if i == 0:
                # First item: capture from document start (root) or parent boundary (nested)
                lines_before = self._extract_lines_before(current_start_line, previous_end_line)
                if lines_before:
                    self._set_metadata(key_node, empty_lines_before=lines_before)
            else:
                # Subsequent items: capture from previous item's end
                lines_before = self._extract_lines_before(current_start_line, previous_end_line)
                if lines_before:
                    self._set_metadata(key_node, empty_lines_before=lines_before)

            # Extract inline comment from value node (if any)
            inline_comment = self._extract_inline_comment(value_node)
            if inline_comment:
                self._set_metadata(key_node, eol_comment=inline_comment)

            # Process structural lines after current item (combined with main loop)
            if i + 1 < len(node.value):
                next_key_node, _ = node.value[i + 1]
                next_start_line = next_key_node.start_mark.line
                lines_before_next = self._extract_lines_before(next_start_line, current_end_line)

                if lines_before_next:
                    self._set_metadata(
                        next_key_node, empty_lines_before=lines_before_next
                    )

            previous_end_line = current_end_line

    def _add_sequence_formatting_metadata(self, node):
        """Add formatting metadata to sequence nodes with optimized processing."""
        if not node.value:
            return

        # Pre-calculate all end lines in single pass
        end_lines = [self._get_node_end_line(item) for item in node.value]

        # Determine if this is a root-level sequence by checking column position
        is_root_sequence = node.start_mark.column == 0
        previous_end_line = -1 if is_root_sequence else node.start_mark.line - 2

        for i, (item_node, current_end_line) in enumerate(zip(node.value, end_lines)):
            current_start_line = item_node.start_mark.line

            if i == 0:
                # First item: capture from document start (root) or parent boundary (nested)
                lines_before = self._extract_lines_before(current_start_line, previous_end_line)
                if lines_before:
                    self._set_metadata(item_node, empty_lines_before=lines_before)
            else:
                # Subsequent items: capture from previous item's end
                lines_before = self._extract_lines_before(current_start_line, previous_end_line)
                if lines_before:
                    self._set_metadata(item_node, empty_lines_before=lines_before)

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
            metadata.empty_lines_before = []
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

    def _get_key_comments(self, key):
        """Get comment metadata for a key."""
        formatting = self._get_key_formatting(key)
        # Extract comments from the lines_before list
        comments = [line for line in formatting.lines_before_raw if line.strip().startswith('#')]
        return CommentMetadata(comments_before=comments)

    def _set_key_comments(self, key, comment_metadata):
        """Set comment metadata for a key."""
        formatting = self._get_key_formatting(key)
        # Replace comment lines in lines_before, preserving empty lines
        new_lines_before = []
        for line in formatting.lines_before_raw:
            if not line.strip().startswith('#'):
                new_lines_before.append(line)  # Keep empty lines
        # Add new comments at the beginning
        new_lines_before = comment_metadata.comments_before + new_lines_before
        formatting.empty_lines_before = new_lines_before
        self._set_key_formatting(key, formatting)

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

    def _get_item_comments(self, index):
        """Get comment metadata for an item."""
        formatting = self._get_item_formatting(index)
        # Extract comments from the lines_before list
        comments = [line for line in formatting.empty_lines_before if line.strip().startswith('#')]
        return CommentMetadata(comments_before=comments)

    def _set_item_comments(self, index, comment_metadata):
        """Set comment metadata for an item."""
        formatting = self._get_item_formatting(index)
        # Replace comment lines in empty_lines_before, preserving empty lines
        new_lines_before = []
        for line in formatting.empty_lines_before:
            if not line.strip().startswith('#'):
                new_lines_before.append(line)  # Keep empty lines
        # Add new comments at the beginning
        new_lines_before = comment_metadata.comments_before + new_lines_before
        formatting.empty_lines_before = new_lines_before
        self._set_item_formatting(index, formatting)

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
        # Initialize raw lines for comment extraction
        self._initialize_raw_lines(stream)


# Register custom constructors
FormattingAwareLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    FormattingAwareConstructor.construct_mapping,
)

FormattingAwareLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    FormattingAwareConstructor.construct_sequence,
)
