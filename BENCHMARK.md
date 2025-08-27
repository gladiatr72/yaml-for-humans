#!/usr/bin/env python3
"""
Accurate YAML for Humans Performance Benchmark

A more rigorous benchmark that accounts for measurement error and statistical variation.
"""

import time
import yaml
import statistics
from io import StringIO
from yaml_for_humans.dumper import dumps
from yaml_for_humans.multi_document import dumps_all
import os


def measure_function(func, iterations=100, warmup=10):
    """
    Measure function performance with proper warmup and statistical analysis.
    Returns (mean_ms, std_dev_ms, min_ms, max_ms)
    """
    # Warmup runs
    for _ in range(warmup):
        func()

    # Actual measurements
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds

    return (
        statistics.mean(times),
        statistics.stdev(times) if len(times) > 1 else 0,
        min(times),
        max(times),
    )


def accurate_benchmark():
    """Run accurate performance benchmarks with statistical analysis."""
    print("Accurate YAML Performance Benchmark")
    print("=" * 50)
    print("(Using proper statistical measurement with warmup)")
    print()

    # Test cases with increasing complexity
    test_data = [
        ("Simple object", {"name": "test", "value": 42}),
        (
            "Medium object",
            {
                "metadata": {"name": "app", "namespace": "default"},
                "spec": {
                    "replicas": 3,
                    "containers": [
                        {"name": "web", "image": "nginx:latest"},
                        {"name": "app", "image": "python:3.9"},
                    ],
                },
            },
        ),
        (
            "Complex object",
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": "test-app",
                    "labels": {f"label{i}": f"value{i}" for i in range(5)},
                },
                "spec": {
                    "replicas": 3,
                    "containers": [
                        {
                            "name": f"container{i}",
                            "image": f"image{i}:latest",
                            "env": [f"VAR{j}=value{j}" for j in range(3)],
                        }
                        for i in range(3)
                    ],
                },
            },
        ),
    ]

    for name, data in test_data:
        print(f"{name}:")

        def pyyaml_serialize():
            stream = StringIO()
            yaml.dump(data, stream)
            return stream.getvalue()

        def yaml4humans_serialize():
            return dumps(data)

        # Measure both approaches
        pyyaml_stats = measure_function(pyyaml_serialize, iterations=1000)
        yaml4h_stats = measure_function(yaml4humans_serialize, iterations=1000)

        print(f"  PyYAML:       {pyyaml_stats[0]:.3f}±{pyyaml_stats[1]:.3f} ms/op")
        print(f"  YAML4Humans:  {yaml4h_stats[0]:.3f}±{yaml4h_stats[1]:.3f} ms/op")
        print(f"  Slowdown:     {yaml4h_stats[0]/pyyaml_stats[0]:.2f}x")
        print()

    # Multi-document test
    print("Multi-document:")
    multi_data = [test_data[0][1], test_data[1][1]]

    def pyyaml_multi():
        stream = StringIO()
        yaml.dump_all(multi_data, stream)
        return stream.getvalue()

    def yaml4h_multi():
        return dumps_all(multi_data)

    pyyaml_multi_stats = measure_function(pyyaml_multi, iterations=500)
    yaml4h_multi_stats = measure_function(yaml4h_multi, iterations=500)

    print(
        f"  PyYAML:       {pyyaml_multi_stats[0]:.3f}±{pyyaml_multi_stats[1]:.3f} ms/op"
    )
    print(
        f"  YAML4Humans:  {yaml4h_multi_stats[0]:.3f}±{yaml4h_multi_stats[1]:.3f} ms/op"
    )
    print(f"  Slowdown:     {yaml4h_multi_stats[0]/pyyaml_multi_stats[0]:.2f}x")
    print()


def real_file_benchmark():
    """Benchmark with actual files."""
    print("Real File Benchmark")
    print("=" * 30)

    test_files = ["tests/test-data/whee.yaml"]

    for filepath in test_files:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                content = f.read()

            print(f"{os.path.basename(filepath)} ({len(content)} chars):")

            # Parse the file
            if "---" in content:
                data = list(yaml.safe_load_all(content))
            else:
                data = yaml.safe_load(content)

            def pyyaml_serialize():
                stream = StringIO()
                if isinstance(data, list):
                    yaml.dump_all(data, stream)
                else:
                    yaml.dump(data, stream)
                return stream.getvalue()

            def yaml4h_serialize():
                if isinstance(data, list):
                    return dumps_all(data)
                else:
                    return dumps(data)

            # Measure serialization (fewer iterations for large files)
            iterations = 100 if len(content) < 10000 else 10

            pyyaml_stats = measure_function(pyyaml_serialize, iterations=iterations)
            yaml4h_stats = measure_function(yaml4h_serialize, iterations=iterations)

            print(f"  PyYAML:       {pyyaml_stats[0]:.3f}±{pyyaml_stats[1]:.3f} ms/op")
            print(f"  YAML4Humans:  {yaml4h_stats[0]:.3f}±{yaml4h_stats[1]:.3f} ms/op")
            print(f"  Slowdown:     {yaml4h_stats[0]/pyyaml_stats[0]:.2f}x")
            print()


def format_quality_comparison():
    """Compare output quality and readability."""
    print("Output Quality Comparison")
    print("=" * 30)

    test_data = {
        "metadata": {"name": "test", "labels": {}},
        "spec": {
            "containers": [
                {"name": "web", "env": [], "ports": [80, 443]},
                {"resources": {}, "image": "nginx:latest"},
            ],
            "volumes": [],
        },
    }

    pyyaml_stream = StringIO()
    yaml.dump(test_data, pyyaml_stream)
    pyyaml_output = pyyaml_stream.getvalue()

    yaml4h_output = dumps(test_data)

    print("PyYAML output:")
    print(pyyaml_output)
    print("YAML4Humans output:")
    print(yaml4h_output)

    print("Quality improvements:")
    print(
        "- Empty containers inline: {}",
        (
            "{}/[] appear inline"
            if ("{}" in yaml4h_output or "[]" in yaml4h_output)
            else "No"
        ),
    )
    print(
        "- Priority key ordering: {}",
        (
            "name appears first"
            if yaml4h_output.find("name:") < yaml4h_output.find("labels:")
            else "Standard order"
        ),
    )


if __name__ == "__main__":
    accurate_benchmark()
    print()
    real_file_benchmark()
    print()
    format_quality_comparison()
