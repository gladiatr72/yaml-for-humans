#!/usr/bin/env python3
"""
Example: Docker Compose with human-friendly formatting.

Shows how the formatter handles Docker Compose-style configurations.
"""

from yaml_for_humans.dumper import dumps


def main():
    """Generate a Docker Compose file with human-friendly formatting."""

    compose = {
        "version": "3.8",
        "services": {
            "web": {
                "image": "nginx:alpine",
                "command": ["nginx", "-g", "daemon off;"],
                "ports": ["80:80", "443:443"],
                "environment": [
                    "NGINX_HOST=localhost",
                    "NGINX_PORT=80",
                    "TLS_ENABLED=true",
                ],
                "volumes": [
                    "./nginx.conf:/etc/nginx/nginx.conf:ro",
                    "./html:/usr/share/nginx/html:ro",
                    "./certs:/etc/ssl/certs:ro",
                ],
                "depends_on": ["app", "cache"],
            },
            "app": {
                "image": "python:3.9-slim",
                "command": ["python", "app.py"],
                "environment": {
                    "DATABASE_URL": "postgres://user:pass@db:5432/myapp",
                    "REDIS_URL": "redis://cache:6379",
                    "DEBUG": "false",
                    "SECRET_KEY": "your-secret-key-here",
                },
                "volumes": ["./app:/code"],
                "depends_on": ["db", "cache"],
            },
            "db": {
                "image": "postgres:13-alpine",
                "environment": [
                    "POSTGRES_DB=myapp",
                    "POSTGRES_USER=user",
                    "POSTGRES_PASSWORD=secure-password",
                ],
                "volumes": ["pgdata:/var/lib/postgresql/data"],
                "ports": ["5432:5432"],
            },
            "cache": {
                "image": "redis:6-alpine",
                "command": ["redis-server", "--appendonly", "yes"],
                "volumes": ["redis-data:/data"],
                "ports": ["6379:6379"],
            },
        },
        "volumes": {"pgdata": {}, "redis-data": {}},
        "networks": {"default": {"driver": "bridge"}},
    }

    print("=== Docker Compose with Human-Friendly Formatting ===")
    print(dumps(compose))

    print("\n=== Features Shown ===")
    print("1. String arrays are compact: ports, environment variables")
    print("2. Service definitions are well-structured with proper indentation")
    print("3. Mixed content types handled appropriately")
    print("4. Empty dictionaries stay inline: volumes section")


if __name__ == "__main__":
    main()
