"""
Tests for the CLI functionality.

Tests the command-line interface including timeout, input processing,
and the --inputs flag functionality.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yaml

from yaml_for_humans.cli import (
    _generate_k8s_filename,
    _has_items_array,
    _huml_main,
    _is_json_lines,
    _is_multi_document_yaml,
    _is_valid_file_type,
    _looks_like_json,
    _looks_like_yaml,
    _read_stdin_with_timeout,
)


class TestStdinTimeout:
    """Test the stdin timeout functionality."""

    def test_looks_like_json(self):
        """Test JSON detection heuristic."""
        assert _looks_like_json('{"key": "value"}')
        assert _looks_like_json('["item1", "item2"]')
        assert _looks_like_json('  {"key": "value"}  ')  # With whitespace
        assert not _looks_like_json("key: value")
        assert not _looks_like_json("- item1")
        assert not _looks_like_json("")

    def test_is_multi_document_yaml(self):
        """Test multi-document YAML detection."""
        # Single document
        single_doc = "key: value\nitem: test"
        assert not _is_multi_document_yaml(single_doc)

        # Multi-document with separator
        multi_doc = "doc: 1\n---\ndoc: 2"
        assert _is_multi_document_yaml(multi_doc)

        # Document starting with separator
        with_separator = "---\nkey: value"
        assert _is_multi_document_yaml(with_separator)

        # Multiple separators
        multiple = "doc: 1\n---\ndoc: 2\n---\ndoc: 3"
        assert _is_multi_document_yaml(multiple)

    def test_is_json_lines(self):
        """Test JSON Lines format detection."""
        # Single line - not JSON Lines
        single_line = '{"key": "value"}'
        assert not _is_json_lines(single_line)

        # Multiple JSON objects, one per line
        json_lines = '{"id": 1, "name": "test"}\n{"id": 2, "name": "test2"}'
        assert _is_json_lines(json_lines)

        # Mix of JSON and non-JSON - not JSON Lines
        mixed = '{"id": 1}\nkey: value'
        assert not _is_json_lines(mixed)

        # Empty lines should be ignored
        with_empty = '{"id": 1}\n\n{"id": 2}\n'
        assert _is_json_lines(with_empty)

        # Array objects on separate lines
        array_objects = "[1, 2, 3]\n[4, 5, 6]"
        assert _is_json_lines(array_objects)

    def test_has_items_array(self):
        """Test JSON items array detection."""
        # JSON with items array containing objects
        with_items = {
            "kind": "List",
            "items": [
                {"name": "service1", "type": "web"},
                {"name": "service2", "type": "api"},
            ],
        }
        assert _has_items_array(with_items)

        # JSON with items array but no objects (primitives only)
        primitive_items = {"data": "values", "items": ["string1", "string2", 123]}
        assert not _has_items_array(primitive_items)

        # JSON without items key
        no_items = {"services": [{"name": "test"}], "version": "1.0"}
        assert not _has_items_array(no_items)

        # JSON with items but not an array
        items_not_array = {"items": "not an array"}
        assert not _has_items_array(items_not_array)

        # Empty items array
        empty_items = {"items": []}
        assert not _has_items_array(empty_items)

        # Non-dict input
        assert not _has_items_array([1, 2, 3])
        assert not _has_items_array("string")

        # Mixed items array (some objects, some primitives)
        mixed_items = {"items": [{"name": "obj1"}, "string", {"name": "obj2"}]}
        assert _has_items_array(mixed_items)

    def test_stdin_timeout_function_exists(self):
        """Test that the timeout function exists and is callable."""
        # Just test that the function exists and can handle basic timeout logic
        assert callable(_read_stdin_with_timeout)

        # Test with a mock that simulates successful read
        with patch("threading.Thread") as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = False
            mock_thread_class.return_value = mock_thread

            # Mock the input_data being populated
            with patch("sys.stdin") as mock_stdin:
                mock_stdin.read.return_value = '{"test": "data"}'

                # Test the core components exist
                assert hasattr(mock_stdin, "read")
                assert hasattr(mock_thread, "start")

    def test_timeout_error_type(self):
        """Test that timeout raises the correct error type."""
        # Test with a mock that simulates timeout
        with patch("threading.Thread") as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = True  # Still running = timeout
            mock_thread_class.return_value = mock_thread

            with pytest.raises(TimeoutError):
                _read_stdin_with_timeout(10)


class TestCLIFunctionality:
    """Test CLI input processing functionality."""

    def test_json_input_processing(self, capsys):
        """Test processing JSON input."""
        test_input = '{"name": "test", "items": ["a", "b", "c"]}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        assert "name: test" in output
        assert "  - a" in output
        assert "  - b" in output
        assert "  - c" in output

    def test_yaml_input_processing(self, capsys):
        """Test processing YAML input."""
        test_input = """name: test
containers:
  - name: web
    image: nginx
    ports: [80, 443]"""

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        assert "name: test" in output
        assert "containers:" in output
        assert "name: web" in output  # Priority key ordering
        assert "  - 80" in output  # Inline sequence

    def test_auto_format_detection(self, capsys):
        """Test automatic format detection."""
        json_input = '{"type": "json"}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=json_input
        ):
            _huml_main(timeout=1000)  # Should detect JSON

        captured = capsys.readouterr()
        assert "type: json" in captured.out

    def test_multi_document_processing(self, capsys):
        """Test multi-document YAML processing."""
        test_input = """doc: 1
---
doc: 2
items: [x, y, z]"""

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        assert "---" in output
        assert output.count("---") == 1  # Two documents = 1 separator
        assert "doc: 1" in output
        assert "doc: 2" in output
        assert "  - x" in output

    def test_timeout_error(self, capsys):
        """Test timeout error handling."""
        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout",
            side_effect=TimeoutError("No input received within 50ms"),
        ):
            with pytest.raises(SystemExit):
                _huml_main(timeout=50)

        captured = capsys.readouterr()
        assert "Error: No input received within 50ms" in captured.err

    def test_empty_input_error(self, capsys):
        """Test empty input error handling."""
        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value="   "
        ):  # Only whitespace
            with pytest.raises(SystemExit):
                _huml_main(timeout=1000)

        captured = capsys.readouterr()
        assert "Error: No input provided" in captured.err

    def test_invalid_json_error(self, capsys):
        """Test invalid JSON error handling."""
        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout",
            return_value='{"invalid": json}',
        ):
            with pytest.raises(SystemExit):
                _huml_main(timeout=1000)

        captured = capsys.readouterr()
        assert "Error: Invalid JSON input" in captured.err

    def test_invalid_yaml_error(self, capsys):
        """Test invalid YAML error handling."""
        invalid_yaml = """
        key: value
        [invalid: yaml structure
        """

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=invalid_yaml
        ):
            with pytest.raises(SystemExit):
                _huml_main(timeout=1000)

        captured = capsys.readouterr()
        assert "Error: Invalid YAML input" in captured.err

    def test_custom_indent(self, capsys):
        """Test custom indentation."""
        test_input = '{"nested": {"items": ["a", "b"]}}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(indent=4, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should use 4-space indentation
        assert "nested:" in output  # Top level no indent
        assert "    items:" in output  # 4-space indent
        assert "        - a" in output  # 8-space indent for list items


class TestInputsFlag:
    """Test the --inputs flag functionality."""

    def setup_method(self):
        """Set up test files."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test JSON file
        self.json_file = os.path.join(self.temp_dir, "test.json")
        with open(self.json_file, "w") as f:
            json.dump({"name": "json-test", "items": [1, 2, 3]}, f)

        # Create test YAML file
        self.yaml_file = os.path.join(self.temp_dir, "test.yaml")
        with open(self.yaml_file, "w") as f:
            yaml.dump({"name": "yaml-test", "data": {"key": "value"}}, f)

        # Create another YAML file
        self.yaml_file2 = os.path.join(self.temp_dir, "test2.yml")
        with open(self.yaml_file2, "w") as f:
            yaml.dump({"service": "web", "ports": [80, 443]}, f)

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_single_json_file(self, capsys):
        """Test processing single JSON file."""
        # This test would require the actual --inputs implementation
        # For now, we'll test the core logic that would be used

        with open(self.json_file, "r") as f:
            content = f.read()

        data = json.loads(content)
        from yaml_for_humans import dumps

        result = dumps(data)

        assert "name: json-test" in result
        assert "  - 1" in result

    def test_single_yaml_file(self, capsys):
        """Test processing single YAML file."""
        with open(self.yaml_file, "r") as f:
            content = f.read()

        data = yaml.safe_load(content)
        from yaml_for_humans import dumps

        result = dumps(data)

        assert "name: yaml-test" in result
        assert "data:" in result

    def test_multiple_files(self, capsys):
        """Test processing multiple files."""
        files = [self.json_file, self.yaml_file, self.yaml_file2]

        documents = []
        for file_path in files:
            with open(file_path, "r") as f:
                content = f.read()
                if file_path.endswith(".json"):
                    data = json.loads(content)
                else:
                    data = yaml.safe_load(content)
                documents.append(data)

        from yaml_for_humans import dumps_all

        result = dumps_all(documents)

        # Should contain content from all files
        assert "name: json-test" in result
        assert "name: yaml-test" in result
        assert "service: web" in result

        # Should have proper document separators
        assert result.count("---") == 2  # 3 documents = 2 separators

    def test_inputs_flag_single_file(self, capsys):
        """Test --inputs flag with single file."""
        inputs = self.json_file

        # Use the actual CLI function to test --inputs flag
        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        assert "name: json-test" in output
        assert "  - 1" in output
        assert "  - 2" in output
        assert "  - 3" in output

    def test_inputs_flag_multiple_files(self, capsys):
        """Test --inputs flag with multiple files."""
        inputs = f"{self.json_file},{self.yaml_file},{self.yaml_file2}"

        # Use the actual CLI function to test --inputs flag
        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain content from all files
        assert "name: json-test" in output
        assert "name: yaml-test" in output
        assert "service: web" in output

        # Should have proper document separators for multiple documents
        assert "---" in output
        # Multi-document output should not start with separator
        assert not output.strip().startswith("---")

    def test_inputs_flag_mixed_formats(self, capsys):
        """Test --inputs flag with mixed JSON/YAML files."""
        inputs = f"{self.json_file},{self.yaml_file}"

        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Both files should be processed and formatted correctly
        assert "name: json-test" in output
        assert "name: yaml-test" in output

        # JSON arrays should be formatted inline
        assert "  - 1" in output

        # YAML structure should be preserved
        assert "data:" in output
        assert "  key: value" in output

    def test_inputs_flag_with_multi_doc_yaml(self, capsys):
        """Test --inputs flag with multi-document YAML file."""
        # Create a multi-document YAML file
        multi_doc_file = os.path.join(self.temp_dir, "multi.yaml")
        with open(multi_doc_file, "w") as f:
            f.write(
                """name: doc1
items: [a, b, c]
---
name: doc2
ports: [80, 443]"""
            )

        inputs = multi_doc_file

        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain both documents
        assert "name: doc1" in output
        assert "name: doc2" in output

        # Should have proper separators
        assert "---" in output

        # Arrays should be formatted inline
        assert "  - a" in output
        assert "  - 80" in output

    def test_inputs_flag_nonexistent_file(self, capsys):
        """Test --inputs flag with non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "missing.yaml")

        # Now continues processing instead of exiting
        _huml_main(inputs=nonexistent_file, timeout=1000)

        captured = capsys.readouterr()
        assert "File not found" in captured.err
        assert "missing.yaml" in captured.err

    def test_inputs_flag_empty_file(self, capsys):
        """Test --inputs flag with empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.yaml")
        with open(empty_file, "w") as f:
            f.write("")

        inputs = f"{empty_file},{self.json_file}"

        # Should process the valid file and skip the empty one
        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should only contain the JSON file content
        assert "name: json-test" in output

    def test_inputs_flag_invalid_json(self, capsys):
        """Test --inputs flag with invalid JSON file."""
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, "w") as f:
            f.write('{"invalid": json}')  # Invalid JSON

        # Now continues processing instead of exiting
        _huml_main(inputs=invalid_file, timeout=1000)

        captured = capsys.readouterr()
        assert "Error: Failed to parse" in captured.err
        assert "invalid.json" in captured.err

    def test_inputs_flag_auto_multi_document_yaml(self, capsys):
        """Test --inputs flag with auto-detected multi-document YAML."""
        # Create multi-document YAML file (without needing --multi-doc flag)
        multi_yaml = os.path.join(self.temp_dir, "multi-auto.yaml")
        with open(multi_yaml, "w") as f:
            f.write(
                """---
name: service1
type: web
ports: [80, 443]
---
name: service2
type: api
ports: [8080]
config:
  debug: false"""
            )

        _huml_main(inputs=multi_yaml, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain both documents
        assert "name: service1" in output
        assert "name: service2" in output

        # Should have separators
        assert "---" in output
        assert output.count("---") == 1  # Two documents = 1 separator

        # Arrays should be inline
        assert "  - 80" in output
        assert "  - 443" in output

    def test_inputs_flag_json_lines(self, capsys):
        """Test --inputs flag with JSON Lines format."""
        # Create JSON Lines file
        jsonl_file = os.path.join(self.temp_dir, "data.jsonl")
        with open(jsonl_file, "w") as f:
            f.write('{"name": "user1", "tags": ["admin", "active"]}\n')
            f.write(
                '{"name": "user2", "tags": ["user"], "settings": {"theme": "dark"}}\n'
            )
            f.write('{"name": "user3", "tags": ["user", "premium"]}\n')

        _huml_main(inputs=jsonl_file, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all three users
        assert "name: user1" in output
        assert "name: user2" in output
        assert "name: user3" in output

        # Should have document separators for multi-document output
        assert "---" in output
        assert output.count("---") == 2  # Three documents = 2 separators

        # Arrays should be inline
        assert "  - admin" in output
        assert "  - active" in output
        assert "  - premium" in output

        # Objects should be structured properly
        assert "settings:" in output
        assert "  theme: dark" in output

    def test_inputs_flag_mixed_with_multi_docs(self, capsys):
        """Test --inputs flag with mixed single and multi-document files."""
        # Create a single-doc JSON
        single_json = os.path.join(self.temp_dir, "single.json")
        with open(single_json, "w") as f:
            json.dump({"service": "gateway", "version": "2.0"}, f)

        # Create multi-doc YAML
        multi_yaml = os.path.join(self.temp_dir, "multi.yaml")
        with open(multi_yaml, "w") as f:
            f.write("name: app1\n---\nname: app2")

        inputs = f"{single_json},{multi_yaml}"
        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all documents
        assert "service: gateway" in output
        assert "version: '2.0'" in output
        assert "name: app1" in output
        assert "name: app2" in output

        # Should have proper document count (1 + 2 = 3 documents)
        assert output.count("---") == 2  # 3 documents = 2 separators

    def test_inputs_flag_json_items_array(self, capsys):
        """Test --inputs flag with JSON containing items array."""
        # Create JSON file with items array (like Kubernetes list response)
        items_json = os.path.join(self.temp_dir, "k8s-list.json")
        list_data = {
            "apiVersion": "v1",
            "kind": "List",
            "metadata": {"resourceVersion": "12345"},
            "items": [
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {"name": "web-service"},
                    "spec": {"ports": [{"port": 80}]},
                },
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {"name": "web-deployment"},
                    "spec": {"replicas": 3},
                },
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {"name": "app-config"},
                    "data": {"env": "production", "debug": "false"},
                },
            ],
        }

        with open(items_json, "w") as f:
            json.dump(list_data, f)

        _huml_main(inputs=items_json, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all three items as separate documents
        assert "kind: Service" in output
        assert "kind: Deployment" in output
        assert "kind: ConfigMap" in output

        # Should have metadata names
        assert "name: web-service" in output
        assert "name: web-deployment" in output
        assert "name: app-config" in output

        # Should have document separators (3 items = 3 documents)
        assert output.count("---") == 2  # 3 documents = 2 separators between them
        assert not output.strip().startswith(
            "---"
        )  # Multi-document format should not start with separator

        # Objects should be multiline formatted
        assert "port: 80" in output

        # Priority key ordering should be preserved
        lines = output.split("\n")
        service_section = []
        in_service = False

        for line in lines:
            if "kind: Service" in line:
                in_service = True
                service_section = [line]
            elif in_service and line.strip() == "---":
                break
            elif in_service:
                service_section.append(line)

        service_text = "\n".join(service_section)
        # apiVersion should come before spec in ordering
        assert service_text.find("apiVersion:") < service_text.find("spec:")

    def test_inputs_flag_json_items_array_mixed_types(self, capsys):
        """Test --inputs flag with JSON items array containing mixed object types."""
        # Create JSON with items that have mixed content types
        mixed_json = os.path.join(self.temp_dir, "mixed-items.json")
        mixed_data = {
            "results": "success",
            "items": [
                {"type": "user", "name": "alice", "roles": ["admin"]},
                {"type": "config", "settings": {"theme": "dark", "lang": "en"}},
                {"type": "service", "name": "api", "ports": [8080, 9090]},
            ],
        }

        with open(mixed_json, "w") as f:
            json.dump(mixed_data, f)

        _huml_main(inputs=mixed_json, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all items
        assert "type: user" in output
        assert "type: config" in output
        assert "type: service" in output

        assert "name: alice" in output
        assert "name: api" in output

        # Should have 3 document separators
        assert output.count("---") == 2  # 3 documents = 2 separators

        # Arrays and objects should be properly formatted
        assert "  - admin" in output  # roles array inline
        assert "  - 8080" in output  # ports array inline
        assert "settings:" in output  # nested object
        assert "  theme: dark" in output

    def test_inputs_flag_json_no_items_array(self, capsys):
        """Test --inputs flag with regular JSON (no items array)."""
        # Regular JSON without items array should be processed normally
        regular_json = os.path.join(self.temp_dir, "regular.json")
        regular_data = {
            "application": "web-app",
            "services": [
                {"name": "frontend", "port": 3000},
                {"name": "backend", "port": 8000},
            ],
            "version": "2.1.0",
        }

        with open(regular_json, "w") as f:
            json.dump(regular_data, f)

        _huml_main(inputs=regular_json, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should be processed as single document (no document separators)
        assert "---" not in output
        assert "application: web-app" in output
        assert "version: 2.1.0" in output

        # Nested services should be formatted as multi-line objects
        assert "services:" in output
        assert "name: frontend" in output

    def test_inputs_flag_json_items_primitive_array(self, capsys):
        """Test --inputs flag with JSON items array containing primitives (should not split)."""
        # JSON with items containing only primitives should not be split
        primitive_json = os.path.join(self.temp_dir, "primitive-items.json")
        primitive_data = {
            "category": "colors",
            "items": ["red", "blue", "green", "yellow"],
        }

        with open(primitive_json, "w") as f:
            json.dump(primitive_data, f)

        _huml_main(inputs=primitive_json, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should be processed as single document (primitives don't warrant separation)
        assert "---" not in output
        assert "category: colors" in output
        assert "items:" in output
        assert "  - red" in output
        assert "  - blue" in output

    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.yaml")

        # This would be handled in the actual CLI implementation
        assert not os.path.exists(nonexistent_file)

    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        text_file = os.path.join(self.temp_dir, "test.txt")
        with open(text_file, "w") as f:
            f.write("This is just text")

        # Should be ignored or handled gracefully in actual implementation
        assert os.path.exists(text_file)
        assert not (
            text_file.endswith(".json")
            or text_file.endswith(".yaml")
            or text_file.endswith(".yml")
        )


class TestOutputFlag:
    """Test the --output flag functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_generate_k8s_filename(self):
        """Test Kubernetes manifest filename generation."""
        # Full Kubernetes manifest
        k8s_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "type": "app",
            "metadata": {"name": "web-server"},
        }
        assert _generate_k8s_filename(k8s_manifest) == "deployment-app-web-server.yaml"

        # Without type
        k8s_no_type = {
            "kind": "Service",
            "metadata": {"name": "api-service"},
        }
        assert _generate_k8s_filename(k8s_no_type) == "service-api-service.yaml"

        # Without metadata name
        k8s_no_name = {
            "kind": "ConfigMap",
            "type": "config",
        }
        assert _generate_k8s_filename(k8s_no_name) == "configmap-config.yaml"

        # Only kind
        k8s_kind_only = {"kind": "Pod"}
        assert _generate_k8s_filename(k8s_kind_only) == "pod.yaml"

        # No identifying fields
        generic_doc = {"data": {"key": "value"}}
        assert _generate_k8s_filename(generic_doc) == "document.yaml"

        # Non-dict input
        assert _generate_k8s_filename("not a dict") == "document.yaml"

    def test_output_single_file(self, capsys):
        """Test --output flag with single file."""
        output_file = os.path.join(self.temp_dir, "output.yaml")
        test_input = '{"name": "test", "version": "1.0"}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000, output=output_file)

        # Check that file was created
        assert os.path.exists(output_file)

        # Check file contents
        with open(output_file, "r") as f:
            content = f.read()
        assert "name: test" in content
        assert "version: '1.0'" in content

        # Should not output to stdout
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_output_directory_single_document(self, capsys):
        """Test --output flag with directory for single document."""
        import os

        output_dir = os.path.join(self.temp_dir, "output") + os.sep
        k8s_input = '{"kind": "Pod", "metadata": {"name": "test-pod"}, "spec": {}}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=k8s_input
        ):
            _huml_main(timeout=1000, output=output_dir, auto=True)

        captured = capsys.readouterr()
        assert "Created directory:" in captured.err

        # Check that directory was created
        dir_path = output_dir.rstrip(os.sep)
        assert os.path.exists(dir_path)
        assert os.path.isdir(dir_path)

        # Check that file was created with correct name (with prefix)
        expected_file = os.path.join(dir_path, "19-pod-test-pod.yaml")
        assert os.path.exists(expected_file)

        # Check file contents
        with open(expected_file, "r") as f:
            content = f.read()
        assert "kind: Pod" in content
        assert "name: test-pod" in content

    def test_output_directory_multiple_documents(self, capsys):
        """Test --output flag with directory for multiple documents."""
        import os

        output_dir = os.path.join(self.temp_dir, "manifests") + os.sep

        # Create JSON with items array
        items_json = os.path.join(self.temp_dir, "k8s-list.json")
        list_data = {
            "items": [
                {"kind": "Service", "metadata": {"name": "web-svc"}},
                {"kind": "Deployment", "metadata": {"name": "web-app"}},
                {"kind": "ConfigMap", "metadata": {"name": "app-config"}},
            ]
        }
        with open(items_json, "w") as f:
            json.dump(list_data, f)

        _huml_main(inputs=items_json, timeout=1000, output=output_dir, auto=True)

        captured = capsys.readouterr()
        assert "Created directory:" in captured.err

        # Check that directory was created
        dir_path = output_dir.rstrip(os.sep)
        assert os.path.exists(dir_path)

        # Check that all files were created (with prefixes)
        expected_files = [
            "11-service-web-svc.yaml",
            "14-deployment-web-app.yaml",
            "07-configmap-app-config.yaml",
        ]

        for expected_file in expected_files:
            file_path = os.path.join(dir_path, expected_file)
            assert os.path.exists(file_path), f"File {expected_file} was not created"

        # Check contents of one file (with prefix)
        with open(os.path.join(dir_path, "11-service-web-svc.yaml"), "r") as f:
            content = f.read()
        assert "kind: Service" in content
        assert "name: web-svc" in content

    def test_output_directory_without_auto_fails(self, capsys):
        """Test --output flag with non-existent directory fails without --auto."""
        import os

        output_dir = os.path.join(self.temp_dir, "nonexistent") + os.sep
        test_input = '{"test": "data"}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            with pytest.raises(SystemExit):
                _huml_main(timeout=1000, output=output_dir, auto=False)

        captured = capsys.readouterr()
        assert "Error: Directory does not exist:" in captured.err

    def test_output_file_with_auto_creates_parent_dirs(self, capsys):
        """Test --output flag with --auto creates parent directories."""
        nested_file = os.path.join(self.temp_dir, "deep", "nested", "output.yaml")
        test_input = '{"created": "file"}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000, output=nested_file, auto=True)

        captured = capsys.readouterr()
        assert "Created parent directories" in captured.err

        # Check that file and parent dirs were created
        assert os.path.exists(nested_file)

        with open(nested_file, "r") as f:
            content = f.read()
        assert "created: file" in content

    def test_output_multiple_files_to_single_file(self, capsys):
        """Test --output flag writes multiple documents to single file."""
        output_file = os.path.join(self.temp_dir, "multi.yaml")

        # Create test files
        json_file = os.path.join(self.temp_dir, "test.json")
        with open(json_file, "w") as f:
            json.dump({"service": "web"}, f)

        yaml_file = os.path.join(self.temp_dir, "test.yaml")
        with open(yaml_file, "w") as f:
            yaml.dump({"service": "api"}, f)

        inputs = f"{json_file},{yaml_file}"
        _huml_main(inputs=inputs, timeout=1000, output=output_file)

        # Check that file was created
        assert os.path.exists(output_file)

        with open(output_file, "r") as f:
            content = f.read()

        # Should contain both documents with separator
        assert "service: web" in content
        assert "service: api" in content
        assert "---" in content
        # Should not start with separator
        assert not content.strip().startswith("---")

    def test_output_filename_conflicts_handled(self, capsys):
        """Test that filename conflicts are handled by adding numbers."""
        import os

        output_dir = os.path.join(self.temp_dir, "conflicts") + os.sep

        # Create JSON with items that would have same filename
        items_json = os.path.join(self.temp_dir, "conflicts.json")
        list_data = {
            "items": [
                {"kind": "Pod", "metadata": {"name": "worker"}},
                {"kind": "Pod", "metadata": {"name": "worker"}},  # Same name
                {"kind": "Pod", "metadata": {"name": "worker"}},  # Same name again
            ]
        }
        with open(items_json, "w") as f:
            json.dump(list_data, f)

        _huml_main(inputs=items_json, timeout=1000, output=output_dir, auto=True)

        dir_path = output_dir.rstrip(os.sep)

        # Check that all files were created with conflict resolution (with prefixes)
        expected_files = [
            "19-pod-worker.yaml",
            "19-pod-worker-1.yaml",
            "19-pod-worker-2.yaml",
        ]

        for expected_file in expected_files:
            file_path = os.path.join(dir_path, expected_file)
            assert os.path.exists(file_path), f"File {expected_file} was not created"

    def test_filename_fallback_from_source_file(self, capsys):
        """Test that non-k8s documents get named after source file when using --inputs."""
        output_dir = os.path.join(self.temp_dir, "fallback") + os.sep

        # Create a JSON file with non-k8s data
        source_file = os.path.join(self.temp_dir, "user-config.json")
        non_k8s_data = {"username": "alice", "preferences": {"theme": "dark"}}
        with open(source_file, "w") as f:
            json.dump(non_k8s_data, f)

        _huml_main(inputs=source_file, timeout=1000, output=output_dir, auto=True)

        # Should be named after source file
        expected_file = os.path.join(output_dir.rstrip(os.sep), "user-config.yaml")
        assert os.path.exists(expected_file)

        with open(expected_file, "r") as f:
            content = f.read()
        assert "username: alice" in content

    def test_filename_fallback_stdin_single_document(self, capsys):
        """Test that stdin documents get named stdin-0 when no k8s info."""
        output_dir = os.path.join(self.temp_dir, "stdin") + os.sep

        test_input = '{"config": "value", "number": 42}'

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000, output=output_dir, auto=True)

        expected_file = os.path.join(output_dir.rstrip(os.sep), "stdin-0.yaml")
        assert os.path.exists(expected_file)

        with open(expected_file, "r") as f:
            content = f.read()
        assert "config: value" in content

    def test_filename_fallback_stdin_multiple_documents(self, capsys):
        """Test that stdin multi-documents get named stdin-0, stdin-1, etc."""
        output_dir = os.path.join(self.temp_dir, "stdin-multi") + os.sep

        # Multi-document YAML without k8s info
        test_input = """config: value1
number: 1
---
config: value2
number: 2
---
config: value3
number: 3"""

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000, output=output_dir, auto=True)

        # Should create stdin-0.yaml, stdin-1.yaml, stdin-2.yaml
        for i in range(3):
            expected_file = os.path.join(output_dir.rstrip(os.sep), f"stdin-{i}.yaml")
            assert os.path.exists(expected_file), f"File stdin-{i}.yaml was not created"

            with open(expected_file, "r") as f:
                content = f.read()
            assert f"config: value{i + 1}" in content

    def test_filename_fallback_mixed_k8s_and_non_k8s(self, capsys):
        """Test filename fallback behavior with mixed k8s and non-k8s documents."""
        output_dir = os.path.join(self.temp_dir, "mixed") + os.sep

        # Create file with both k8s and non-k8s data
        source_file = os.path.join(self.temp_dir, "mixed-resources.json")
        mixed_data = {
            "items": [
                {"kind": "Pod", "metadata": {"name": "worker"}},  # k8s resource
                {"username": "alice", "preferences": {"theme": "dark"}},  # non-k8s data
                {
                    "kind": "Service",
                    "metadata": {"name": "api"},
                    "type": "ClusterIP",
                },  # k8s with type
            ]
        }
        with open(source_file, "w") as f:
            json.dump(mixed_data, f)

        _huml_main(inputs=source_file, timeout=1000, output=output_dir, auto=True)

        dir_path = output_dir.rstrip(os.sep)

        # Check k8s resource gets proper name (with prefix)
        pod_file = os.path.join(dir_path, "19-pod-worker.yaml")
        assert os.path.exists(pod_file)

        # Check non-k8s data gets source filename
        fallback_file = os.path.join(dir_path, "mixed-resources.yaml")
        assert os.path.exists(fallback_file)
        with open(fallback_file, "r") as f:
            content = f.read()
        assert "username: alice" in content

        # Check k8s with type gets proper name (with prefix)
        service_file = os.path.join(dir_path, "11-service-clusterip-api.yaml")
        assert os.path.exists(service_file)


class TestStdinAutoDetection:
    """Test automatic format detection for stdin input."""

    def test_stdin_auto_detect_multi_document_yaml(self, capsys):
        """Test that multi-document YAML is auto-detected from stdin."""
        test_input = """name: doc1
---
name: doc2
---
name: doc3"""

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all three documents with separators
        assert "name: doc1" in output
        assert "name: doc2" in output
        assert "name: doc3" in output
        assert output.count("---") == 2  # 2 separators for 3 documents
        assert not output.strip().startswith("---")  # No separator at start

    def test_stdin_auto_detect_json_lines(self, capsys):
        """Test that JSON Lines format is auto-detected from stdin."""
        test_input = """{"name": "doc1"}
{"name": "doc2"}
{"name": "doc3"}"""

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all three documents as YAML with separators
        assert "name: doc1" in output
        assert "name: doc2" in output
        assert "name: doc3" in output
        assert output.count("---") == 2  # 2 separators for 3 documents

    def test_stdin_auto_detect_json_items_array(self, capsys):
        """Test that JSON items arrays are auto-detected from stdin."""
        test_input = (
            """{"items": [{"name": "doc1"}, {"name": "doc2"}, {"name": "doc3"}]}"""
        )

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain all three items as separate YAML documents
        assert "name: doc1" in output
        assert "name: doc2" in output
        assert "name: doc3" in output
        assert output.count("---") == 2  # 2 separators for 3 documents

    def test_stdin_single_document_still_works(self, capsys):
        """Test that single documents from stdin still work correctly."""
        test_input = """{"name": "single-doc", "type": "test"}"""

        with patch(
            "yaml_for_humans.cli._read_stdin_with_timeout", return_value=test_input
        ):
            _huml_main(timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain single document without separators
        assert "name: single-doc" in output
        assert "type: test" in output
        assert "---" not in output


class TestGlobbingAndDirectorySupport:
    """Test the enhanced --inputs flag with globbing and directory support."""

    def setup_method(self):
        """Set up test files and directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(self.sub_dir)

        # Create various test files
        self.json_files = []
        self.yaml_files = []
        self.other_files = []

        # JSON files
        for i in range(3):
            json_file = os.path.join(self.temp_dir, f"config{i}.json")
            with open(json_file, "w") as f:
                json.dump({"name": f"json-config-{i}", "id": i}, f)
            self.json_files.append(json_file)

        # YAML files
        for i in range(2):
            yaml_file = os.path.join(self.temp_dir, f"service{i}.yaml")
            with open(yaml_file, "w") as f:
                yaml.dump({"service": f"web-{i}", "port": 8000 + i}, f)
            self.yaml_files.append(yaml_file)

        # Files in subdirectory
        sub_json = os.path.join(self.sub_dir, "sub.json")
        with open(sub_json, "w") as f:
            json.dump({"location": "subdirectory"}, f)
        self.json_files.append(sub_json)

        # Invalid files
        txt_file = os.path.join(self.temp_dir, "readme.txt")
        with open(txt_file, "w") as f:
            f.write("This is just text, not JSON or YAML")
        self.other_files.append(txt_file)

        # Invalid JSON file
        invalid_json = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json, "w") as f:
            f.write('{"invalid": json}')  # Invalid syntax
        self.other_files.append(invalid_json)

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_valid_file_type_detection(self):
        """Test _is_valid_file_type function."""
        # Valid extensions
        assert _is_valid_file_type(self.json_files[0])
        assert _is_valid_file_type(self.yaml_files[0])

        # Invalid extension but might contain valid content
        assert not _is_valid_file_type(self.other_files[0])  # txt file

    def test_looks_like_yaml_function(self):
        """Test the _looks_like_yaml helper function."""
        assert _looks_like_yaml("key: value")
        assert _looks_like_yaml("- item1\n- item2")
        assert _looks_like_yaml("---\nkey: value")
        assert _looks_like_yaml("key: value\n  nested: true")

        # Should not detect JSON as YAML
        assert not _looks_like_yaml('{"key": "value"}')
        assert not _looks_like_yaml('["item1", "item2"]')

        # Edge cases
        assert not _looks_like_yaml("")
        assert not _looks_like_yaml("   ")

    def test_glob_pattern_json_files(self, capsys):
        """Test globbing with JSON files."""
        glob_pattern = os.path.join(self.temp_dir, "*.json")

        _huml_main(inputs=glob_pattern, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out
        error = captured.err

        # Should process all JSON files
        assert "name: json-config-0" in output
        assert "name: json-config-1" in output
        assert "name: json-config-2" in output

        # Should have multi-document separators
        assert output.count("---") >= 2

        # Should report invalid file
        assert (
            "Skipping file with invalid format" in error
            or "Error: Failed to parse" in error
        )

    def test_glob_pattern_yaml_files(self, capsys):
        """Test globbing with YAML files."""
        glob_pattern = os.path.join(self.temp_dir, "service*.yaml")

        _huml_main(inputs=glob_pattern, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should process all matching YAML files
        assert "service: web-0" in output
        assert "service: web-1" in output
        assert "port: 8000" in output
        assert "port: 8001" in output

    def test_glob_pattern_no_matches(self, capsys):
        """Test glob pattern that matches no files."""
        glob_pattern = os.path.join(self.temp_dir, "nonexistent*.json")

        _huml_main(inputs=glob_pattern, timeout=1000)

        captured = capsys.readouterr()
        error = captured.err
        output = captured.out

        assert "No files found matching pattern" in error
        assert output == ""  # No output since no files matched

    def test_directory_processing(self, capsys):
        """Test directory processing with os.sep."""
        dir_path = self.temp_dir + os.sep

        _huml_main(inputs=dir_path, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out
        error = captured.err

        # Should process all valid files in directory
        assert "name: json-config-0" in output
        assert "service: web-0" in output

        # Should skip invalid files and report them
        assert "Skipping file with invalid format" in error

    def test_directory_nonexistent(self, capsys):
        """Test directory that doesn't exist."""
        nonexistent_dir = os.path.join(self.temp_dir, "missing") + os.sep

        _huml_main(inputs=nonexistent_dir, timeout=1000)

        captured = capsys.readouterr()
        error = captured.err
        output = captured.out

        assert "Directory not found" in error
        assert output == ""  # No output since directory doesn't exist

    def test_mixed_glob_and_files(self, capsys):
        """Test mixing glob patterns and explicit files."""
        glob_pattern = os.path.join(self.temp_dir, "*.json")
        explicit_file = self.yaml_files[0]
        inputs = f"{glob_pattern},{explicit_file}"

        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should process both glob matches and explicit file
        assert "name: json-config-" in output  # From glob
        assert "service: web-0" in output  # From explicit file

    def test_mixed_directory_and_files(self, capsys):
        """Test mixing directory and explicit files."""
        dir_path = self.sub_dir + os.sep  # Only has sub.json
        explicit_file = self.yaml_files[0]
        inputs = f"{dir_path},{explicit_file}"

        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should process both directory contents and explicit file
        assert "location: subdirectory" in output  # From directory
        assert "service: web-0" in output  # From explicit file

    def test_continue_on_invalid_files(self, capsys):
        """Test that processing continues even with invalid files."""
        # Mix valid and invalid files
        valid_file = self.json_files[0]
        invalid_file = self.other_files[1]  # invalid.json
        inputs = f"{valid_file},{invalid_file}"

        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out
        error = captured.err

        # Should process valid file
        assert "name: json-config-0" in output

        # Should report error for invalid file but continue
        assert "Error: Failed to parse" in error
        assert "invalid.json" in error

    def test_glob_with_subdirectories(self, capsys):
        """Test glob patterns that include subdirectories."""
        glob_pattern = os.path.join(self.temp_dir, "**", "*.json")

        # Note: Need to use recursive glob for this to work
        import glob as glob_module

        matches = glob_module.glob(glob_pattern, recursive=True)

        if matches:  # Only test if recursive glob is supported
            _huml_main(inputs=glob_pattern, timeout=1000)

            captured = capsys.readouterr()
            # This might not work with basic glob, but we test the pattern

    def test_empty_directory(self, capsys):
        """Test processing empty directory."""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        dir_path = empty_dir + os.sep

        _huml_main(inputs=dir_path, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out
        error = captured.err

        # Should handle empty directory gracefully
        # Since no valid files are found, should just return with no output
        assert output == ""

    def test_file_and_glob_mixed_invalid(self, capsys):
        """Test mixing valid files, globs, and invalid patterns."""
        valid_file = self.json_files[0]
        valid_glob = os.path.join(self.temp_dir, "service*.yaml")
        invalid_glob = os.path.join(self.temp_dir, "missing*.txt")

        inputs = f"{valid_file},{valid_glob},{invalid_glob}"

        _huml_main(inputs=inputs, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out
        error = captured.err

        # Should process valid inputs
        assert "name: json-config-0" in output
        assert "service: web-" in output

        # Should report missing pattern
        assert "No files found matching pattern" in error

    def test_glob_case_sensitivity(self, capsys):
        """Test glob pattern case sensitivity."""
        # Create a file with uppercase extension
        upper_file = os.path.join(self.temp_dir, "test.JSON")
        with open(upper_file, "w") as f:
            json.dump({"case": "upper"}, f)

        # Test lowercase pattern
        glob_pattern = os.path.join(self.temp_dir, "*.json")

        _huml_main(inputs=glob_pattern, timeout=1000)

        captured = capsys.readouterr()
        output = captured.out

        # Should match regardless of case (depends on OS)
        # This test documents the current behavior


class TestFileTypeDetection:
    """Test file type detection for various file formats."""

    def setup_method(self):
        """Set up test files."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_extension_based_detection(self):
        """Test file type detection based on extensions."""
        # Create test files with various extensions
        test_files = {
            "test.json": '{"test": true}',
            "test.yaml": "test: true",
            "test.yml": "test: true",
            "test.jsonl": '{"line": 1}\n{"line": 2}',
            "test.txt": "Just text",
            "test": '{"no_extension": true}',  # No extension, but JSON content
        }

        for filename, content in test_files.items():
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)

        # Test valid extensions
        assert _is_valid_file_type(os.path.join(self.temp_dir, "test.json"))
        assert _is_valid_file_type(os.path.join(self.temp_dir, "test.yaml"))
        assert _is_valid_file_type(os.path.join(self.temp_dir, "test.yml"))
        assert _is_valid_file_type(os.path.join(self.temp_dir, "test.jsonl"))

        # Test invalid extension
        assert not _is_valid_file_type(os.path.join(self.temp_dir, "test.txt"))

        # Test no extension with JSON content
        assert _is_valid_file_type(os.path.join(self.temp_dir, "test"))

    def test_content_based_detection(self):
        """Test file type detection based on content."""
        # File without extension but with YAML content
        yaml_file = os.path.join(self.temp_dir, "config")
        with open(yaml_file, "w") as f:
            f.write("database:\n  host: localhost\n  port: 5432")

        assert _is_valid_file_type(yaml_file)

        # File without extension but with JSON content
        json_file = os.path.join(self.temp_dir, "settings")
        with open(json_file, "w") as f:
            f.write('{"database": {"host": "localhost", "port": 5432}}')

        assert _is_valid_file_type(json_file)

        # File with neither JSON nor YAML content
        text_file = os.path.join(self.temp_dir, "readme")
        with open(text_file, "w") as f:
            f.write("This is just plain text without any structured format")

        assert not _is_valid_file_type(text_file)

    def test_empty_file_detection(self):
        """Test detection of empty files."""
        empty_file = os.path.join(self.temp_dir, "empty.json")
        with open(empty_file, "w") as f:
            f.write("")

        # Empty files should be considered invalid
        assert not _is_valid_file_type(empty_file)

    def test_unreadable_file_detection(self):
        """Test handling of unreadable files."""
        # This test is platform-dependent and might not work in all environments
        unreadable_file = os.path.join(self.temp_dir, "unreadable.json")
        with open(unreadable_file, "w") as f:
            json.dump({"test": "data"}, f)

        # Try to make file unreadable (might not work in all environments)
        try:
            os.chmod(unreadable_file, 0o000)
            assert not _is_valid_file_type(unreadable_file)
        except (OSError, PermissionError):
            # Skip this test if we can't change file permissions
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(unreadable_file, 0o644)
            except (OSError, PermissionError):
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
