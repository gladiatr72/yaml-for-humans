"""
Convenience functions for human-friendly YAML dumping.

This module provides drop-in replacements for yaml.dump() and yaml.dumps()
that use the HumanFriendlyDumper by default, with optional empty line preservation.
"""

import re
from io import StringIO
from .emitter import HumanFriendlyDumper
from .formatting_emitter import FormattingAwareDumper
from .formatting_aware import FormattingAwareLoader


def _process_empty_line_markers(yaml_text):
    """Convert empty line markers to actual empty lines."""
    lines = yaml_text.split('\n')
    processed_lines = []
    
    for line in lines:
        if '__EMPTY_LINES_' in line:
            # Extract the number of empty lines needed
            match = re.search(r'__EMPTY_LINES_(\d+)__', line)
            if match:
                empty_count = int(match.group(1))
                processed_lines.extend('' for _ in range(empty_count))
            # Skip the marker line itself
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def dump(data, stream, preserve_empty_lines=False, **kwargs):
    """
    Serialize Python object to YAML with human-friendly formatting.

    Args:
        data: Python object to serialize
        stream: File-like object to write to
        preserve_empty_lines: If True, preserve empty lines from FormattingAware objects
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
    # Choose dumper based on whether we need empty line preservation
    if preserve_empty_lines:
        dumper_class = FormattingAwareDumper
    else:
        dumper_class = HumanFriendlyDumper
    
    # Set sensible defaults for human-friendly output
    defaults = {
        "Dumper": dumper_class,
        "default_flow_style": False,
        "indent": 2,
        "sort_keys": False,
    }

    # Update with user-provided kwargs first
    defaults.update(kwargs)
    
    # Handle preserve_empty_lines parameter specially
    if preserve_empty_lines and dumper_class == FormattingAwareDumper:
        # Remove preserve_empty_lines from kwargs passed to yaml.dump
        # since PyYAML doesn't expect it
        defaults.pop("preserve_empty_lines", None)
        # The FormattingAwareDumper will get it via its constructor
        if "Dumper" in defaults and defaults["Dumper"] == FormattingAwareDumper:
            # Create a custom dumper class with preserve_empty_lines preset
            class PresetFormattingAwareDumper(FormattingAwareDumper):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault('preserve_empty_lines', preserve_empty_lines)
                    super().__init__(*args, **kwargs)
            defaults["Dumper"] = PresetFormattingAwareDumper

    import yaml

    if preserve_empty_lines and dumper_class == FormattingAwareDumper:
        # For formatting-aware dumping, we need to post-process
        from io import StringIO
        temp_stream = StringIO()
        result = yaml.dump(data, temp_stream, **defaults)
        yaml_output = temp_stream.getvalue()
        
        # Post-process to convert empty line markers to actual empty lines
        yaml_output = _process_empty_line_markers(yaml_output)
        
        # Write to the actual stream
        stream.write(yaml_output)
        return result
    else:
        return yaml.dump(data, stream, **defaults)


def dumps(data, preserve_empty_lines=False, **kwargs):
    """
    Serialize Python object to YAML string with human-friendly formatting.

    Args:
        data: Python object to serialize
        preserve_empty_lines: If True, preserve empty lines from FormattingAware objects
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
    stream = StringIO()
    dump(data, stream, preserve_empty_lines=preserve_empty_lines, **kwargs)
    return stream.getvalue()


def load_with_formatting(stream):
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
        if '\n' in stream or ':' in stream:
            # Looks like YAML content
            return yaml.load(stream, Loader=FormattingAwareLoader)
        else:
            # Assume it's a file path
            with open(stream, 'r') as f:
                return yaml.load(f, Loader=FormattingAwareLoader)
    else:
        # Stream object
        return yaml.load(stream, Loader=FormattingAwareLoader)
