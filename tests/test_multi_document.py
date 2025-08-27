"""
Tests for multi-document YAML functionality.

Tests the MultiDocumentDumper, KubernetesManifestDumper,
and all related convenience functions.
"""

import os
import tempfile

import pytest
import yaml

from yaml_for_humans.multi_document import (
    KubernetesManifestDumper,
    MultiDocumentDumper,
    dump_all,
    dumps_all,
    dumps_kubernetes_manifests,
)


class TestMultiDocumentDumper:
    """Test the MultiDocumentDumper class."""

    def test_single_document(self):
        """Test dumping a single document."""
        document = {"key": "value", "list": ["item1", "item2"]}
        dumper = MultiDocumentDumper()
        dumper.dump_document(document)
        result = dumper.getvalue()

        assert "---" not in result  # Single document should not have separator
        assert "key: value" in result
        assert "  - item1\n  - item2" in result  # Human-friendly formatting

        # Should be valid YAML
        parsed = list(yaml.safe_load_all(result))
        assert len(parsed) == 1
        assert parsed[0] == document

    def test_multiple_documents(self):
        """Test dumping multiple documents."""
        documents = [
            {"doc": 1, "items": ["a", "b"]},
            {"doc": 2, "nested": {"key": "value"}},
            {"doc": 3, "empty_dict": {}},
        ]

        dumper = MultiDocumentDumper()
        dumper.dump_all(documents)
        result = dumper.getvalue()

        # Should have document separators between docs (3 docs = 2 separators)
        separator_count = result.count("---")
        assert separator_count == 2

        # Should have proper spacing between documents
        lines = result.split("\n")
        separator_lines = [i for i, line in enumerate(lines) if line.strip() == "---"]

        # Check spacing between separators
        for i in range(1, len(separator_lines)):
            curr_sep = separator_lines[i]
            # There should be at least one blank line before each separator (except first)
            assert lines[curr_sep - 1].strip() == ""

        # Should be valid multi-document YAML
        parsed = list(yaml.safe_load_all(result))
        assert len(parsed) == 3
        assert parsed == documents

    def test_human_friendly_formatting(self):
        """Test that human-friendly formatting is preserved."""
        documents = [
            {
                "containers": [
                    {
                        "ports": [8080, 9090],
                        "name": "web",  # Should appear first due to priority
                        "image": "nginx",
                        "command": ["nginx", "-g", "daemon off;"],  # Strings inline
                    }
                ]
            }
        ]

        result = dumps_all(documents)

        # Check priority key ordering
        assert "name: web" in result
        container_text = result[result.find("containers:") :]
        name_pos = container_text.find("name:")
        ports_pos = container_text.find("ports:")
        assert name_pos < ports_pos  # name should come before ports

        # Check string sequence formatting
        assert "      - nginx\n      - -g\n      - daemon off;" in result

        # Check object sequence formatting
        assert "containers:\n  -\n    name: web" in result


class TestConvenienceFunctions:
    """Test the convenience functions for multi-document dumping."""

    def test_dumps_all(self):
        """Test dumps_all function."""
        documents = [
            {"type": "config", "data": {"key": "value"}},
            {"type": "service", "ports": [80, 443]},
        ]

        result = dumps_all(documents)

        assert "---" in result
        assert result.count("---") == 1  # 2 documents = 1 separator
        assert "type: config" in result
        assert "type: service" in result
        assert "  - 80\n  - 443" in result  # String sequences inline

        # Validate
        parsed = list(yaml.safe_load_all(result))
        assert parsed == documents

    def test_dump_all_to_file(self):
        """Test dump_all function with file output."""
        documents = [{"doc1": {"items": ["a", "b"]}}, {"doc2": {"value": 42}}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name
            dump_all(documents, f)

        try:
            # Read back and verify
            with open(temp_path, "r") as f:
                content = f.read()
                parsed = list(yaml.safe_load_all(content))

            assert parsed == documents
            assert content.count("---") == 1  # 2 documents = 1 separator

        finally:
            os.unlink(temp_path)

    def test_custom_dumper_options(self):
        """Test custom dumper options are respected."""
        documents = [{"test": ["item1", "item2"]}, {"number": 42}]

        # Test with explicit_end=True
        result = dumps_all(documents, explicit_end=True)
        assert "..." in result  # Should have document end markers

        # Test with custom indent
        result = dumps_all(documents, indent=4)
        assert "    - item1" in result  # Should use 4-space indent


class TestKubernetesManifestDumper:
    """Test the Kubernetes-specific manifest dumper."""

    def test_resource_ordering(self):
        """Test that Kubernetes resources are ordered correctly."""
        manifests = [
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": "app"},
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": "app-service"},
            },
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "app-config"},
            },
            {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": "app-ns"}},
        ]

        result = dumps_kubernetes_manifests(manifests)

        # Parse documents to check order
        parsed = list(yaml.safe_load_all(result))
        kinds = [doc["kind"] for doc in parsed]

        # Should be ordered: Namespace, ConfigMap, Service, Deployment
        expected_order = ["Namespace", "ConfigMap", "Service", "Deployment"]
        assert kinds == expected_order

    def test_unknown_resources(self):
        """Test handling of unknown Kubernetes resource types."""
        manifests = [
            {
                "apiVersion": "custom/v1",
                "kind": "CustomResource",
                "metadata": {"name": "custom"},
            },
            {"apiVersion": "v1", "kind": "Service", "metadata": {"name": "service"}},
            {
                "apiVersion": "unknown/v1",
                "kind": "UnknownType",
                "metadata": {"name": "unknown"},
            },
        ]

        result = dumps_kubernetes_manifests(manifests)
        parsed = list(yaml.safe_load_all(result))
        kinds = [doc["kind"] for doc in parsed]

        # Service should come first (known), unknown resources should come after
        assert kinds[0] == "Service"
        assert "CustomResource" in kinds[1:]
        assert "UnknownType" in kinds[1:]

    def test_disable_resource_ordering(self):
        """Test disabling resource ordering."""
        manifests = [
            {"kind": "Deployment", "metadata": {"name": "app"}},
            {"kind": "Service", "metadata": {"name": "service"}},
            {"kind": "ConfigMap", "metadata": {"name": "config"}},
        ]

        dumper = KubernetesManifestDumper(sort_resources=False)
        dumper.dump_all(manifests)
        result = dumper.getvalue()

        parsed = list(yaml.safe_load_all(result))
        kinds = [doc["kind"] for doc in parsed]

        # Should maintain original order
        assert kinds == ["Deployment", "Service", "ConfigMap"]

    def test_kubernetes_formatting(self):
        """Test Kubernetes manifest formatting with containers."""
        manifests = [
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "ports": [{"containerPort": 80}],
                                    "name": "nginx",  # Should appear first
                                    "image": "nginx:latest",
                                    "command": [
                                        "/bin/sh",
                                        "-c",
                                        'nginx -g "daemon off;"',
                                    ],
                                }
                            ]
                        }
                    }
                },
            }
        ]

        result = dumps_kubernetes_manifests(manifests)

        # Check priority key ordering
        assert "name: nginx" in result
        container_section = result[result.find("containers:") :]
        name_pos = container_section.find("name:")
        ports_pos = container_section.find("ports:")
        assert name_pos < ports_pos

        # Check human-friendly formatting
        assert "containers:\n        -\n          name: nginx" in result
        assert "            - /bin/sh\n            - -c" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_document_list(self):
        """Test handling of empty document list."""
        result = dumps_all([])
        assert result.strip() == ""  # Should produce empty output

    def test_single_none_document(self):
        """Test handling of None document."""
        result = dumps_all([None])
        parsed = list(yaml.safe_load_all(result))
        assert parsed == [None]

    def test_mixed_document_types(self):
        """Test mixing different document types."""
        documents = [
            {"dict": "document"},
            ["list", "document"],
            "string document",
            42,
            None,
            True,
        ]

        result = dumps_all(documents)
        parsed = list(yaml.safe_load_all(result))
        assert parsed == documents

    def test_very_large_document_list(self):
        """Test performance with many documents."""
        documents = [{"doc": i, "data": f"value-{i}"} for i in range(100)]

        result = dumps_all(documents)
        parsed = list(yaml.safe_load_all(result))

        assert len(parsed) == 100
        assert parsed == documents
        assert result.count("---") == 99  # 100 documents = 99 separators

    def test_getvalue_with_file_stream(self):
        """Test error when calling getvalue on non-StringIO stream."""
        with tempfile.NamedTemporaryFile(mode="w") as f:
            dumper = MultiDocumentDumper(f)
            with pytest.raises(ValueError, match="does not support getvalue"):
                dumper.getvalue()


class TestDocumentSeparation:
    """Test document separation and formatting."""

    def test_document_separators(self):
        """Test proper document separator placement."""
        documents = [
            {"first": "document"},
            {"second": "document"},
            {"third": "document"},
        ]

        result = dumps_all(documents)
        lines = result.split("\n")

        # Find all separator lines
        separators = [
            (i, line) for i, line in enumerate(lines) if line.strip() == "---"
        ]
        assert len(separators) == 2  # 3 documents = 2 separators

        # First separator should not be at the beginning (separators are between docs)
        first_sep_line = separators[0][0]
        assert first_sep_line > 0  # Not at the very beginning

        # Subsequent separators should have blank lines before them
        for i in range(1, len(separators)):
            sep_line = separators[i][0]
            assert lines[sep_line - 1].strip() == ""

    def test_explicit_end_markers(self):
        """Test explicit document end markers."""
        documents = [{"doc": 1}, {"doc": 2}]

        result = dumps_all(documents, explicit_end=True)
        assert result.count("...") == 2

        # Should still be valid YAML
        parsed = list(yaml.safe_load_all(result))
        assert parsed == documents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
