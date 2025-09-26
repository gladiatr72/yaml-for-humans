"""
Tests for comment preservation functionality.

This module tests the new comment preservation feature that allows
yaml-for-humans to maintain comments from the original YAML when
reformatting, following the rule that comments are associated with
the next non-comment, non-blank line.
"""

import pytest
from yaml_for_humans import load_with_formatting, dumps
from yaml_for_humans.formatting_aware import FormattingAwareDict, CommentMetadata


class TestCommentPreservation:
    """Test comment preservation functionality."""

    def test_simple_comment_preservation(self):
        """Test basic comment preservation before keys."""
        yaml_content = """# Configuration file
key1: value1
# Important setting
key2: value2"""

        # Load with formatting metadata
        data = load_with_formatting(yaml_content)

        # Verify we got a FormattingAwareDict
        assert isinstance(data, FormattingAwareDict)

        # Check comment metadata - comments should be associated with next content
        key1_comments = data._get_key_comments('key1')
        assert len(key1_comments.comments_before) == 1
        assert key1_comments.comments_before[0] == "# Configuration file"

        key2_comments = data._get_key_comments('key2')
        assert len(key2_comments.comments_before) == 1
        assert key2_comments.comments_before[0] == "# Important setting"

        # Test preservation
        preserved = dumps(data, preserve_comments=True)

        # Should preserve comments
        assert "# Configuration file" in preserved
        assert "# Important setting" in preserved
        assert preserved.index("# Configuration file") < preserved.index("key1: value1")
        assert preserved.index("# Important setting") < preserved.index("key2: value2")

        # Test without preservation
        normal = dumps(data, preserve_comments=False)

        # Should not have comments
        assert "# Configuration file" not in normal
        assert "# Important setting" not in normal

    def test_multiple_comments_before_content(self):
        """Test multiple comments before a single content line."""
        yaml_content = """# First comment
# Second comment
# Third comment
key: value"""

        data = load_with_formatting(yaml_content)

        # All comments should be associated with the key
        key_comments = data._get_key_comments('key')
        assert len(key_comments.comments_before) == 3
        assert key_comments.comments_before[0] == "# First comment"
        assert key_comments.comments_before[1] == "# Second comment"
        assert key_comments.comments_before[2] == "# Third comment"

        # Test preservation maintains order
        preserved = dumps(data, preserve_comments=True)
        lines = preserved.strip().split('\n')

        expected_lines = [
            "# First comment",
            "# Second comment",
            "# Third comment",
            "key: value"
        ]
        assert lines == expected_lines

    def test_comments_with_empty_lines(self):
        """Test comments separated by empty lines."""
        yaml_content = """# Comment 1

# Comment 2
key1: value1

# Comment 3

key2: value2"""

        data = load_with_formatting(yaml_content)

        # Comments should be associated according to the rule:
        # Comments are associated with next non-comment, non-blank line
        key1_comments = data._get_key_comments('key1')
        assert len(key1_comments.comments_before) == 2
        assert key1_comments.comments_before[0] == "# Comment 1"
        assert key1_comments.comments_before[1] == "# Comment 2"

        key2_comments = data._get_key_comments('key2')
        assert len(key2_comments.comments_before) == 1
        assert key2_comments.comments_before[0] == "# Comment 3"

    def test_complex_yaml_comment_preservation(self):
        """Test comment preservation with complex YAML structures."""
        yaml_content = """# API Configuration
apiVersion: v1
kind: ConfigMap

# Metadata section
metadata:
  name: test-config
  namespace: default

# Data section
data:
  # Database settings
  database_url: postgresql://localhost
  # Cache settings
  cache_ttl: 3600"""

        data = load_with_formatting(yaml_content)

        # Check top-level comments
        api_comments = data._get_key_comments('apiVersion')
        assert len(api_comments.comments_before) == 1
        assert api_comments.comments_before[0] == "# API Configuration"

        metadata_comments = data._get_key_comments('metadata')
        assert len(metadata_comments.comments_before) == 1
        assert metadata_comments.comments_before[0] == "# Metadata section"

        data_comments = data._get_key_comments('data')
        assert len(data_comments.comments_before) == 1
        assert data_comments.comments_before[0] == "# Data section"

        # Check nested comments in data section
        assert isinstance(data['data'], FormattingAwareDict)
        database_comments = data['data']._get_key_comments('database_url')
        assert len(database_comments.comments_before) == 1
        assert database_comments.comments_before[0] == "# Database settings"

        cache_comments = data['data']._get_key_comments('cache_ttl')
        assert len(cache_comments.comments_before) == 1
        assert cache_comments.comments_before[0] == "# Cache settings"

    def test_comment_preservation_with_lists(self):
        """Test comment preservation with YAML lists."""
        yaml_content = """# List of items
items:
  # First item
  - item1
  # Second item
  - item2
  # Third item
  - item3"""

        data = load_with_formatting(yaml_content)

        # Check top-level comment
        items_comments = data._get_key_comments('items')
        assert len(items_comments.comments_before) == 1
        assert items_comments.comments_before[0] == "# List of items"

        # Check list item comments
        from yaml_for_humans.formatting_aware import FormattingAwareList
        assert isinstance(data['items'], FormattingAwareList)

        item1_comments = data['items']._get_item_comments(0)
        assert len(item1_comments.comments_before) == 1
        assert item1_comments.comments_before[0] == "# First item"

        item2_comments = data['items']._get_item_comments(1)
        assert len(item2_comments.comments_before) == 1
        assert item2_comments.comments_before[0] == "# Second item"

        item3_comments = data['items']._get_item_comments(2)
        assert len(item3_comments.comments_before) == 1
        assert item3_comments.comments_before[0] == "# Third item"

    def test_no_comments_yaml(self):
        """Test that YAML without comments works correctly."""
        yaml_content = """key1: value1
key2: value2
key3: value3"""

        data = load_with_formatting(yaml_content)

        # Check that no keys have comments
        for key in data.keys():
            comments = data._get_key_comments(key)
            assert len(comments.comments_before) == 0
            assert comments.eol_comment is None

        # Both preserved and normal should be identical
        preserved = dumps(data, preserve_comments=True)
        normal = dumps(data, preserve_comments=False)

        # Remove any potential trailing whitespace differences
        assert preserved.strip() == normal.strip()

    def test_backward_compatibility(self):
        """Test that existing functionality still works."""
        yaml_content = """key1: value1
key2: value2"""

        # Regular dumps should work without preserve_comments parameter
        result = dumps({'key1': 'value1', 'key2': 'value2'})

        # Should produce valid YAML
        assert 'key1: value1' in result
        assert 'key2: value2' in result

        # FormattingAwareDict should render normally when preserve_comments=False
        data = load_with_formatting(yaml_content)
        result = dumps(data, preserve_comments=False)

        assert 'key1: value1' in result
        assert 'key2: value2' in result

    def test_combined_empty_lines_and_comments(self):
        """Test preservation of both empty lines and comments together."""
        yaml_content = """# Header comment
key1: value1

# Comment before key2
key2: value2


# Comment before key3 with multiple empty lines
key3: value3"""

        data = load_with_formatting(yaml_content)

        # Test with both preservations enabled
        preserved = dumps(data, preserve_empty_lines=True, preserve_comments=True)

        # Should contain both comments and empty lines
        assert "# Header comment" in preserved
        assert "# Comment before key2" in preserved
        assert "# Comment before key3 with multiple empty lines" in preserved

        # Check structure is maintained
        lines = preserved.strip().split('\n')

        # Find key positions to verify structure
        key1_line = next(i for i, line in enumerate(lines) if 'key1:' in line)
        key2_line = next(i for i, line in enumerate(lines) if 'key2:' in line)
        key3_line = next(i for i, line in enumerate(lines) if 'key3:' in line)

        # Verify comments appear before their associated keys
        header_line = next(i for i, line in enumerate(lines) if '# Header comment' in line)
        comment2_line = next(i for i, line in enumerate(lines) if '# Comment before key2' in line)
        comment3_line = next(i for i, line in enumerate(lines) if '# Comment before key3' in line)

        assert header_line < key1_line
        assert comment2_line < key2_line
        assert comment3_line < key3_line

    def test_comment_metadata_object(self):
        """Test CommentMetadata class functionality."""
        # Test empty metadata
        empty_meta = CommentMetadata()
        assert not empty_meta.has_comments()
        assert empty_meta.comments_before == []
        assert empty_meta.eol_comment is None

        # Test metadata with comments
        comments_meta = CommentMetadata(
            comments_before=["# Comment 1", "# Comment 2"],
            eol_comment="# End of line comment"
        )
        assert comments_meta.has_comments()
        assert len(comments_meta.comments_before) == 2
        assert comments_meta.eol_comment == "# End of line comment"

        # Test repr
        repr_str = repr(comments_meta)
        assert "CommentMetadata" in repr_str
        assert "Comment 1" in repr_str
        assert "End of line comment" in repr_str