"""
Tests for multiline scalar formatting functionality.

This module tests that multiline strings are formatted using literal block scalars (|)
instead of escaped quoted strings for better human readability.
"""

import yaml
from yaml_for_humans import dumps


def test_multiline_string_uses_literal_block():
    """Test that multiline strings are formatted using literal block scalars."""
    data = {"single": "single line", "multi": "line1\nline2\nline3"}

    result = dumps(data)

    # Should contain literal block scalar for multiline
    assert "multi: |-" in result or "multi: |" in result
    # Should not contain escaped newlines for multiline content
    assert "\\n" not in result
    # Single line should remain as regular scalar
    assert "single: single line" in result

    # Verify the YAML is still valid and round-trips correctly
    parsed = yaml.safe_load(result)
    assert parsed == data


def test_complex_multiline_formatting():
    """Test that complex multiline content uses readable literal block format."""
    data = {
        "config": (
            "line 1\n"
            "line 2 with spaces\n"
            "line 3\n"
            "  indented content\n"
            "line 5\n"
        )
    }

    result = dumps(data)

    # Should use literal block scalar, not escaped strings
    assert "config: |" in result
    assert "\\n" not in result

    # Should contain readable content lines
    assert "line 1" in result
    assert "line 2 with spaces" in result
    assert "  indented content" in result

    # Verify round-trip
    parsed = yaml.safe_load(result)
    assert parsed == data


def test_mixed_string_types():
    """Test that single-line and multiline strings are handled appropriately."""
    data = {
        "short": "just a short string",
        "long_single": "a very long single line string that might wrap but has no newlines",
        "multiline_simple": "first\nsecond",
        "multiline_complex": "line 1\nline 2\n  indented\nline 4",
        "empty": "",
    }

    result = dumps(data)

    # Single line strings should not use literal blocks
    assert "short: just a short string" in result

    # Multiline strings should use literal blocks
    assert "multiline_simple: |-" in result or "multiline_simple: |" in result
    assert "multiline_complex: |-" in result or "multiline_complex: |" in result

    # Should not contain escaped newlines anywhere
    assert "\\n" not in result

    # Verify round-trip
    parsed = yaml.safe_load(result)
    assert parsed == data


def test_multiline_edge_cases():
    """Test edge cases for multiline string handling."""
    data = {
        "trailing_newline": "line1\nline2\n",
        "leading_newline": "\nline1\nline2",
        "multiple_newlines": "line1\n\n\nline2",
        "only_newlines": "\n\n\n",
        "special_chars": "line with: colons and - dashes\nand more\n",
    }

    result = dumps(data)

    # All should use literal block format
    for key in data.keys():
        assert f"{key}: |" in result

    # Should not contain escaped characters
    assert "\\n" not in result

    # Verify round-trip
    parsed = yaml.safe_load(result)
    assert parsed == data


def test_comparison_with_test_data():
    """Test that output matches the expected pretty format from test data."""
    # This uses the same data structure as the test files but focuses on
    # the general multiline formatting capability, not Kubernetes specifics
    data = {
        "metadata": {"name": "example-config"},
        "data": {
            "sample.conf": (
                "user nginx;\n"
                "worker_processes  3;\n"
                "error_log  /var/log/nginx/error.log;\n"
                "events {\n"
                "  worker_connections  10240;\n"
                "}\n"
                "\n"
                "stream {\n"
                "        upstream backend {\n"
                "                least_conn;\n"
                "                server somewhere:9200;\n"
                "        }\n"
                "        server {\n"
                "                listen 3080;\n"
                "                proxy_pass backend;\n"
                "                proxy_timeout 30s;\n"
                "        }\n"
                "}\n"
            )
        },
    }

    result = dumps(data)

    # Should use literal block scalar for readable multiline content
    assert "sample.conf: |" in result
    assert "\\n" not in result

    # Content should be readable
    assert "user nginx;" in result
    assert "worker_processes  3;" in result
    assert "server somewhere:9200;" in result

    # Verify round-trip
    parsed = yaml.safe_load(result)
    assert parsed == data
