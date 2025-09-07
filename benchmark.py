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


def time_operation(func, iterations=1000, warmup=50):
    """Time an operation over multiple iterations with warmup."""
    import gc
    
    # Force garbage collection before starting
    gc.collect()
    
    # Extended warmup to stabilize JIT/caching effects
    for _ in range(warmup):
        func()
    
    # Force GC again after warmup
    gc.collect()

    # Actual timing runs with periodic GC
    times = []
    for i in range(iterations):
        # Force GC every 100 iterations to reduce noise
        if i % 100 == 0:
            gc.collect()
            
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    # Remove outliers (top/bottom 5%) for more stable results
    sorted_times = sorted(times)
    outlier_count = max(1, len(times) // 20)  # 5%
    trimmed_times = sorted_times[outlier_count:-outlier_count] if len(times) > 20 else times

    return {
        "mean": statistics.mean(trimmed_times),
        "median": statistics.median(trimmed_times),
        "stdev": statistics.stdev(trimmed_times) if len(trimmed_times) > 1 else 0,
        "min": min(trimmed_times),
        "max": max(trimmed_times),
        "raw_samples": len(times),
        "trimmed_samples": len(trimmed_times),
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
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def pyyaml_multi(docs):
        return yaml.dump_all(docs, default_flow_style=False, sort_keys=False)

    results = []

    for test_name, (data, iterations) in test_data.items():
        print(f"{test_name}:")
        print(f"  Testing with {iterations:,} iterations...")

        # Create bound functions to eliminate lambda overhead and capture issues
        if test_name == "Multi-document":
            def pyyaml_func():
                return pyyaml_multi(data)
            def huml_func():
                return dumps_all(data)
        else:
            def pyyaml_func():
                return pyyaml_single(data)
            def huml_func():
                return dumps(data)

        # Verify both functions produce valid output (sanity check)
        pyyaml_output = pyyaml_func()
        huml_output = huml_func()
        
        # Basic validation that both produced non-empty strings
        if not pyyaml_output or not huml_output:
            print(f"    ERROR: One library produced empty output, skipping {test_name}")
            continue
            
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

        # Format performance comparison with proper statistical significance
        # Use 10% threshold to account for measurement noise and system variability
        if ratio < 0.90:  # Significantly faster (>10% improvement)
            perf_display = f"{1 / ratio:5.2f}x faster"
        elif ratio > 1.10:  # Significantly slower (>10% degradation) 
            perf_display = f"{ratio:5.2f}x slower"
        else:  # Within 10% - not statistically significant
            perf_display = "equivalent performance (within measurement error)"

        print(f"    Performance:     {perf_display}")

        # Calculate output size difference (using already generated output)
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

    avg_ratio = statistics.mean(ratios)
    median_ratio = statistics.median(ratios)
    weighted_avg = sum(weighted_ratios) / total_iterations

    print(f"Average performance ratio:   {avg_ratio:5.2f}x")
    print(f"Median performance ratio:    {median_ratio:5.2f}x")
    print(f"Weighted average ratio:      {weighted_avg:5.2f}x")
    print(f"Range:                       {min(ratios):4.2f}x - {max(ratios):4.2f}x")
    print()

    # Provide interpretation of ratios with statistical significance
    faster_count = sum(1 for r in ratios if r < 0.90)
    slower_count = sum(1 for r in ratios if r > 1.10) 
    equiv_count = len(ratios) - faster_count - slower_count

    print(f"Test cases where YAML4Humans is faster:      {faster_count}")
    print(f"Test cases where YAML4Humans is slower:      {slower_count}")
    print(f"Test cases with equivalent performance:      {equiv_count}")
    print()

    # Overall assessment with realistic expectations
    if avg_ratio < 0.85:
        assessment = "Unexpected - YAML4Humans appears faster (verify results)"
    elif avg_ratio < 1.15:
        assessment = "Excellent - performance is essentially equivalent"
    elif avg_ratio < 2.0:
        assessment = "Good - reasonable trade-off for human-readable formatting"
    elif avg_ratio < 4.0:
        assessment = "Fair - moderate performance cost for formatting benefits"
    else:
        assessment = "Poor - significant performance cost, consider use case carefully"

    print(f"Overall Assessment: {assessment}")
    print()
    print("Note: Performance varies by data structure complexity and system load.")
    print("YAML4Humans prioritizes human-readable output over raw performance.")
    print("Results within 10% should be considered equivalent due to measurement")
    print("variability. Claims of superior performance require verification.")


if __name__ == "__main__":
    benchmark_serialization()
