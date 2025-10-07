"""
Tests for dumper helper functions.

Tests pure helper functions extracted from complex marker processing logic.
"""

import pytest

from yaml_for_humans.dumper import (
    _expand_content_marker,
    _expand_empty_marker,
    _expand_inline_comment,
    _process_single_line,
    _process_content_line_markers,
)


class TestExpandContentMarker:
    """Test _expand_content_marker pure function."""

    def test_expand_with_empty_lines(self):
        """Test expanding content marker with empty lines."""
        markers = {"abc123": ["", "", "# comment"]}
        result = _expand_content_marker("abc123", markers)
        assert result == ["", "", "# comment"]

    def test_expand_with_comments_only(self):
        """Test expanding content marker with only comments."""
        markers = {"def456": ["# comment 1", "# comment 2"]}
        result = _expand_content_marker("def456", markers)
        assert result == ["# comment 1", "# comment 2"]

    def test_expand_missing_hash(self):
        """Test expanding with hash not in markers returns empty list."""
        markers = {"abc123": ["content"]}
        result = _expand_content_marker("missing", markers)
        assert result == []

    def test_expand_empty_markers_dict(self):
        """Test expanding with empty markers dict."""
        result = _expand_content_marker("any", {})
        assert result == []

    def test_expand_mixed_content(self):
        """Test expanding with mixed empty lines and comments."""
        markers = {"xyz789": ["", "# comment", "", "# another"]}
        result = _expand_content_marker("xyz789", markers)
        assert result == ["", "# comment", "", "# another"]


class TestExpandEmptyMarker:
    """Test _expand_empty_marker pure function."""

    def test_expand_single_empty_line(self):
        """Test expanding single empty line."""
        result = _expand_empty_marker(1)
        assert result == [""]

    def test_expand_multiple_empty_lines(self):
        """Test expanding multiple empty lines."""
        result = _expand_empty_marker(3)
        assert result == ["", "", ""]

    def test_expand_zero_empty_lines(self):
        """Test expanding zero empty lines returns empty list."""
        result = _expand_empty_marker(0)
        assert result == []

    def test_expand_large_count(self):
        """Test expanding large number of empty lines."""
        result = _expand_empty_marker(10)
        assert len(result) == 10
        assert all(line == "" for line in result)


class TestExpandInlineComment:
    """Test _expand_inline_comment pure function."""

    def test_expand_comment_found(self):
        """Test expanding inline comment when hash found."""
        markers = {"abc123": {"comment": "# my comment"}}
        line = "key: value__INLINE_COMMENT_abc123__"
        result = _expand_inline_comment("abc123", line, markers)
        assert result == "key: value  # my comment"

    def test_expand_comment_not_found(self):
        """Test expanding inline comment when hash not found."""
        markers = {}
        line = "key: value__INLINE_COMMENT_missing__"
        result = _expand_inline_comment("missing", line, markers)
        # Should remove the marker
        assert "__INLINE_COMMENT_" not in result
        assert "key: value" in result

    def test_expand_comment_with_special_chars(self):
        """Test expanding comment with special characters."""
        markers = {"xyz789": {"comment": "# TODO: fix this!"}}
        line = "setting: true__INLINE_COMMENT_xyz789__"
        result = _expand_inline_comment("xyz789", line, markers)
        assert result == "setting: true  # TODO: fix this!"

    def test_expand_preserves_line_structure(self):
        """Test that expansion preserves indentation and structure."""
        markers = {"hash1": {"comment": "# note"}}
        line = "  nested: value__INLINE_COMMENT_hash1__"
        result = _expand_inline_comment("hash1", line, markers)
        assert result == "  nested: value  # note"


class TestProcessSingleLine:
    """Test _process_single_line pure function."""

    def test_process_content_marker_line(self):
        """Test processing line with content marker."""
        markers = {"abc": ["# comment"]}
        line = "  __CONTENT_LINES_abc__"
        result = _process_single_line(line, markers)
        assert result == ["# comment"]

    def test_process_empty_marker_line(self):
        """Test processing line with empty marker."""
        markers = {}
        line = "  __EMPTY_LINES_2__"
        result = _process_single_line(line, markers)
        assert result == ["", ""]

    def test_process_inline_comment_line(self):
        """Test processing line with inline comment marker."""
        markers = {"xyz": {"comment": "# note"}}
        line = "key: value__INLINE_COMMENT_xyz__"
        result = _process_single_line(line, markers)
        assert result == ["key: value  # note"]

    def test_process_regular_line(self):
        """Test processing line with no markers."""
        markers = {}
        line = "key: value"
        result = _process_single_line(line, markers)
        assert result == ["key: value"]

    def test_process_marker_without_match(self):
        """Test processing line with marker text but no regex match."""
        markers = {}
        line = "__CONTENT_LINES_"  # No hash
        result = _process_single_line(line, markers)
        assert result == []

    def test_process_empty_line(self):
        """Test processing empty line."""
        result = _process_single_line("", {})
        assert result == [""]


class TestProcessContentLineMarkersIntegration:
    """Integration tests for full marker processing."""

    def test_process_no_markers(self):
        """Test processing text with no markers returns unchanged."""
        text = "key: value\nitem: test"
        result = _process_content_line_markers(text, {})
        assert result == text

    def test_process_with_content_markers(self):
        """Test processing with content markers."""
        text = "before\n__CONTENT_LINES_abc__\nafter"
        markers = {"abc": ["# comment 1", "# comment 2"]}
        result = _process_content_line_markers(text, markers)
        assert result == "before\n# comment 1\n# comment 2\nafter"

    def test_process_with_empty_markers(self):
        """Test processing with empty line markers."""
        text = "section1:\n__EMPTY_LINES_2__\nsection2:"
        result = _process_content_line_markers(text, {})
        assert result == "section1:\n\n\nsection2:"

    def test_process_with_inline_comments(self):
        """Test processing with inline comment markers."""
        text = "key: value__INLINE_COMMENT_xyz__"
        markers = {"xyz": {"comment": "# important"}}
        result = _process_content_line_markers(text, markers)
        assert result == "key: value  # important"

    def test_process_mixed_markers(self):
        """Test processing with multiple marker types."""
        text = "__CONTENT_LINES_c1__\nkey: val__INLINE_COMMENT_i1__\n__EMPTY_LINES_1__"
        markers = {
            "c1": ["# header"],
            "i1": {"comment": "# note"},
        }
        result = _process_content_line_markers(text, markers)
        assert result == "# header\nkey: val  # note\n"

    def test_process_with_none_markers(self):
        """Test processing with None markers parameter."""
        text = "key: value"
        result = _process_content_line_markers(text, None)
        assert result == "key: value"

    def test_fast_path_optimization(self):
        """Test that fast path returns early when no markers present."""
        text = "key: value\nitem: test\ndata: something"
        # No markers in text, should return immediately
        result = _process_content_line_markers(text, {"unused": ["content"]})
        assert result == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
