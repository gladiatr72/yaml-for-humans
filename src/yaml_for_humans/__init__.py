"""
YAML for Humans - Human-friendly YAML formatting

This package provides custom PyYAML emitters that produce more readable YAML output
with intelligent sequence formatting and priority key ordering.

Features:
- Single document dumping with human-friendly formatting
- Multi-document dumping with proper separators
- Kubernetes manifest dumping with resource ordering
- Priority key ordering for container-related fields
"""

from .emitter import HumanFriendlyEmitter, HumanFriendlyDumper
from .dumper import dumps, dump
from .multi_document import (
    MultiDocumentDumper,
    KubernetesManifestDumper,
    dump_all,
    dumps_all,
    dump_kubernetes_manifests,
    dumps_kubernetes_manifests,
)

__version__ = "1.0.0"
__all__ = [
    "HumanFriendlyEmitter",
    "HumanFriendlyDumper",
    "dumps",
    "dump",
    "MultiDocumentDumper",
    "KubernetesManifestDumper",
    "dump_all",
    "dumps_all",
    "dump_kubernetes_manifests",
    "dumps_kubernetes_manifests",
]
