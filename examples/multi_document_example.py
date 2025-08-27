#!/usr/bin/env python3
"""
Example: Multi-document YAML with human-friendly formatting.

Demonstrates the multi-document dumper functionality for creating
YAML files with multiple documents separated by --- markers.
"""

from yaml_for_humans.multi_document import dumps_all, MultiDocumentDumper


def basic_multi_document_example():
    """Basic multi-document example with different data types."""

    print("=== Basic Multi-Document Example ===")

    documents = [
        # Configuration document
        {
            "config": {
                "version": "1.0",
                "features": ["feature1", "feature2", "feature3"],
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "credentials": {
                        "username": "admin",
                        "password_ref": {"secret": "db-creds", "key": "password"},
                    },
                },
            }
        },
        # Service list document
        {
            "services": [
                {
                    "name": "web-service",
                    "image": "nginx:latest",
                    "command": ["nginx", "-g", "daemon off;"],
                    "ports": [80, 443],
                    "environment": ["NGINX_HOST=0.0.0.0", "NGINX_PORT=80"],
                },
                {
                    "name": "api-service",
                    "image": "python:3.9",
                    "command": ["python", "app.py"],
                    "ports": [8000, 8001],
                    "volumes": ["/app:/code", "/data:/app/data"],
                },
            ]
        },
        # Simple key-value document
        {
            "metadata": {
                "created": "2025-01-01",
                "author": "DevOps Team",
                "tags": ["production", "web-app", "microservices"],
            }
        },
    ]

    yaml_output = dumps_all(documents)
    print(yaml_output)

    print("\n=== Features Demonstrated ===")
    print("1. Multiple documents separated by '---' markers")
    print("2. Human-friendly sequence formatting throughout")
    print("3. Priority key ordering in service definitions")
    print("4. Mixed content types: objects, arrays, strings")


def advanced_multi_document_example():
    """Advanced example with custom dumper options."""

    print("\n=== Advanced Multi-Document Example ===")

    documents = [
        {
            "pipeline": {
                "stages": ["build", "test", "deploy"],
                "jobs": [
                    {
                        "name": "build-job",
                        "image": "docker:latest",
                        "script": [
                            "docker build -t app:latest .",
                            "docker tag app:latest registry.com/app:$CI_COMMIT_SHA",
                            "docker push registry.com/app:$CI_COMMIT_SHA",
                        ],
                    }
                ],
            }
        },
        {
            "deployment": {
                "environment": "production",
                "replicas": 3,
                "containers": [
                    {
                        "name": "web-app",
                        "image": "registry.com/app:latest",
                        "env": [
                            {"name": "NODE_ENV", "value": "production"},
                            {"name": "PORT", "value": "3000"},
                        ],
                        "resources": {
                            "limits": {"cpu": "1", "memory": "1Gi"},
                            "requests": {"cpu": "500m", "memory": "512Mi"},
                        },
                    }
                ],
            }
        },
    ]

    # Use custom dumper options
    dumper = MultiDocumentDumper(
        explicit_end=True,  # Add document end markers
        indent=4,  # Use 4-space indentation
    )

    dumper.dump_all(documents)
    result = dumper.getvalue()

    print(result)

    print("\n=== Advanced Features ===")
    print("1. Document end markers (...) enabled")
    print("2. Custom 4-space indentation")
    print("3. Complex nested structures with proper formatting")


def configuration_files_example():
    """Example of using multi-document for configuration files."""

    print("\n=== Configuration Files Example ===")

    # Simulate multiple related configuration sections
    config_documents = [
        # Application configuration
        {
            "app": {
                "name": "my-web-app",
                "version": "2.1.0",
                "debug": False,
                "features": ["authentication", "logging", "metrics", "health-checks"],
            }
        },
        # Logging configuration
        {
            "logging": {
                "level": "INFO",
                "handlers": [
                    {"name": "console", "type": "StreamHandler", "formatter": "json"},
                    {
                        "name": "file",
                        "type": "RotatingFileHandler",
                        "filename": "/var/log/app.log",
                        "max_size": "10MB",
                        "backup_count": 5,
                    },
                ],
            }
        },
        # Security configuration
        {
            "security": {
                "authentication": {
                    "providers": ["oauth2", "ldap"],
                    "session_timeout": 3600,
                    "allowed_origins": [
                        "https://app.example.com",
                        "https://admin.example.com",
                    ],
                },
                "encryption": {"algorithm": "AES-256-GCM", "key_rotation_days": 90},
            }
        },
    ]

    result = dumps_all(config_documents, indent=2)
    print(result)

    print("\n=== Configuration Use Case ===")
    print("1. Logical separation of configuration concerns")
    print("2. Easy to read and maintain")
    print("3. Each document can be processed independently")


def main():
    """Run all multi-document examples."""
    basic_multi_document_example()
    advanced_multi_document_example()
    configuration_files_example()

    print("\n" + "=" * 50)
    print("Multi-document YAML examples completed!")
    print("Key benefits:")
    print("- Clean document separation with --- markers")
    print("- Human-friendly formatting preserved throughout")
    print("- Flexible dumper options for different use cases")
    print("- Valid multi-document YAML that can be loaded back")


if __name__ == "__main__":
    main()
