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
from .dumper import dumps, dump, load_with_formatting
from .formatting_aware import FormattingAwareLoader
from .formatting_emitter import FormattingAwareDumper
from .multi_document import (
    MultiDocumentDumper,
    KubernetesManifestDumper,
    dump_all,
    dumps_all,
    dump_kubernetes_manifests,
    dumps_kubernetes_manifests,
)

try:
    import importlib.metadata

    __version__: str = importlib.metadata.version("yaml-for-humans")
except (importlib.metadata.PackageNotFoundError, ImportError):
    # Fallback for development installs
    __version__: str = "1.0.4"
__all__: list[str] = [
    "HumanFriendlyEmitter",
    "HumanFriendlyDumper",
    "dumps",
    "dump",
    "load_with_formatting",
    "FormattingAwareLoader",
    "FormattingAwareDumper",
    "MultiDocumentDumper",
    "KubernetesManifestDumper",
    "dump_all",
    "dumps_all",
    "dump_kubernetes_manifests",
    "dumps_kubernetes_manifests",
]
