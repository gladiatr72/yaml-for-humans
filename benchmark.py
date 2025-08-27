#!/usr/bin/env python3
"""
YAML for Humans Performance Benchmark

Compares serialization and deserialization performance between PyYAML and YAML for Humans.
"""

import os
import time
from io import StringIO

import yaml

from yaml_for_humans.dumper import dumps
from yaml_for_humans.multi_document import dumps_all


def time_operation(func, *args, iterations=1000):
    """Time an operation over multiple iterations."""
    start = time.perf_counter()
    for _ in range(iterations):
        _ = func(*args)
    end = time.perf_counter()
    return (end - start) / iterations * 1000  # ms per operation


def benchmark_serialization():
    """Benchmark YAML serialization performance."""
    print("YAML Serialization Performance Benchmark")
    print("=" * 50)

    # Create test data of various sizes
    small_data = {"name": "test", "count": 42}

    medium_data = {
        "metadata": {"name": "app", "labels": {"env": "prod", "version": "1.0"}},
        "spec": {
            "replicas": 3,
            "containers": [
                {"name": "web", "image": "nginx:latest", "ports": [80, 443]},
                {"name": "app", "image": "python:3.9", "env": ["DEBUG=false"]},
            ],
        },
    }

    large_data = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "large-app",
            "labels": {f"label{i}": f"value{i}" for i in range(20)},
        },
        "spec": {
            "replicas": 5,
            "containers": [
                {
                    "name": f"container{i}",
                    "image": f"image{i}:latest",
                    "env": [f"VAR{j}=value{j}" for j in range(10)],
                    "ports": list(range(8000 + i * 10, 8010 + i * 10)),
                }
                for i in range(10)
            ],
        },
    }

    # Multi-document data
    multi_docs = [small_data, medium_data, large_data]

    def pyyaml_dump(data):
        stream = StringIO()
        yaml.dump(data, stream)
        return stream.getvalue()

    def pyyaml_dump_all(docs):
        stream = StringIO()
        yaml.dump_all(docs, stream)
        return stream.getvalue()

    test_cases = [
        ("Small data", small_data, 5000, pyyaml_dump, dumps),
        ("Medium data", medium_data, 1000, pyyaml_dump, dumps),
        ("Large data", large_data, 100, pyyaml_dump, dumps),
        ("Multi-document", multi_docs, 100, pyyaml_dump_all, dumps_all),
    ]

    for name, data, iterations, pyyaml_func, huml_func in test_cases:
        print(f"{name} ({iterations} iterations):")

        pyyaml_time = time_operation(lambda: pyyaml_func(data), iterations=iterations)
        huml_time = time_operation(lambda: huml_func(data), iterations=iterations)

        print(f"  PyYAML:       {pyyaml_time:.3f} ms/op")
        print(f"  YAML4Humans:  {huml_time:.3f} ms/op")
        print(
            f"  Ratio:        {huml_time / pyyaml_time:.2f}x {'slower' if huml_time > pyyaml_time else 'faster'}"
        )


def benchmark_deserialization():
    """Benchmark YAML deserialization performance."""
    print("\\n\\nYAML Deserialization Performance Benchmark")
    print("=" * 50)

    # Create YAML test data by serializing known good Python objects
    from io import StringIO

    # Create the data first, then serialize to YAML
    small_data = {"name": "test", "count": 42, "enabled": True}
    medium_data = {
        "metadata": {"name": "app", "labels": {"env": "prod", "version": "1.0"}},
        "spec": {
            "replicas": 3,
            "containers": [
                {"name": "web", "image": "nginx:latest", "ports": [80, 443]},
                {"name": "app", "image": "python:3.9", "env": ["DEBUG=false"]},
            ],
        },
    }

    large_data = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "large-app",
            "labels": {
                f"label{i}": f"value{i}" for i in range(10)
            },  # Smaller than before
        },
        "spec": {
            "replicas": 5,
            "containers": [
                {
                    "name": f"container{i}",
                    "image": f"image{i}:latest",
                    "env": [
                        f"VAR{j}=value{j}" for j in range(5)
                    ],  # Smaller than before
                    "ports": [8000 + i],
                }
                for i in range(5)  # Smaller than before
            ],
        },
    }

    multi_docs = [small_data, medium_data]

    # Convert to YAML strings
    def to_yaml(data):
        stream = StringIO()
        yaml.dump(data, stream)
        return stream.getvalue()

    def to_yaml_multi(docs):
        stream = StringIO()
        yaml.dump_all(docs, stream)
        return stream.getvalue()

    yaml_samples = {
        "small": to_yaml(small_data),
        "medium": to_yaml(medium_data),
        "large": to_yaml(large_data),
        "multi": to_yaml_multi(multi_docs),
    }

    # Test deserialization
    test_cases = [
        ("Small YAML", "small", 5000),
        ("Medium YAML", "medium", 1000),
        ("Large YAML", "large", 100),
        ("Multi-document", "multi", 100),
    ]

    for name, key, iterations in test_cases:
        yaml_content = yaml_samples[key]
        print(f"\\n{name} ({iterations} iterations):")
        print(f"  Content size: {len(yaml_content)} chars")

        if "multi" in key:
            pyyaml_time = time_operation(
                lambda: list(yaml.safe_load_all(yaml_content)), iterations=iterations
            )
        else:
            pyyaml_time = time_operation(
                lambda: yaml.safe_load(yaml_content), iterations=iterations
            )

        print(f"  PyYAML load:  {pyyaml_time:.3f} ms/op")
        print("  (YAML4Humans only handles serialization, not deserialization)")


def benchmark_real_file():
    """Benchmark with real Kubernetes files."""
    print("\\n\\nReal File Performance Benchmark")
    print("=" * 50)

    test_files = ["tests/test-data/whee.yaml", "tests/test-data/gotk-components.yaml"]

    for filepath in test_files:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                content = f.read()

            print(f"\\n{os.path.basename(filepath)}:")
            print(f"  File size: {len(content)} chars")

            # Test deserialization
            if "---" in content:
                pyyaml_time = time_operation(
                    lambda: list(yaml.safe_load_all(content)), iterations=10
                )
                print(f"  PyYAML load_all: {pyyaml_time:.3f} ms/op (10 iterations)")
            else:
                pyyaml_time = time_operation(
                    lambda: yaml.safe_load(content), iterations=100
                )
                print(f"  PyYAML load:     {pyyaml_time:.3f} ms/op (100 iterations)")

            # Test round-trip
            data = (
                list(yaml.safe_load_all(content))
                if "---" in content
                else yaml.safe_load(content)
            )

            def pyyaml_serialize():
                stream = StringIO()
                if isinstance(data, list):
                    yaml.dump_all(data, stream)
                else:
                    yaml.dump(data, stream)
                return stream.getvalue()

            def huml_serialize():
                if isinstance(data, list):
                    return dumps_all(data)
                else:
                    return dumps(data)

            pyyaml_ser_time = time_operation(pyyaml_serialize, iterations=10)
            huml_ser_time = time_operation(huml_serialize, iterations=10)

            print(f"  PyYAML dump:     {pyyaml_ser_time:.3f} ms/op (10 iterations)")
            print(f"  YAML4Humans:     {huml_ser_time:.3f} ms/op (10 iterations)")
            print(
                f"  Serialization ratio: {huml_ser_time / pyyaml_ser_time:.2f}x {'slower' if huml_ser_time > pyyaml_ser_time else 'faster'}"
            )


if __name__ == "__main__":
    benchmark_serialization()
    benchmark_deserialization()
    benchmark_real_file()
