"""
Test CLI empty line preservation functionality.
"""

import subprocess
import sys
import pytest


class TestCLIEmptyLines:
    """Test CLI empty line preservation features."""

    def test_cli_does_not_preserve_empty_lines_by_default(self):
        """Test that CLI does not preserve empty lines by default."""
        yaml_input = "key1: value1\n\nkey2: value2\n\n\nkey3: value3"
        
        # Run the CLI with the input
        result = subprocess.run(
            [sys.executable, "-m", "yaml_for_humans.cli"],
            input=yaml_input,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
        
        # Should NOT preserve empty lines by default
        expected_lines = [
            'key1: value1',
            'key2: value2',
            'key3: value3'
        ]
        
        actual_lines = result.stdout.strip().split('\n')
        assert actual_lines == expected_lines

    def test_cli_can_preserve_empty_lines_with_P_flag(self):
        """Test that CLI can preserve empty lines with -P flag."""
        yaml_input = "key1: value1\n\nkey2: value2\n\n\nkey3: value3"
        
        # Run the CLI with -P flag
        result = subprocess.run(
            [sys.executable, "-m", "yaml_for_humans.cli", "-P"],
            input=yaml_input,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
        
        # Should preserve empty lines
        expected_lines = [
            'key1: value1',
            '',
            'key2: value2', 
            '',
            '',
            'key3: value3'
        ]
        
        actual_lines = result.stdout.strip().split('\n')
        assert actual_lines == expected_lines

    def test_cli_preserves_empty_lines_with_file_input_and_P_flag(self, tmp_path):
        """Test that CLI preserves empty lines when processing files with -P flag."""
        # Create a test file with empty lines
        test_file = tmp_path / "test.yaml"
        test_file.write_text("apiVersion: v1\nkind: Pod\n\nmetadata:\n  name: test")
        
        # Run the CLI with --inputs flag and -P flag
        result = subprocess.run(
            [sys.executable, "-m", "yaml_for_humans.cli", "-P", "--inputs", str(test_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
        
        # Should preserve the empty line after "kind: Pod"
        assert 'kind: Pod\n\nmetadata:' in result.stdout

    def test_cli_help_includes_preserve_empty_lines_option(self):
        """Test that CLI help includes the new preserve-empty-lines option."""
        result = subprocess.run(
            [sys.executable, "-m", "yaml_for_humans.cli", "--help"],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0
        assert "-P, --preserve-empty-lines" in result.stdout or "--preserve-empty-lines" in result.stdout
        assert "Preserve empty lines" in result.stdout

    def test_cli_with_json_input_still_works(self):
        """Test that CLI still works correctly with JSON input."""
        json_input = '{"key1": "value1", "key2": "value2"}'
        
        result = subprocess.run(
            [sys.executable, "-m", "yaml_for_humans.cli"],
            input=json_input,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0, f"CLI failed with stderr: {result.stderr}"
        
        # JSON input should still work normally
        assert 'key1: value1' in result.stdout
        assert 'key2: value2' in result.stdout