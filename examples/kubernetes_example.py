#!/usr/bin/env python3
"""
Example: Kubernetes Deployment with human-friendly formatting.

This example shows how the block_sequence_for_people formatter
handles complex Kubernetes manifests.
"""

from yaml_for_humans.dumper import dumps


def main():
    """Generate a Kubernetes deployment with human-friendly formatting."""

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "web-app",
            "labels": {"app": "web-app", "version": "v1.0.0"},
        },
        "spec": {
            "replicas": 3,
            "selector": {"matchLabels": {"app": "web-app"}},
            "template": {
                "metadata": {"labels": {"app": "web-app"}},
                "spec": {
                    "containers": [
                        {
                            "ports": [{"containerPort": 80}],
                            "name": "nginx",  # name will appear first
                            "image": "nginx:1.21-alpine",
                            "imagePullPolicy": "IfNotPresent",
                            "command": ["/bin/sh", "-c", 'nginx -g "daemon off;"'],
                            "env": [
                                {"name": "NGINX_PORT", "value": "80"},
                                {"name": "NGINX_HOST", "value": "0.0.0.0"},
                            ],
                            "resources": {
                                "limits": {"cpu": "500m", "memory": "512Mi"},
                                "requests": {"cpu": "250m", "memory": "256Mi"},
                            },
                            "volumeMounts": [
                                {"name": "config", "mountPath": "/etc/nginx/conf.d"}
                            ],
                        }
                    ],
                    "initContainers": [
                        {
                            "name": "init-config",
                            "image": "busybox:latest",
                            "command": ["/bin/sh"],
                            "args": ["-c", 'echo "Initializing config..." && sleep 2'],
                        }
                    ],
                    "volumes": [
                        {"name": "config", "configMap": {"name": "nginx-config"}}
                    ],
                },
            },
        },
    }

    print("=== Kubernetes Deployment with Human-Friendly Formatting ===")
    print(dumps(deployment))

    print("\n=== Key Features Demonstrated ===")
    print("1. Priority key ordering: 'name', 'image', 'imagePullPolicy' appear first")
    print("2. String sequences inline: command and args arrays are compact")
    print("3. Object sequences multiline: containers, volumes have proper indentation")
    print("4. Consistent indentation: dashes are indented under parent containers")


if __name__ == "__main__":
    main()
