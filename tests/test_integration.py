"""
Integration tests for human-friendly YAML formatting.

Tests the complete system with real-world examples including
Kubernetes manifests and complex nested structures.
"""

import os
import tempfile

import pytest
import yaml

from yaml_for_humans.dumper import dump, dumps


class TestKubernetesIntegration:
    """Test with Kubernetes-style YAML manifests."""

    def test_kubernetes_deployment(self):
        """Test a complete Kubernetes deployment manifest."""
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "test-app",
                "labels": {"app": "test-app", "version": "v1.0.0"},
            },
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": "test-app"}},
                "template": {
                    "metadata": {"labels": {"app": "test-app"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "web",
                                "image": "nginx:1.21-alpine",
                                "imagePullPolicy": "IfNotPresent",
                                "command": ["/bin/sh", "-c", 'nginx -g "daemon off;"'],
                                "ports": [{"containerPort": 80, "protocol": "TCP"}],
                                "env": [{"name": "ENV_VAR", "value": "production"}],
                                "resources": {
                                    "limits": {"cpu": "500m", "memory": "512Mi"},
                                    "requests": {"cpu": "250m", "memory": "256Mi"},
                                },
                                "volumeMounts": [
                                    {
                                        "name": "config",
                                        "mountPath": "/etc/nginx/conf.d",
                                    },
                                    {"name": "logs", "mountPath": "/var/log/nginx"},
                                ],
                            }
                        ],
                        "initContainers": [
                            {
                                "name": "init-config",
                                "image": "busybox:latest",
                                "command": ["/bin/sh"],
                                "args": ["-c", 'echo "Initializing..." && sleep 5'],
                            }
                        ],
                        "volumes": [
                            {"name": "config", "configMap": {"name": "nginx-config"}},
                            {"name": "logs", "emptyDir": {}},
                        ],
                    },
                },
            },
        }

        yaml_str = dumps(deployment)

        # Verify key ordering
        lines = yaml_str.split("\n")
        container_section = []
        in_container = False
        container_started = False

        for line in lines:
            if "containers:" in line:
                in_container = True
            elif in_container and not container_started and line.strip() == "-":
                # Start of first container
                container_section = [line]
                container_started = True
            elif (
                in_container
                and container_started
                and (line.strip() == "" or not line.startswith("        "))
            ):
                # End of container section
                break
            elif in_container and container_started:
                container_section.append(line)

        container_text = "\n".join(container_section)

        # Verify priority key ordering in containers
        assert "name: web" in container_text
        assert container_text.find("name:") < container_text.find("ports:")
        assert container_text.find("image:") < container_text.find("resources:")
        assert container_text.find("imagePullPolicy:") < container_text.find(
            "volumeMounts:"
        )

        # Verify sequence formatting
        assert "            - /bin/sh" in yaml_str  # Command strings inline
        assert "            - -c" in yaml_str
        assert (
            "containers:\n        -\n          name: web" in yaml_str
        )  # Objects multiline

        # Verify round-trip
        parsed = yaml.safe_load(yaml_str)
        assert parsed == deployment

    def test_complex_nested_structures(self):
        """Test deeply nested structures with mixed content types."""
        complex_data = {
            "configuration": {
                "database": {
                    "connections": [
                        {
                            "name": "primary",
                            "host": "db1.example.com",
                            "credentials": {
                                "username": "admin",
                                "password_ref": {
                                    "secret": "db-creds",
                                    "key": "password",
                                },
                            },
                            "options": ["ssl=true", "timeout=30", "retry=3"],
                        },
                        {
                            "name": "replica",
                            "host": "db2.example.com",
                            "options": ["readonly=true", "ssl=true"],
                        },
                    ]
                },
                "cache": {
                    "redis": {
                        "servers": ["redis1:6379", "redis2:6379", "redis3:6379"],
                        "config": {"maxmemory": "2gb", "policies": ["allkeys-lru"]},
                    }
                },
            }
        }

        yaml_str = dumps(complex_data)

        # Test string arrays are inline
        assert (
            "          - ssl=true\n          - timeout=30\n          - retry=3"
            in yaml_str
        )
        assert (
            "        - redis1:6379\n        - redis2:6379\n        - redis3:6379"
            in yaml_str
        )

        # Test objects are multiline
        assert "connections:\n      -\n        name: primary" in yaml_str

        # Verify round-trip
        parsed = yaml.safe_load(yaml_str)
        assert parsed == complex_data


class TestFileOperations:
    """Test file I/O operations."""

    def test_dump_to_file(self):
        """Test dumping to a file."""
        data = {
            "test": ["item1", "item2"],
            "objects": [{"name": "obj1", "value": 1}, {"name": "obj2", "value": 2}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name
            dump(data, f)

        try:
            # Read back and verify
            with open(temp_path, "r") as f:
                content = f.read()
                parsed = yaml.safe_load(content)

            assert parsed == data
            assert "  - item1" in content  # String inline
            assert "objects:\n  -\n    name: obj1" in content  # Object multiline

        finally:
            os.unlink(temp_path)

    def test_large_file_handling(self):
        """Test handling of larger data structures."""
        # Create a reasonably large structure
        large_data = {"services": {}}

        for i in range(50):
            large_data["services"][f"service-{i}"] = {
                "name": f"service-{i}",
                "image": f"app:v{i}",
                "command": ["/bin/sh", "-c", f"service-{i} --port={8000 + i}"],
                "env": [
                    {"name": "SERVICE_ID", "value": str(i)},
                    {"name": "PORT", "value": str(8000 + i)},
                ],
                "resources": {},
                "ports": [{"containerPort": 8000 + i}],
            }

        yaml_str = dumps(large_data)
        parsed = yaml.safe_load(yaml_str)

        assert parsed == large_data
        assert len(parsed["services"]) == 50

        # Verify formatting consistency throughout
        lines = yaml_str.split("\n")
        service_lines = [
            line for line in lines if "service-" in line and "name:" in line
        ]
        assert len(service_lines) == 50  # Each service should have a name line


class TestCLIInputsFlag:
    """Test CLI --inputs flag functionality with real files."""

    def setup_method(self):
        """Set up test files for CLI testing."""
        import os
        import tempfile

        self.temp_dir = tempfile.mkdtemp()

        # Create a Kubernetes-style JSON file
        self.k8s_json = os.path.join(self.temp_dir, "deployment.json")
        deployment_data = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "web-app"},
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": "web"}},
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "web",
                                "image": "nginx:alpine",
                                "ports": [{"containerPort": 80}],
                                "env": [{"name": "ENV", "value": "prod"}],
                            }
                        ]
                    }
                },
            },
        }

        with open(self.k8s_json, "w") as f:
            import json

            json.dump(deployment_data, f)

        # Create a Docker Compose YAML file
        self.compose_yaml = os.path.join(self.temp_dir, "docker-compose.yml")
        compose_data = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "ports": ["80:80", "443:443"],
                    "environment": ["NODE_ENV=production"],
                    "depends_on": ["db"],
                },
                "db": {
                    "image": "postgres:13",
                    "environment": {"POSTGRES_DB": "app", "POSTGRES_USER": "user"},
                },
            },
        }

        with open(self.compose_yaml, "w") as f:
            yaml.dump(compose_data, f)

    def teardown_method(self):
        """Clean up test files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_cli_inputs_kubernetes_deployment(self):
        """Test CLI --inputs flag with Kubernetes deployment JSON."""
        import sys
        from io import StringIO

        from yaml_for_humans.cli import _huml_main

        # Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            _huml_main(inputs=self.k8s_json, timeout=1000)
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify key ordering (priority keys first)
        lines = output.split("\n")
        container_section = []
        in_containers = False

        for line in lines:
            if "containers:" in line:
                in_containers = True
            elif in_containers and "name: web" in line:
                # Find the container section
                idx = lines.index(line)
                container_section = lines[
                    idx - 2 : idx + 10
                ]  # Get context around container
                break

        container_text = "\n".join(container_section)

        # Priority key ordering should be preserved
        assert "name: web" in output
        assert "image: nginx:alpine" in output
        assert container_text.find("name:") < container_text.find("ports:")

        # Objects should be multiline formatted (not inline)
        assert "containerPort: 80" in output
        assert "name: ENV" in output

    def test_cli_inputs_multiple_files(self):
        """Test CLI --inputs flag with multiple files."""
        import sys
        from io import StringIO

        from yaml_for_humans.cli import _huml_main

        inputs = f"{self.k8s_json},{self.compose_yaml}"

        # Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            _huml_main(inputs=inputs, timeout=1000)
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        # Should contain both files' content
        assert "kind: Deployment" in output  # From k8s JSON
        assert "version: '3.8'" in output  # From compose YAML (note single quotes)
        assert "services:" in output

        # Should have document separators
        assert "---" in output
        separators = output.count("---")
        assert separators == 1  # Two documents = 1 separator

        # Multi-document output should not start with separator
        assert not output.strip().startswith("---")

        # Arrays should be properly formatted
        assert "  - 80:80" in output  # Docker compose ports inline
        assert "  - NODE_ENV=production" in output  # Environment vars inline


class TestRealWorldExamples:
    """Test with real-world configuration examples."""

    def test_docker_compose_style(self):
        """Test Docker Compose-style configuration."""
        compose_data = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:alpine",
                    "command": ["nginx", "-g", "daemon off;"],
                    "ports": ["80:80", "443:443"],
                    "environment": ["NGINX_HOST=localhost", "NGINX_PORT=80"],
                    "volumes": [
                        "./nginx.conf:/etc/nginx/nginx.conf:ro",
                        "./html:/usr/share/nginx/html:ro",
                    ],
                    "depends_on": ["app"],
                },
                "app": {
                    "image": "python:3.9",
                    "command": ["python", "app.py"],
                    "environment": {
                        "DATABASE_URL": "postgres://user:pass@db:5432/app",
                        "DEBUG": "false",
                    },
                    "volumes": ["./app:/code"],
                    "depends_on": ["db"],
                },
                "db": {
                    "image": "postgres:13",
                    "environment": [
                        "POSTGRES_DB=app",
                        "POSTGRES_USER=user",
                        "POSTGRES_PASSWORD=pass",
                    ],
                    "volumes": ["pgdata:/var/lib/postgresql/data"],
                },
            },
            "volumes": {"pgdata": {}},
        }

        yaml_str = dumps(compose_data)

        # Verify string arrays are inline
        assert "      - nginx\n      - -g\n      - daemon off;" in yaml_str
        assert "      - 80:80\n      - 443:443" in yaml_str

        # Verify objects have proper structure
        assert "services:\n  web:\n    image: nginx:alpine" in yaml_str

        # Test round-trip
        parsed = yaml.safe_load(yaml_str)
        assert parsed == compose_data

    def test_ci_cd_pipeline(self):
        """Test CI/CD pipeline configuration."""
        pipeline_data = {
            "stages": ["build", "test", "deploy"],
            "variables": {
                "DOCKER_REGISTRY": "registry.example.com",
                "IMAGE_TAG": "$CI_COMMIT_SHA",
            },
            "build:image": {
                "stage": "build",
                "image": "docker:latest",
                "services": ["docker:dind"],
                "script": [
                    "docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY",
                    "docker build -t $CI_REGISTRY_IMAGE:$IMAGE_TAG .",
                    "docker push $CI_REGISTRY_IMAGE:$IMAGE_TAG",
                ],
                "only": ["main", "develop"],
            },
            "test:unit": {
                "stage": "test",
                "image": "python:3.9",
                "script": [
                    "pip install -r requirements.txt",
                    "python -m pytest tests/ --cov=src/",
                    "coverage report --fail-under=80",
                ],
                "artifacts": {
                    "reports": {
                        "coverage_report": {
                            "coverage_format": "cobertura",
                            "path": "coverage.xml",
                        }
                    }
                },
            },
        }

        yaml_str = dumps(pipeline_data)

        # Test string sequences are inline
        assert "  - build\n  - test\n  - deploy" in yaml_str
        assert "  - docker:dind" in yaml_str

        # Test round-trip
        parsed = yaml.safe_load(yaml_str)
        assert parsed == pipeline_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
