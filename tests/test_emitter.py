"""
Unit tests for HumanFriendlyEmitter.

Tests the core emitter functionality including sequence formatting,
key ordering, and indentation behavior.
"""

from io import StringIO

import pytest
import yaml

from yaml_for_humans.dumper import dumps
from yaml_for_humans.emitter import HumanFriendlyDumper


class TestHumanFriendlyEmitter:
    """Test the HumanFriendlyEmitter class."""

    def test_simple_string_sequence(self):
        """Test that string sequences are formatted inline."""
        data = {"items": ["first", "second", "third"]}
        result = dumps(data)

        expected_lines = ["items:", "  - first", "  - second", "  - third"]

        for line in expected_lines:
            assert line in result

    def test_complex_object_sequence(self):
        """Test that object sequences use separate lines."""
        data = {
            "containers": [
                {"name": "web", "image": "nginx:latest"},
                {"name": "app", "image": "python:3.9"},
            ]
        }
        result = dumps(data)

        # Should have dashes on separate lines
        assert "containers:\n  -\n    name: web" in result
        assert "image: nginx:latest\n  -\n    name: app" in result

    def test_mixed_sequences(self):
        """Test sequences with both strings and objects."""
        data = {
            "command": ["/bin/sh", "-c", "echo hello"],
            "volumes": [
                {"name": "data", "path": "/data"},
                {"name": "logs", "path": "/logs"},
            ],
        }
        result = dumps(data)

        # Command should be inline
        assert "  - /bin/sh\n  - -c\n  - echo hello" in result

        # Volumes should be multiline
        assert "volumes:\n  -\n    name: data" in result

    def test_nested_sequences(self):
        """Test sequences within sequences."""
        data = {"matrix": [["a", "b", "c"], ["d", "e", "f"]]}
        result = dumps(data)

        # Outer sequence should be multiline (contains arrays)
        # Inner sequences should be inline (contain strings)
        assert "matrix:\n  -\n    - a\n    - b\n    - c" in result

    def test_empty_structures(self):
        """Test handling of empty dictionaries and lists."""
        data = {"resources": {}, "empty_list": [], "populated": {"key": "value"}}
        result = dumps(data)

        # Empty dict should be inline
        assert "resources: {}" in result
        # Empty list should be inline
        assert "empty_list: []" in result

    def test_empty_containers_in_sequences(self):
        """Test that empty containers in sequences are formatted inline with dash."""
        data = {
            "egress": [{}],
            "mixed": [[], {}, "scalar"],
            "networkPolicy": {"ingress": [{"from": [{"podSelector": {}}]}]},
        }
        result = dumps(data)

        # Empty object in sequence should be inline
        assert "egress:\n  - {}" in result
        # Mixed sequence should have all empty containers inline
        assert "mixed:\n  - []\n  - {}\n  - scalar" in result
        # Nested empty object should be inline
        assert "podSelector: {}" in result

    def test_indentation_consistency(self):
        """Test that indentation is consistent throughout."""
        data = {
            "spec": {
                "containers": [
                    {
                        "name": "test",
                        "envFrom": [
                            {"configMapRef": {"name": "config1"}},
                            {"secretRef": {"name": "secret1"}},
                        ],
                    }
                ]
            }
        }
        result = dumps(data, indent=2)
        lines = result.split("\n")

        # Check indentation levels
        container_dash_line = next(
            i
            for i, line in enumerate(lines)
            if line.strip() == "-" and "containers:" in lines[i - 1]
        )
        container_content_line = container_dash_line + 1

        # Dash should be indented under containers
        assert lines[container_dash_line].startswith("    -")
        # Content should be indented under dash
        assert lines[container_content_line].startswith("      ")


class TestKeyOrdering:
    """Test the priority key ordering functionality."""

    def test_priority_keys_first(self):
        """Test that priority keys appear first in output."""
        data = {
            "volumeMounts": [{"path": "/data"}],
            "name": "test-container",
            "resources": {"limits": {"cpu": "100m"}},
            "image": "nginx:latest",
            "ports": [{"containerPort": 80}],
            "imagePullPolicy": "Always",
        }
        result = dumps(data)
        lines = [line.strip() for line in result.split("\n") if ":" in line]

        # Find the order of keys
        key_order = []
        for line in lines:
            if (
                ":" in line
                and not line.startswith("-")
                and (": " in line or line.endswith(":"))
            ):
                key = line.split(":")[0].strip()
                if key not in key_order:
                    key_order.append(key)

        # Priority keys should come first
        priority_keys_found = [
            k for k in key_order if k in HumanFriendlyDumper.PRIORITY_KEYS
        ]
        assert priority_keys_found == ["name", "image", "imagePullPolicy"]

        # name, image, imagePullPolicy should come before resources, ports, volumeMounts
        name_idx = key_order.index("name")
        image_idx = key_order.index("image")
        policy_idx = key_order.index("imagePullPolicy")
        resources_idx = key_order.index("resources")

        assert name_idx < resources_idx
        assert image_idx < resources_idx
        assert policy_idx < resources_idx

    def test_non_priority_keys_preserved_order(self):
        """Test that non-priority keys maintain their original order."""
        data = {"zebra": "last", "alpha": "first", "name": "priority", "beta": "second"}
        result = dumps(data)
        lines = [
            line.strip()
            for line in result.split("\n")
            if ":" in line and not line.startswith("-")
        ]

        # name should be first (priority)
        assert lines[0].startswith("name:")
        # Other keys should maintain relative order: zebra, alpha, beta
        remaining_lines = [line for line in lines if not line.startswith("name:")]
        assert remaining_lines[0].startswith("zebra:")
        assert remaining_lines[1].startswith("alpha:")
        assert remaining_lines[2].startswith("beta:")


class TestYAMLValidity:
    """Test that generated YAML is syntactically valid."""

    def test_round_trip_simple(self):
        """Test that simple structures can be loaded back."""
        original = {
            "strings": ["a", "b", "c"],
            "number": 42,
            "nested": {"key": "value"},
        }

        yaml_str = dumps(original)
        parsed = yaml.safe_load(yaml_str)

        assert parsed == original

    def test_round_trip_complex(self):
        """Test that complex structures can be loaded back."""
        original = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "test-pod", "labels": {"app": "test"}},
            "spec": {
                "containers": [
                    {
                        "name": "web",
                        "image": "nginx:latest",
                        "command": ["/bin/sh", "-c"],
                        "env": [
                            {"name": "VAR1", "value": "val1"},
                            {"name": "VAR2", "value": "val2"},
                        ],
                        "resources": {},
                    }
                ]
            },
        }

        yaml_str = dumps(original)
        parsed = yaml.safe_load(yaml_str)

        assert parsed == original

    def test_special_characters(self):
        """Test handling of special characters in YAML."""
        original = {
            "command": ['echo "hello world"', "cat /etc/passwd"],
            "multiline": "line1\nline2\nline3",
            "special": "value with: colon and - dash",
        }

        yaml_str = dumps(original)
        parsed = yaml.safe_load(yaml_str)

        assert parsed == original


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_non_dict_mappings(self):
        """Test that non-dict mappings are handled correctly."""

        # Create a custom mapping-like object
        class CustomMapping:
            def __init__(self, data):
                self.data = data

            def items(self):
                return self.data.items()

            def __iter__(self):
                return iter(self.data)

        # This should not crash and should use default behavior
        dumper = HumanFriendlyDumper(StringIO())
        custom_map = CustomMapping({"key": "value"})

        # Should not raise an exception
        result = dumper.represent_mapping("tag:yaml.org,2002:map", custom_map)
        assert result is not None

    def test_empty_data(self):
        """Test handling of empty data structures."""
        test_cases = [{}, [], "", None]

        for data in test_cases:
            yaml_str = dumps(data)
            parsed = yaml.safe_load(yaml_str)
            assert parsed == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
