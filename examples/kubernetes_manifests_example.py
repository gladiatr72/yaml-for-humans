#!/usr/bin/env python3
"""
Example: Kubernetes manifests with resource ordering and human-friendly formatting.

Demonstrates the KubernetesManifestDumper functionality for creating
properly ordered Kubernetes YAML manifests.
"""

from yaml_for_humans.multi_document import (
    dumps_kubernetes_manifests,
)


def create_sample_manifests():
    """Create sample Kubernetes manifests for demonstration."""

    return [
        # Deployment (should be ordered after Service)
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "web-app",
                "namespace": "production",
                "labels": {"app": "web-app", "version": "v2.1.0"},
            },
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": "web-app"}},
                "template": {
                    "metadata": {"labels": {"app": "web-app", "version": "v2.1.0"}},
                    "spec": {
                        "containers": [
                            {
                                "ports": [{"containerPort": 8080, "name": "http"}],
                                "name": "web-server",  # name first due to priority
                                "image": "registry.example.com/web-app:v2.1.0",
                                "imagePullPolicy": "IfNotPresent",
                                "env": [
                                    {"name": "NODE_ENV", "value": "production"},
                                    {"name": "PORT", "value": "8080"},
                                    {"name": "LOG_LEVEL", "value": "info"},
                                ],
                                "command": ["/bin/sh", "-c", "npm start"],
                                "resources": {
                                    "limits": {"cpu": "1", "memory": "1Gi"},
                                    "requests": {"cpu": "500m", "memory": "512Mi"},
                                },
                                "volumeMounts": [
                                    {"name": "config", "mountPath": "/app/config"},
                                    {"name": "logs", "mountPath": "/app/logs"},
                                ],
                                "livenessProbe": {
                                    "httpGet": {"path": "/health", "port": 8080},
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10,
                                },
                            }
                        ],
                        "initContainers": [
                            {
                                "name": "db-migration",
                                "image": "registry.example.com/db-migrate:latest",
                                "command": ["migrate", "--up"],
                                "env": [
                                    {"name": "DB_HOST", "value": "postgres"},
                                    {"name": "DB_NAME", "value": "webapp"},
                                ],
                            }
                        ],
                        "volumes": [
                            {"name": "config", "configMap": {"name": "web-app-config"}},
                            {"name": "logs", "emptyDir": {}},
                        ],
                    },
                },
            },
        },
        # Service (should be ordered before Deployment)
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "web-app-service",
                "namespace": "production",
                "labels": {"app": "web-app"},
            },
            "spec": {
                "selector": {"app": "web-app"},
                "ports": [
                    {"name": "http", "port": 80, "targetPort": 8080, "protocol": "TCP"}
                ],
                "type": "ClusterIP",
            },
        },
        # ConfigMap (should be ordered before Service)
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "web-app-config", "namespace": "production"},
            "data": {
                "app.properties": "database.host=postgres\ndatabase.port=5432\nlog.level=info",
                "nginx.conf": "server {\n  listen 80;\n  location / {\n    proxy_pass http://localhost:8080;\n  }\n}",
                "features.yaml": "features:\n  - authentication\n  - logging\n  - metrics",
            },
        },
        # Namespace (should be ordered first)
        {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "production",
                "labels": {"environment": "production", "team": "platform"},
            },
        },
        # Ingress (should be after Service)
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "web-app-ingress",
                "namespace": "production",
                "annotations": {
                    "kubernetes.io/ingress.class": "nginx",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                },
            },
            "spec": {
                "tls": [{"hosts": ["app.example.com"], "secretName": "web-app-tls"}],
                "rules": [
                    {
                        "host": "app.example.com",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "web-app-service",
                                            "port": {"number": 80},
                                        }
                                    },
                                }
                            ]
                        },
                    }
                ],
            },
        },
    ]


def kubernetes_resource_ordering_example():
    """Demonstrate Kubernetes resource ordering."""

    print("=== Kubernetes Resource Ordering Example ===")

    manifests = create_sample_manifests()

    # Show original order
    original_order = [manifest["kind"] for manifest in manifests]
    print(f"Original order: {', '.join(original_order)}")

    # Generate with automatic ordering
    yaml_output = dumps_kubernetes_manifests(manifests)

    # Parse to show new order
    import yaml

    ordered_manifests = list(yaml.safe_load_all(yaml_output))
    ordered_kinds = [manifest["kind"] for manifest in ordered_manifests]
    print(f"Ordered result: {', '.join(ordered_kinds)}")

    print("\n" + yaml_output)

    print("\n=== Ordering Benefits ===")
    print("1. Namespace created before other resources")
    print("2. ConfigMap created before Deployment that uses it")
    print("3. Service created before Ingress that references it")
    print("4. Follows Kubernetes best practices for resource dependencies")


def complex_application_example():
    """Complete application with multiple resource types."""

    print("\n=== Complex Application Example ===")

    app_manifests = [
        # ServiceAccount
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "app-service-account", "namespace": "production"},
        },
        # Secret
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "app-secrets", "namespace": "production"},
            "type": "Opaque",
            "data": {
                "database-url": "cG9zdGdyZXM6Ly91c2VyOnBhc3NAZGIvYXBw",  # base64 encoded
                "api-key": "YWJjZGVmZ2hpams=",
            },
        },
        # StatefulSet (for database)
        {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {"name": "postgres", "namespace": "production"},
            "spec": {
                "serviceName": "postgres",
                "replicas": 1,
                "selector": {"matchLabels": {"app": "postgres"}},
                "template": {
                    "metadata": {"labels": {"app": "postgres"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "postgres",
                                "image": "postgres:13-alpine",
                                "env": [
                                    {"name": "POSTGRES_DB", "value": "webapp"},
                                    {"name": "POSTGRES_USER", "value": "user"},
                                    {"name": "POSTGRES_PASSWORD", "value": "password"},
                                ],
                                "ports": [{"containerPort": 5432}],
                                "volumeMounts": [
                                    {
                                        "name": "postgres-storage",
                                        "mountPath": "/var/lib/postgresql/data",
                                    }
                                ],
                            }
                        ]
                    },
                },
                "volumeClaimTemplates": [
                    {
                        "metadata": {"name": "postgres-storage"},
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "10Gi"}},
                        },
                    }
                ],
            },
        },
        # Job (for initial data setup)
        {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": "db-setup", "namespace": "production"},
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "db-setup",
                                "image": "postgres:13-alpine",
                                "command": ["psql"],
                                "args": [
                                    "-h",
                                    "postgres",
                                    "-U",
                                    "user",
                                    "-d",
                                    "webapp",
                                    "-c",
                                    "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(100));",
                                ],
                                "env": [{"name": "PGPASSWORD", "value": "password"}],
                            }
                        ],
                        "restartPolicy": "OnFailure",
                    }
                }
            },
        },
        # NetworkPolicy
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": "app-network-policy", "namespace": "production"},
            "spec": {
                "podSelector": {"matchLabels": {"app": "web-app"}},
                "policyTypes": ["Ingress", "Egress"],
                "ingress": [
                    {
                        "from": [
                            {"podSelector": {"matchLabels": {"role": "frontend"}}}
                        ],
                        "ports": [{"protocol": "TCP", "port": 8080}],
                    }
                ],
                "egress": [
                    {
                        "to": [{"podSelector": {"matchLabels": {"app": "postgres"}}}],
                        "ports": [{"protocol": "TCP", "port": 5432}],
                    }
                ],
            },
        },
    ]

    result = dumps_kubernetes_manifests(app_manifests)

    # Show the ordering
    import yaml

    ordered = list(yaml.safe_load_all(result))
    print("Resource order:", [r["kind"] for r in ordered])

    print("\nFirst 50 lines of output:")
    print("\n".join(result.split("\n")[:50]))
    print("... (output continues)")

    print("\n=== Complex Application Features ===")
    print("1. Multiple resource types properly ordered")
    print("2. ServiceAccount before other resources that might use it")
    print("3. Secret before Deployment that references it")
    print("4. StatefulSet for stateful services like databases")
    print("5. NetworkPolicy for security")
    print("6. Human-friendly formatting maintained throughout")


def main():
    """Run all Kubernetes manifest examples."""
    kubernetes_resource_ordering_example()
    complex_application_example()

    print("\n" + "=" * 60)
    print("Kubernetes manifests examples completed!")
    print("\nKey benefits of KubernetesManifestDumper:")
    print("- Automatic resource ordering following best practices")
    print("- Human-friendly formatting for better readability")
    print("- Priority key ordering in container specs")
    print("- Valid multi-document YAML for kubectl apply")


if __name__ == "__main__":
    main()
