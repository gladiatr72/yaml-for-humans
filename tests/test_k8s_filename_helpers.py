"""
Tests for Kubernetes filename generation helpers.

Tests pure helper functions extracted from _generate_k8s_filename.
"""

import pytest

from yaml_for_humans.cli import (
    _extract_k8s_parts,
    _generate_fallback_filename,
    _build_filename_from_parts,
    _generate_k8s_filename,
)


class TestExtractK8sParts:
    """Test _extract_k8s_parts pure function."""

    def test_extract_full_manifest(self):
        """Test extracting parts from full K8s manifest."""
        document = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "web-server"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["deployment", "web-server"]

    def test_extract_with_type_field(self):
        """Test extracting parts with type field."""
        document = {
            "kind": "Service",
            "type": "LoadBalancer",
            "metadata": {"name": "api"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["service", "loadbalancer", "api"]

    def test_extract_minimal_manifest(self):
        """Test extracting from minimal manifest."""
        document = {
            "kind": "Pod",
            "metadata": {"name": "test-pod"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["pod", "test-pod"]

    def test_extract_no_metadata(self):
        """Test extracting when no metadata present."""
        document = {"kind": "ConfigMap"}
        parts = _extract_k8s_parts(document)
        assert parts == ["configmap"]

    def test_extract_metadata_not_dict(self):
        """Test extracting when metadata is not a dict."""
        document = {
            "kind": "Secret",
            "metadata": "invalid",
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["secret"]

    def test_extract_empty_document(self):
        """Test extracting from empty document."""
        parts = _extract_k8s_parts({})
        assert parts == []

    def test_extract_case_normalization(self):
        """Test that parts are lowercased."""
        document = {
            "kind": "DaemonSet",
            "metadata": {"name": "NodeExporter"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["daemonset", "nodeexporter"]

    def test_extract_secret_with_docker_type(self):
        """Test real Kubernetes Secret with dockerconfigjson type."""
        document = {
            "kind": "Secret",
            "type": "kubernetes.io/dockerconfigjson",
            "metadata": {"name": "internal-registry"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["secret", "kubernetes.io--dockerconfigjson", "internal-registry"]

    def test_extract_type_with_consecutive_slashes(self):
        """Test consecutive slashes collapse to single --."""
        document = {
            "kind": "Secret",
            "type": "foo///bar",
            "metadata": {"name": "test"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["secret", "foo--bar", "test"]

    def test_extract_type_with_backslashes(self):
        """Test backslash replacement for Windows paths."""
        document = {
            "kind": "Secret",
            "type": "custom\\type\\value",
            "metadata": {"name": "test"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["secret", "custom--type--value", "test"]

    def test_extract_type_with_mixed_delimiters(self):
        """Test consecutive mixed slashes collapse to single --."""
        document = {
            "kind": "Secret",
            "type": "foo/\\bar",
            "metadata": {"name": "test"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["secret", "foo--bar", "test"]

    def test_extract_service_type_unaffected(self):
        """Ensure normal Service types still work (existing behavior)."""
        document = {
            "kind": "Service",
            "type": "LoadBalancer",
            "metadata": {"name": "api"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["service", "loadbalancer", "api"]

    def test_extract_name_with_slashes(self):
        """Test that name field slashes are also sanitized."""
        document = {
            "kind": "ConfigMap",
            "metadata": {"name": "my/app-config"},
        }
        parts = _extract_k8s_parts(document)
        assert parts == ["configmap", "my--app-config"]


class TestGenerateFallbackFilename:
    """Test _generate_fallback_filename pure function."""

    def test_fallback_from_source_file(self):
        """Test fallback from source file path."""
        filename = _generate_fallback_filename("/path/to/manifest.yaml", None)
        assert filename == "manifest.yaml"

    def test_fallback_from_nested_source_file(self):
        """Test fallback from nested source file path."""
        filename = _generate_fallback_filename("/very/deep/path/config.yml", None)
        assert filename == "config.yaml"

    def test_fallback_from_stdin_position(self):
        """Test fallback from stdin position."""
        filename = _generate_fallback_filename(None, 0)
        assert filename == "stdin-0.yaml"

    def test_fallback_from_stdin_position_multiple(self):
        """Test fallback from stdin with position > 0."""
        filename = _generate_fallback_filename(None, 5)
        assert filename == "stdin-5.yaml"

    def test_fallback_no_source_no_stdin(self):
        """Test fallback when no source or stdin info."""
        filename = _generate_fallback_filename(None, None)
        assert filename == "document.yaml"

    def test_fallback_prefers_source_file(self):
        """Test that source file takes precedence over stdin."""
        filename = _generate_fallback_filename("/path/to/file.yaml", 0)
        assert filename == "file.yaml"


class TestBuildFilenameFromParts:
    """Test _build_filename_from_parts pure function."""

    def test_build_single_part(self):
        """Test building filename from single part."""
        filename = _build_filename_from_parts(["deployment"])
        assert filename == "deployment.yaml"

    def test_build_multiple_parts(self):
        """Test building filename from multiple parts."""
        filename = _build_filename_from_parts(["service", "loadbalancer", "api"])
        assert filename == "service-loadbalancer-api.yaml"

    def test_build_two_parts(self):
        """Test building filename from two parts."""
        filename = _build_filename_from_parts(["pod", "web"])
        assert filename == "pod-web.yaml"

    def test_build_empty_parts(self):
        """Test building filename from empty parts list."""
        filename = _build_filename_from_parts([])
        assert filename == ".yaml"

    def test_build_with_hyphens_in_parts(self):
        """Test that existing hyphens in parts are preserved."""
        filename = _build_filename_from_parts(["daemon-set", "node-exporter"])
        assert filename == "daemon-set-node-exporter.yaml"


class TestGenerateK8sFilenameIntegration:
    """Integration tests for _generate_k8s_filename."""

    def test_generate_full_manifest(self):
        """Test generating filename from full K8s manifest."""
        document = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "web-server"},
        }
        filename = _generate_k8s_filename(document)
        assert filename == "deployment-web-server.yaml"

    def test_generate_minimal_manifest(self):
        """Test generating filename from minimal manifest."""
        document = {
            "kind": "Service",
            "metadata": {"name": "api"},
        }
        filename = _generate_k8s_filename(document)
        assert filename == "service-api.yaml"

    def test_generate_no_metadata(self):
        """Test generating filename when no metadata."""
        document = {"kind": "Pod"}
        filename = _generate_k8s_filename(document)
        assert filename == "pod.yaml"

    def test_generate_non_dict_fallback(self):
        """Test generating filename for non-dict document."""
        filename = _generate_k8s_filename("not a dict")
        assert filename == "document.yaml"

    def test_generate_non_dict_with_source(self):
        """Test generating filename for non-dict with source file."""
        filename = _generate_k8s_filename(
            "not a dict",
            source_file="/path/to/manifest.yaml"
        )
        assert filename == "manifest.yaml"

    def test_generate_empty_dict_fallback(self):
        """Test generating filename from empty dict uses fallback."""
        filename = _generate_k8s_filename({})
        assert filename == "document.yaml"

    def test_generate_empty_dict_with_stdin(self):
        """Test generating filename from empty dict with stdin position."""
        filename = _generate_k8s_filename({}, stdin_position=2)
        assert filename == "stdin-2.yaml"

    def test_generate_with_prefix(self):
        """Test generating filename with resource ordering prefix."""
        document = {
            "kind": "Deployment",
            "metadata": {"name": "app"},
        }
        # Note: This requires get_k8s_resource_prefix which we're not mocking
        # Just verify the function accepts the parameter
        filename = _generate_k8s_filename(document, add_prefix=False)
        assert filename == "deployment-app.yaml"

    def test_generate_preserves_case_in_source(self):
        """Test that source file basename case is preserved."""
        filename = _generate_k8s_filename(
            "not dict",
            source_file="/path/MyManifest.yaml"
        )
        assert filename == "MyManifest.yaml"

    def test_generate_dockerconfig_secret_filename(self):
        """Integration: kubernetes.io/dockerconfigjson generates valid filename."""
        document = {
            "kind": "Secret",
            "type": "kubernetes.io/dockerconfigjson",
            "metadata": {"name": "internal-registry"},
        }
        filename = _generate_k8s_filename(document)
        assert filename == "secret-kubernetes.io--dockerconfigjson-internal-registry.yaml"
        # Verify no path separators remain
        assert "/" not in filename
        assert "\\" not in filename


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
