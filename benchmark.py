#!/usr/bin/env python3
"""
YAML for Humans Performance Benchmark

Compares serialization performance between PyYAML and YAML for Humans.
The purpose is to quantify the performance trade-off for human-friendly formatting.
"""

import time
from io import StringIO
import statistics

import yaml

from yaml_for_humans.dumper import dumps
from yaml_for_humans.multi_document import dumps_all


def time_operation(func, iterations=1000, warmup=10):
    """Time an operation over multiple iterations with warmup."""
    # Warmup runs to stabilize performance
    for _ in range(warmup):
        func()

    # Actual timing runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
    }


def create_test_data():
    """Create realistic test data of varying complexity."""

    # Simple configuration (typical config file)
    simple_config = {
        "app_name": "web-service",
        "version": "2.1.0",
        "port": 8080,
        "debug": False,
        "database": {"host": "localhost", "port": 5432, "name": "myapp"},
        "features": ["auth", "logging", "metrics"],
        "timeouts": {"connection": 30, "read": 60, "write": 30},
    }

    # Kubernetes-style deployment (common real-world use case)
    k8s_deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "nginx-deployment",
            "namespace": "production",
            "labels": {
                "app": "nginx",
                "version": "1.21",
                "env": "production",
                "component": "web",
            },
        },
        "spec": {
            "replicas": 3,
            "selector": {"matchLabels": {"app": "nginx"}},
            "template": {
                "metadata": {"labels": {"app": "nginx"}},
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:1.21-alpine",
                            "ports": [
                                {"containerPort": 80, "protocol": "TCP"},
                                {"containerPort": 443, "protocol": "TCP"},
                            ],
                            "env": [
                                {"name": "NGINX_HOST", "value": "example.com"},
                                {"name": "NGINX_PORT", "value": "80"},
                                {"name": "ENVIRONMENT", "value": "production"},
                            ],
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "500m", "memory": "512Mi"},
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": 80},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10,
                            },
                        }
                    ]
                },
            },
        },
    }

    # Large, complex configuration (stress test)
    large_config = {
        "microservices": {
            f"service-{i:02d}": {
                "name": f"microservice-{i:02d}",
                "image": f"myregistry/service-{i:02d}:v1.2.{i}",
                "replicas": (i % 5) + 1,
                "ports": [8000 + i, 9000 + i],
                "env_vars": {
                    f"SERVICE_NAME": f"service-{i:02d}",
                    f"SERVICE_PORT": str(8000 + i),
                    **{f"CONFIG_{j}": f"value_{i}_{j}" for j in range(8)},
                },
                "resources": {
                    "cpu_request": f"{(i * 50) + 100}m",
                    "cpu_limit": f"{(i * 100) + 500}m",
                    "memory_request": f"{(i * 64) + 128}Mi",
                    "memory_limit": f"{(i * 128) + 512}Mi",
                },
                "health_checks": {
                    "liveness": f"/health/{i}",
                    "readiness": f"/ready/{i}",
                    "startup": f"/startup/{i}",
                },
                "scaling": {
                    "min_replicas": 1,
                    "max_replicas": i + 5,
                    "cpu_threshold": 70 + (i * 2),
                    "memory_threshold": 80 + i,
                },
            }
            for i in range(20)  # 20 microservices
        },
        "global_config": {
            "cluster": "production",
            "region": "us-east-1",
            "monitoring": {
                "enabled": True,
                "endpoints": ["prometheus", "grafana", "jaeger"],
                "scrape_interval": "15s",
            },
            "security": {
                "tls_enabled": True,
                "cert_manager": True,
                "network_policies": True,
            },
            "shared_labels": {f"label-{i}": f"shared-value-{i}" for i in range(25)},
        },
    }

    # Multi-document scenario (common for Kubernetes manifests)
    multi_docs = [simple_config, k8s_deployment]

    return {
        "Simple Config": (simple_config, 5000),
        "Kubernetes Deployment": (k8s_deployment, 1000),
        "Large Configuration": (large_config, 200),
        "Multi-document": (multi_docs, 1000),
    }


def benchmark_serialization():
    """Compare serialization performance between PyYAML and YAML for Humans."""
    print("YAML Serialization Performance Benchmark")
    print("PyYAML vs YAML for Humans")
    print("=" * 65)
    print("Purpose: Quantify performance trade-off for human-friendly formatting")
    print()

    test_data = create_test_data()

    def pyyaml_single(data):
        stream = StringIO()
        yaml.dump(data, stream, default_flow_style=False, sort_keys=False)
        return stream.getvalue()

    def pyyaml_multi(docs):
        stream = StringIO()
        yaml.dump_all(docs, stream, default_flow_style=False, sort_keys=False)
        return stream.getvalue()

    results = []

    for test_name, (data, iterations) in test_data.items():
        print(f"{test_name}:")
        print(f"  Testing with {iterations:,} iterations...")

        # Choose appropriate functions
        if test_name == "Multi-document":
            pyyaml_func = lambda: pyyaml_multi(data)
            huml_func = lambda: dumps_all(data)
        else:
            pyyaml_func = lambda: pyyaml_single(data)
            huml_func = lambda: dumps(data)

        # Benchmark PyYAML
        pyyaml_stats = time_operation(pyyaml_func, iterations=iterations)

        # Benchmark YAML for Humans
        huml_stats = time_operation(huml_func, iterations=iterations)

        # Calculate performance ratio
        ratio = huml_stats["mean"] / pyyaml_stats["mean"]

        # Store results
        results.append(
            {
                "name": test_name,
                "pyyaml": pyyaml_stats,
                "huml": huml_stats,
                "ratio": ratio,
                "iterations": iterations,
            }
        )

        # Display results
        print(
            f"    PyYAML:          {pyyaml_stats['mean']:6.3f} ms/op (±{pyyaml_stats['stdev']:5.3f})"
        )
        print(
            f"    YAML4Humans:     {huml_stats['mean']:6.3f} ms/op (±{huml_stats['stdev']:5.3f})"
        )
        print(f"    Performance:     {ratio:5.2f}x slower")

        # Calculate output size difference (for interest)
        if test_name != "Multi-document":
            pyyaml_output = pyyaml_single(data)
            huml_output = dumps(data)
        else:
            pyyaml_output = pyyaml_multi(data)
            huml_output = dumps_all(data)

        size_ratio = len(huml_output) / len(pyyaml_output)
        print(
            f"    Output size:     {size_ratio:5.2f}x larger ({len(pyyaml_output)} → {len(huml_output)} chars)"
        )
        print()

    # Summary analysis
    print("=" * 65)
    print("PERFORMANCE SUMMARY")
    print("=" * 65)

    ratios = [r["ratio"] for r in results]
    weighted_ratios = [(r["ratio"] * r["iterations"]) for r in results]
    total_iterations = sum(r["iterations"] for r in results)

    print(f"Average slowdown:        {statistics.mean(ratios):5.2f}x")
    print(f"Median slowdown:         {statistics.median(ratios):5.2f}x")
    print(f"Weighted average:        {sum(weighted_ratios) / total_iterations:5.2f}x")
    print(f"Range:                   {min(ratios):4.2f}x - {max(ratios):4.2f}x")
    print()

    # Interpretation
    avg_ratio = statistics.mean(ratios)
    if avg_ratio < 2.0:
        interpretation = "Excellent - minimal performance impact"
    elif avg_ratio < 3.0:
        interpretation = "Good - reasonable trade-off for formatting benefits"
    elif avg_ratio < 5.0:
        interpretation = "Moderate - consider use case vs. performance needs"
    else:
        interpretation = "Significant - evaluate if formatting benefits justify cost"

    print(f"Assessment: {interpretation}")
    print()
    print("Note: Performance varies by data structure complexity.")
    print("The formatting benefits may justify the performance cost for")
    print("human-readable configuration files and development workflows.")


if __name__ == "__main__":
    benchmark_serialization()
