"""
Tests for empty line preservation functionality.

This module tests the new empty line preservation feature that allows
yaml-for-humans to maintain empty lines from the original YAML when
reformatting.
"""

import pytest
from yaml_for_humans import load_with_formatting, dumps
from yaml_for_humans.formatting_aware import FormattingAwareDict


class TestEmptyLinePreservation:
    """Test empty line preservation functionality."""

    def test_simple_empty_line_preservation(self):
        """Test basic empty line preservation between keys."""
        yaml_content = """key1: value1

key2: value2


key3: value3"""
        
        # Load with formatting metadata
        data = load_with_formatting(yaml_content)
        
        # Verify we got a FormattingAwareDict
        assert isinstance(data, FormattingAwareDict)
        
        # Check formatting metadata
        assert data._get_key_formatting('key1').empty_lines_before == 0
        assert data._get_key_formatting('key2').empty_lines_before == 1
        assert data._get_key_formatting('key3').empty_lines_before == 2
        
        # Test preservation
        preserved = dumps(data, preserve_empty_lines=True)
        preserved_lines = preserved.strip().split('\n')
        
        # Should preserve empty lines
        expected_lines = [
            'key1: value1',
            '',
            'key2: value2', 
            '',
            '',
            'key3: value3'
        ]
        
        assert preserved_lines == expected_lines
        
        # Test without preservation
        normal = dumps(data, preserve_empty_lines=False)
        normal_lines = normal.strip().split('\n')
        
        # Should not have empty lines
        expected_normal = [
            'key1: value1',
            'key2: value2',
            'key3: value3'
        ]
        
        assert normal_lines == expected_normal

    def test_complex_yaml_empty_line_preservation(self):
        """Test empty line preservation with complex YAML structures."""
        yaml_content = """apiVersion: v1
kind: ConfigMap

metadata:
  name: test-config
  namespace: default"""
        
        # Load with formatting metadata
        data = load_with_formatting(yaml_content)
        
        # Verify we got a FormattingAwareDict
        assert isinstance(data, FormattingAwareDict)
        
        # Check that metadata key has empty line before it
        assert data._get_key_formatting('metadata').empty_lines_before == 1
        
        # Test preservation
        preserved = dumps(data, preserve_empty_lines=True)
        
        # Should contain empty line before metadata
        assert '\nkind: ConfigMap\n\nmetadata:' in preserved

    def test_no_empty_lines_yaml(self):
        """Test that YAML without empty lines works correctly."""
        yaml_content = """key1: value1
key2: value2
key3: value3"""
        
        # Load with formatting metadata
        data = load_with_formatting(yaml_content)
        
        # Check that no keys have empty lines before them
        for key in data.keys():
            assert data._get_key_formatting(key).empty_lines_before == 0
        
        # Both preserved and normal should be identical
        preserved = dumps(data, preserve_empty_lines=True)
        normal = dumps(data, preserve_empty_lines=False)
        
        # Remove any potential trailing whitespace differences
        assert preserved.strip() == normal.strip()

    def test_empty_line_count_accuracy(self):
        """Test that empty line counts are accurate."""
        test_cases = [
            ("key1: value1\n\nkey2: value2", 1),  # One empty line
            ("key1: value1\n\n\nkey2: value2", 2),  # Two empty lines  
            ("key1: value1\n\n\n\nkey2: value2", 3),  # Three empty lines
            ("key1: value1\nkey2: value2", 0),  # No empty lines
        ]
        
        for yaml_content, expected_empty_lines in test_cases:
            data = load_with_formatting(yaml_content)
            actual_empty_lines = data._get_key_formatting('key2').empty_lines_before
            assert actual_empty_lines == expected_empty_lines, \
                f"Expected {expected_empty_lines} empty lines, got {actual_empty_lines}"

    def test_backward_compatibility(self):
        """Test that existing functionality still works."""
        yaml_content = """key1: value1
key2: value2"""
        
        # Regular dumps should work without preserve_empty_lines parameter
        result = dumps({'key1': 'value1', 'key2': 'value2'})
        
        # Should produce valid YAML
        assert 'key1: value1' in result
        assert 'key2: value2' in result
        
        # FormattingAwareDict should render normally when preserve_empty_lines=False
        data = load_with_formatting(yaml_content)
        result = dumps(data, preserve_empty_lines=False)
        
        assert 'key1: value1' in result
        assert 'key2: value2' in result

    def test_load_with_formatting_file_path(self):
        """Test load_with_formatting with actual file path."""
        # Use an existing test file
        test_file = 'tests/test-data/kustomization.yaml'
        
        # Load with file path
        data = load_with_formatting(test_file)
        
        # Should be a FormattingAwareDict
        assert isinstance(data, FormattingAwareDict)
        
        # Should have 'resources' key with empty line before it
        assert 'resources' in data
        assert data._get_key_formatting('resources').empty_lines_before == 1