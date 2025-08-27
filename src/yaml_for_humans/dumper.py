"""
Convenience functions for human-friendly YAML dumping.

This module provides drop-in replacements for yaml.dump() and yaml.dumps()
that use the HumanFriendlyDumper by default.
"""

from io import StringIO
from .emitter import HumanFriendlyDumper


def dump(data, stream, **kwargs):
    """
    Serialize Python object to YAML with human-friendly formatting.

    Args:
        data: Python object to serialize
        stream: File-like object to write to
        **kwargs: Additional arguments passed to HumanFriendlyDumper

    Example:
        with open('output.yaml', 'w') as f:
            dump(my_data, f, indent=2)
    """
    # Set sensible defaults for human-friendly output
    defaults = {
        "Dumper": HumanFriendlyDumper,
        "default_flow_style": False,
        "indent": 2,
        "sort_keys": False,
    }

    # Update with user-provided kwargs
    defaults.update(kwargs)

    import yaml

    return yaml.dump(data, stream, **defaults)


def dumps(data, **kwargs):
    """
    Serialize Python object to YAML string with human-friendly formatting.

    Args:
        data: Python object to serialize
        **kwargs: Additional arguments passed to HumanFriendlyDumper

    Returns:
        str: YAML representation of the data

    Example:
        yaml_str = dumps(my_data, indent=2)
        print(yaml_str)
    """
    stream = StringIO()
    dump(data, stream, **kwargs)
    return stream.getvalue()
