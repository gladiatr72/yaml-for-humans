"""
Tests for file validation helper functions.

Tests pure helper functions extracted from _is_valid_file_type.
"""

import tempfile
import pytest

from yaml_for_humans.cli import (
    _has_valid_extension,
    _sample_file_content,
    _content_looks_valid,
    _is_valid_file_type,
)


class TestHasValidExtension:
    """Test _has_valid_extension pure function."""

    def test_yaml_extension(self):
        """Test .yaml extension is valid."""
        assert _has_valid_extension("file.yaml") is True
        assert _has_valid_extension("path/to/file.yaml") is True

    def test_yml_extension(self):
        """Test .yml extension is valid."""
        assert _has_valid_extension("file.yml") is True
        assert _has_valid_extension("/absolute/path/file.yml") is True

    def test_json_extension(self):
        """Test .json extension is valid."""
        assert _has_valid_extension("data.json") is True

    def test_jsonl_extension(self):
        """Test .jsonl extension is valid."""
        assert _has_valid_extension("data.jsonl") is True

    def test_invalid_extension(self):
        """Test invalid extensions return False."""
        assert _has_valid_extension("file.txt") is False
        assert _has_valid_extension("file.xml") is False
        assert _has_valid_extension("file.md") is False

    def test_no_extension(self):
        """Test file without extension returns False."""
        assert _has_valid_extension("README") is False
        assert _has_valid_extension("file") is False

    def test_case_insensitive(self):
        """Test extension check is case insensitive."""
        assert _has_valid_extension("FILE.YAML") is True
        assert _has_valid_extension("FILE.JSON") is True
        assert _has_valid_extension("File.Yml") is True


class TestSampleFileContent:
    """Test _sample_file_content I/O function."""

    def test_sample_valid_file(self):
        """Test sampling content from valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: value\nitem: test")
            f.flush()
            content = _sample_file_content(f.name)
            assert content == "key: value\nitem: test"

    def test_sample_empty_file(self):
        """Test sampling empty file returns None."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.flush()
            content = _sample_file_content(f.name)
            assert content is None

    def test_sample_whitespace_only_file(self):
        """Test sampling file with only whitespace returns None."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("   \n  \n  ")
            f.flush()
            content = _sample_file_content(f.name)
            assert content is None

    def test_sample_nonexistent_file(self):
        """Test sampling non-existent file returns None."""
        content = _sample_file_content("/nonexistent/path/file.yaml")
        assert content is None

    def test_sample_large_file_limits_to_1024(self):
        """Test that sampling limits to first 1024 characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            large_content = "x" * 2000
            f.write(large_content)
            f.flush()
            content = _sample_file_content(f.name)
            assert len(content) == 1024


class TestContentLooksValid:
    """Test _content_looks_valid pure function."""

    def test_valid_json_object(self):
        """Test JSON object content is valid."""
        assert _content_looks_valid('{"key": "value"}') is True

    def test_valid_json_array(self):
        """Test JSON array content is valid."""
        assert _content_looks_valid('["item1", "item2"]') is True

    def test_valid_yaml(self):
        """Test YAML content is valid."""
        assert _content_looks_valid("key: value") is True
        assert _content_looks_valid("- item1\n- item2") is True

    def test_yaml_with_separator(self):
        """Test YAML with document separator is valid."""
        assert _content_looks_valid("---\nkey: value") is True

    def test_invalid_content(self):
        """Test random text is invalid."""
        assert _content_looks_valid("random text without structure") is False

    def test_empty_string(self):
        """Test empty string is invalid."""
        assert _content_looks_valid("") is False


class TestIsValidFileTypeIntegration:
    """Integration tests for _is_valid_file_type."""

    def test_valid_yaml_file_with_extension(self):
        """Test valid YAML file with proper extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: value")
            f.flush()
            assert _is_valid_file_type(f.name) is True

    def test_valid_json_file_with_extension(self):
        """Test valid JSON file with proper extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"key": "value"}')
            f.flush()
            assert _is_valid_file_type(f.name) is True

    def test_empty_file_with_valid_extension(self):
        """Test empty file with valid extension is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.flush()
            assert _is_valid_file_type(f.name) is False

    def test_file_without_extension_but_valid_content(self):
        """Test file without extension but with valid YAML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write("key: value\nitem: test")
            f.flush()
            assert _is_valid_file_type(f.name) is True

    def test_file_without_extension_and_invalid_content(self):
        """Test file without extension and invalid content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='', delete=False) as f:
            f.write("random text")
            f.flush()
            assert _is_valid_file_type(f.name) is False

    def test_nonexistent_file(self):
        """Test non-existent file returns False."""
        assert _is_valid_file_type("/nonexistent/file.yaml") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
