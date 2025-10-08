"""
Convenience functions for human-friendly YAML dumping.

This module provides drop-in replacements for yaml.dump() and yaml.dumps()
that use the HumanFriendlyDumper by default, with optional empty line preservation.
"""

import re
import threading
import yaml
from dataclasses import dataclass
from io import StringIO
from typing import Any, TextIO, Pattern, Optional, Type
from .emitter import HumanFriendlyDumper
from .formatting_emitter import FormattingAwareDumper
from .formatting_aware import FormattingAwareLoader

# Pre-compiled regex patterns for content line markers
_EMPTY_LINE_PATTERN: Pattern[str] = re.compile(r"__EMPTY_LINES_(\d+)__")  # Backward compatibility
_CONTENT_LINE_PATTERN: Pattern[str] = re.compile(r"__CONTENT_LINES_([^_]+)__")
_INLINE_COMMENT_PATTERN: Pattern[str] = re.compile(r"__INLINE_COMMENT_([^_]+)__")

# Thread-local buffer pool for StringIO reuse and content markers
_local: threading.local = threading.local()


@dataclass(frozen=True)
class DumpConfig:
    """Configuration for YAML dump operations.

    Encapsulates preservation flags and computed properties for dump behavior.
    """
    preserve_empty_lines: bool = False
    preserve_comments: bool = False
    dumper_class: Optional[Type] = None

    @property
    def needs_formatting(self) -> bool:
        """Check if any formatting preservation is enabled.

        Returns:
            True if preserve_empty_lines or preserve_comments is enabled

        Examples:
            >>> config = DumpConfig(preserve_empty_lines=True)
            >>> config.needs_formatting
            True

            >>> config = DumpConfig()
            >>> config.needs_formatting
            False
        """
        return self.preserve_empty_lines or self.preserve_comments


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


def _expand_content_marker(content_hash: str, markers: dict) -> list[str]:
    """Expand content marker hash to list of lines.

    Args:
        content_hash: Hash key for stored content
        markers: Dictionary mapping hashes to content

    Returns:
        List of lines (empty strings for blank lines, text for comments)
    """
    if content_hash not in markers:
        return []
    return markers[content_hash]


def _expand_empty_marker(count: int) -> list[str]:
    """Expand empty line marker to list of empty strings.

    Args:
        count: Number of empty lines

    Returns:
        List of empty strings
    """
    return [""] * count


def _expand_inline_comment(comment_hash: str, line: str, markers: dict) -> str:
    """Expand inline comment marker to line with comment.

    Args:
        comment_hash: Hash key for stored comment
        line: Original line with marker
        markers: Dictionary mapping hashes to comment info

    Returns:
        Line with marker replaced by comment, or cleaned line if hash not found
    """
    if comment_hash in markers:
        comment_info = markers[comment_hash]
        clean_line = line.replace(f"__INLINE_COMMENT_{comment_hash}__", "")
        return f"{clean_line}  {comment_info['comment']}"
    else:
        # Fallback: just remove the marker if not found
        return _INLINE_COMMENT_PATTERN.sub("", line)


def _process_single_line(line: str, markers: dict) -> list[str]:
    """Process single line for markers and expand to result lines.

    Args:
        line: Line to process
        markers: Dictionary of content/comment markers

    Returns:
        List of result lines (empty list if marker should be skipped,
        single-item list for regular lines, multi-item list for expanded content)
    """
    # Handle new unified content markers
    if "__CONTENT_LINES_" in line:
        match = _CONTENT_LINE_PATTERN.search(line)
        if match:
            content_hash = match.group(1)
            return _expand_content_marker(content_hash, markers)
        return []  # Skip marker line if no match

    # Handle legacy empty line markers for backward compatibility
    elif "__EMPTY_LINES_" in line:
        match = _EMPTY_LINE_PATTERN.search(line)
        if match:
            empty_count = int(match.group(1))
            return _expand_empty_marker(empty_count)
        return []  # Skip marker line if no match

    # Handle inline comment markers
    elif "__INLINE_COMMENT_" in line:
        match = _INLINE_COMMENT_PATTERN.search(line)
        if match:
            comment_hash = match.group(1)
            return [_expand_inline_comment(comment_hash, line, markers)]
        else:
            return [line]

    # No markers, return line as-is
    else:
        return [line]


def _process_content_line_markers(yaml_text: str, content_markers: dict = None) -> str:
    """Convert unified content line markers to actual empty lines and comments."""
    content_markers = content_markers or {}

    # Fast path: if no markers present, return original text unchanged
    if "__CONTENT_LINES_" not in yaml_text and "__EMPTY_LINES_" not in yaml_text and "__INLINE_COMMENT_" not in yaml_text:
        return yaml_text

    lines = yaml_text.split("\n")
    result = []

    for line in lines:
        result.extend(_process_single_line(line, content_markers))

    return "\n".join(result)


def _process_empty_line_markers(yaml_text: str) -> str:
    """Backward compatibility wrapper for old empty line marker processing."""
    return _process_content_line_markers(yaml_text)


def _select_dumper(preserve_empty_lines: bool, preserve_comments: bool) -> type:
    """Select appropriate dumper class based on preservation requirements.

    Args:
        preserve_empty_lines: Whether to preserve empty lines
        preserve_comments: Whether to preserve comments

    Returns:
        Dumper class (FormattingAwareDumper or HumanFriendlyDumper)
    """
    if preserve_empty_lines or preserve_comments:
        return FormattingAwareDumper
    else:
        return HumanFriendlyDumper


def _build_dump_kwargs(dumper_class: type, **user_kwargs: Any) -> dict:
    """Build kwargs dict for yaml.dump with defaults and user overrides.

    Args:
        dumper_class: Dumper class to use
        **user_kwargs: User-provided kwargs to merge

    Returns:
        Merged kwargs dict with defaults
    """
    defaults = {
        "Dumper": dumper_class,
        "default_flow_style": False,
        "indent": 2,
        "sort_keys": False,
        "width": 120,
    }
    defaults.update(user_kwargs)
    return defaults


def _create_preset_dumper(
    base_dumper: type, preserve_empty_lines: bool, preserve_comments: bool
) -> type:
    """Create dumper class with preservation flags preset.

    Args:
        base_dumper: Base dumper class to extend
        preserve_empty_lines: Whether to preserve empty lines
        preserve_comments: Whether to preserve comments

    Returns:
        New dumper class with preset flags
    """
    class PresetFormattingAwareDumper(base_dumper):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("preserve_empty_lines", preserve_empty_lines)
            kwargs.setdefault("preserve_comments", preserve_comments)
            super().__init__(*args, **kwargs)

    return PresetFormattingAwareDumper


def _setup_formatting_dumper(config: DumpConfig, dump_kwargs: dict) -> dict:
    """Configure dump kwargs for formatting-aware dumper.

    Removes PyYAML-incompatible parameters and creates preset dumper with
    preservation flags.

    Args:
        config: Dump configuration with preservation flags
        dump_kwargs: Base dump kwargs to modify

    Returns:
        Modified dump kwargs with formatting dumper configured

    Examples:
        >>> config = DumpConfig(preserve_empty_lines=True, preserve_comments=False)
        >>> kwargs = {"Dumper": FormattingAwareDumper, "indent": 2}
        >>> result = _setup_formatting_dumper(config, kwargs)
        >>> "preserve_empty_lines" not in result
        True
    """
    # Create a copy to avoid mutating input
    modified_kwargs = dump_kwargs.copy()

    # Remove formatting parameters (PyYAML doesn't expect them)
    modified_kwargs.pop("preserve_empty_lines", None)
    modified_kwargs.pop("preserve_comments", None)

    # Create preset dumper with preservation flags if needed
    if modified_kwargs.get("Dumper") == FormattingAwareDumper:
        modified_kwargs["Dumper"] = _create_preset_dumper(
            FormattingAwareDumper,
            config.preserve_empty_lines,
            config.preserve_comments
        )

    return modified_kwargs


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
    import yaml

    # 1. Create configuration and select dumper
    dumper_class = _select_dumper(preserve_empty_lines, preserve_comments)
    config = DumpConfig(
        preserve_empty_lines=preserve_empty_lines,
        preserve_comments=preserve_comments,
        dumper_class=dumper_class
    )

    # 2. Build dump kwargs with defaults and user overrides
    dump_kwargs = _build_dump_kwargs(dumper_class, **kwargs)

    # 3. Configure formatting dumper if needed
    if config.needs_formatting and dumper_class == FormattingAwareDumper:
        dump_kwargs = _setup_formatting_dumper(config, dump_kwargs)

    # 4. Execute dump with post-processing if needed
    if config.needs_formatting and dumper_class == FormattingAwareDumper:
        temp_stream = _get_buffer()
        try:
            result = yaml.dump(data, temp_stream, **dump_kwargs)
            yaml_output = temp_stream.getvalue()

            # Post-process to expand markers
            content_markers = _get_content_markers()
            yaml_output = _process_content_line_markers(yaml_output, content_markers)

            stream.write(yaml_output)
            return result
        finally:
            _return_buffer(temp_stream)
    else:
        return yaml.dump(data, stream, **dump_kwargs)


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
