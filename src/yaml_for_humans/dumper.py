"""
Convenience functions for human-friendly YAML dumping.

This module provides drop-in replacements for yaml.dump() and yaml.dumps()
that use the HumanFriendlyDumper by default, with optional empty line preservation.
"""

import re
import threading
import yaml
import json
from io import StringIO
from typing import Any, TextIO, Pattern
from .emitter import HumanFriendlyDumper
from .formatting_emitter import FormattingAwareDumper
from .formatting_aware import FormattingAwareLoader

# Pre-compiled regex patterns for content line markers
_EMPTY_LINE_PATTERN: Pattern[str] = re.compile(r"__EMPTY_LINES_(\d+)__")  # Backward compatibility
_CONTENT_LINE_PATTERN: Pattern[str] = re.compile(r"__CONTENT_LINES_([^_]+)__")
_INLINE_COMMENT_PATTERN: Pattern[str] = re.compile(r"__INLINE_COMMENT_([^_]+)__")

# Thread-local buffer pool for StringIO reuse and content markers
_local: threading.local = threading.local()


def _get_buffer() -> StringIO:
    """Get a reusable StringIO buffer for current thread."""
    if not hasattr(_local, "buffer_pool"):
        _local.buffer_pool = []

    if _local.buffer_pool:
        buffer = _local.buffer_pool.pop()
        buffer.seek(0)
        buffer.truncate(0)
        return buffer
    else:
        return StringIO()


def _store_content_markers(markers: dict) -> None:
    """Store content markers in thread-local storage."""
    _local.content_markers = markers


def _get_content_markers() -> dict:
    """Get content markers from thread-local storage."""
    return getattr(_local, 'content_markers', {})


def _return_buffer(buffer: StringIO) -> None:
    """Return buffer to pool for reuse."""
    if not hasattr(_local, "buffer_pool"):
        _local.buffer_pool = []

    if len(_local.buffer_pool) < 5:  # Limit pool size
        _local.buffer_pool.append(buffer)


def _process_content_line_markers(yaml_text: str, content_markers: dict = None) -> str:
    """Convert unified content line markers to actual empty lines and comments."""
    content_markers = content_markers or {}

    # Fast path: if no markers present, return original text unchanged
    if "__CONTENT_LINES_" not in yaml_text and "__EMPTY_LINES_" not in yaml_text and "__INLINE_COMMENT_" not in yaml_text:
        return yaml_text

    lines = yaml_text.split("\n")
    result = []
    result_extend = result.extend  # Cache method lookup for performance

    for line in lines:
        # Handle new unified content markers
        if "__CONTENT_LINES_" in line:
            match = _CONTENT_LINE_PATTERN.search(line)
            if match:
                content_hash = match.group(1)
                if content_hash in content_markers:
                    # Convert stored line content to actual lines
                    content_lines = content_markers[content_hash]
                    for content_line in content_lines:
                        if content_line == "":  # Empty line
                            result.append("")
                        else:  # Comment line
                            result.append(content_line)
            # Skip marker lines
        # Handle legacy empty line markers for backward compatibility
        elif "__EMPTY_LINES_" in line:
            match = _EMPTY_LINE_PATTERN.search(line)
            if match:
                empty_count = int(match.group(1))
                result_extend([""] * empty_count)  # Bulk extend operation
            # Skip marker lines
        # Handle inline comment markers
        elif "__INLINE_COMMENT_" in line:
            match = _INLINE_COMMENT_PATTERN.search(line)
            if match:
                comment_hash = match.group(1)
                if comment_hash in content_markers:
                    comment_info = content_markers[comment_hash]
                    # Replace the composite key with original key + comment
                    clean_line = line.replace(f"__INLINE_COMMENT_{comment_hash}__", "")
                    result.append(f"{clean_line}  {comment_info['comment']}")
                else:
                    # Fallback: just remove the marker if not found
                    clean_line = _INLINE_COMMENT_PATTERN.sub("", line)
                    result.append(clean_line)
            else:
                result.append(line)
        else:
            result.append(line)

    return "\n".join(result)


def _process_empty_line_markers(yaml_text: str) -> str:
    """Backward compatibility wrapper for old empty line marker processing."""
    return _process_content_line_markers(yaml_text)


def dump(
    data: Any, stream: TextIO, preserve_empty_lines: bool = False, preserve_comments: bool = False, **kwargs: Any
) -> None:
    """
    Serialize Python object to YAML with human-friendly formatting.

    Args:
        data: Python object to serialize
        stream: File-like object to write to
        preserve_empty_lines: If True, preserve empty lines from FormattingAware objects
        preserve_comments: If True, preserve comments from FormattingAware objects
        **kwargs: Additional arguments passed to the dumper

    Example:
        with open('output.yaml', 'w') as f:
            dump(my_data, f, indent=2)

        # To preserve empty lines from loaded YAML:
        with open('input.yaml', 'r') as f:
            data = yaml.load(f, Loader=FormattingAwareLoader)
        with open('output.yaml', 'w') as f:
            dump(data, f, preserve_empty_lines=True)
    """
    # Choose dumper based on whether we need formatting preservation
    if preserve_empty_lines or preserve_comments:
        dumper_class = FormattingAwareDumper
    else:
        dumper_class = HumanFriendlyDumper

    # Set sensible defaults for human-friendly output
    defaults = {
        "Dumper": dumper_class,
        "default_flow_style": False,
        "indent": 2,
        "sort_keys": False,
        "width": 120,
    }

    # Update with user-provided kwargs first
    defaults.update(kwargs)

    # Handle formatting preservation parameters specially
    if (preserve_empty_lines or preserve_comments) and dumper_class == FormattingAwareDumper:
        # Remove formatting parameters from kwargs passed to yaml.dump
        # since PyYAML doesn't expect them
        defaults.pop("preserve_empty_lines", None)
        defaults.pop("preserve_comments", None)
        # The FormattingAwareDumper will get them via its constructor
        if "Dumper" in defaults and defaults["Dumper"] == FormattingAwareDumper:
            # Create a custom dumper class with formatting preservation preset
            class PresetFormattingAwareDumper(FormattingAwareDumper):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault("preserve_empty_lines", preserve_empty_lines)
                    kwargs.setdefault("preserve_comments", preserve_comments)
                    super().__init__(*args, **kwargs)

            defaults["Dumper"] = PresetFormattingAwareDumper

    import yaml

    if (preserve_empty_lines or preserve_comments) and dumper_class == FormattingAwareDumper:
        # For formatting-aware dumping, we need to post-process
        temp_stream = _get_buffer()
        try:
            # Use yaml.dump with our custom dumper class that stores content markers
            result = yaml.dump(data, temp_stream, **defaults)
            yaml_output = temp_stream.getvalue()

            # Post-process to convert content line markers to actual lines
            content_markers = _get_content_markers()
            yaml_output = _process_content_line_markers(yaml_output, content_markers)

            # Write to the actual stream
            stream.write(yaml_output)
            return result
        finally:
            _return_buffer(temp_stream)
    else:
        return yaml.dump(data, stream, **defaults)


def dumps(data: Any, preserve_empty_lines: bool = False, preserve_comments: bool = False, **kwargs: Any) -> str:
    """
    Serialize Python object to YAML string with human-friendly formatting.

    Args:
        data: Python object to serialize
        preserve_empty_lines: If True, preserve empty lines from FormattingAware objects
        preserve_comments: If True, preserve comments from FormattingAware objects
        **kwargs: Additional arguments passed to the dumper

    Returns:
        str: YAML representation of the data

    Example:
        yaml_str = dumps(my_data, indent=2)
        print(yaml_str)

        # To preserve empty lines:
        data = yaml.load(yaml_str, Loader=FormattingAwareLoader)
        yaml_with_empty_lines = dumps(data, preserve_empty_lines=True)
    """
    stream = _get_buffer()
    try:
        dump(data, stream, preserve_empty_lines=preserve_empty_lines, preserve_comments=preserve_comments, **kwargs)
        return stream.getvalue()
    finally:
        _return_buffer(stream)


def load_with_formatting(stream: str | TextIO) -> Any:
    """
    Load YAML with formatting metadata preservation.

    Args:
        stream: Input stream, file path string, or YAML string

    Returns:
        Python object with formatting metadata attached

    Example:
        with open('input.yaml', 'r') as f:
            data = load_with_formatting(f)

        # Or load from file path
        data = load_with_formatting('input.yaml')

        # Or load from string
        data = load_with_formatting('key: value')

        # Now dump with preserved empty lines
        output = dumps(data, preserve_empty_lines=True)
    """
    import yaml

    # Handle different input types
    if isinstance(stream, str):
        # Check if it's a file path or YAML content
        if "\n" in stream or ":" in stream:
            # Looks like YAML content
            return yaml.load(stream, Loader=FormattingAwareLoader)
        else:
            # Assume it's a file path
            with open(stream, "r") as f:
                return yaml.load(f, Loader=FormattingAwareLoader)
    else:
        # Stream object
        return yaml.load(stream, Loader=FormattingAwareLoader)


class KeyPreservingResolver(yaml.resolver.Resolver):
    """
    Custom YAML resolver that preserves string keys while allowing boolean conversion for values.

    This resolver prevents automatic conversion of keys like 'on', 'off', 'yes', 'no' to booleans
    while maintaining standard YAML behavior for values.
    """

    def __init__(self):
        super().__init__()
        # Remove boolean resolver to prevent automatic conversion
        # We'll add it back selectively for values only
        if (None, 'tag:yaml.org,2002:bool') in self.yaml_implicit_resolvers:
            self.yaml_implicit_resolvers.remove((None, 'tag:yaml.org,2002:bool'))

        # Remove bool patterns from first character lookups
        for char, resolvers in list(self.yaml_implicit_resolvers.items()):
            if char in ['y', 'Y', 'n', 'N', 't', 'T', 'f', 'F', 'o', 'O']:
                # Filter out boolean resolvers
                filtered_resolvers = [
                    (tag, regexp) for tag, regexp in resolvers
                    if tag != 'tag:yaml.org,2002:bool'
                ]
                if filtered_resolvers != resolvers:
                    self.yaml_implicit_resolvers[char] = filtered_resolvers


class KeyPreservingSafeLoader(yaml.SafeLoader):
    """
    Safe YAML loader that preserves problematic string keys as strings.

    Inherits from SafeLoader for security while removing boolean resolvers
    to prevent automatic boolean conversion of mapping keys.
    """

    def __init__(self, stream):
        super().__init__(stream)
        # Remove boolean resolver after parent initialization
        self._remove_boolean_resolvers()

    def _remove_boolean_resolvers(self):
        """Remove boolean resolvers to prevent automatic conversion."""
        # Remove boolean resolver from implicit resolvers
        for key, resolvers in list(self.yaml_implicit_resolvers.items()):
            filtered_resolvers = [
                (tag, regexp) for tag, regexp in resolvers
                if tag != 'tag:yaml.org,2002:bool'
            ]
            if filtered_resolvers != resolvers:
                self.yaml_implicit_resolvers[key] = filtered_resolvers


def _load_yaml_safe_keys(content: str) -> Any:
    """
    Load YAML content using a safe loader that preserves string keys.

    This function prevents automatic conversion of keys like 'on', 'off', 'yes', 'no'
    to boolean values while maintaining security by using SafeLoader as the base.

    Args:
        content: YAML content string to parse

    Returns:
        Parsed Python object with string keys preserved

    Example:
        >>> yaml_content = "on:\\n  pull_request:\\n  push:"
        >>> result = _load_yaml_safe_keys(yaml_content)
        >>> list(result.keys())[0]  # Returns 'on' as string, not True
        'on'
    """
    return yaml.load(content, Loader=KeyPreservingSafeLoader)
