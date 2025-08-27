"""
Type stubs for yaml-for-humans package.
"""

from typing import List

from .emitter import (
    HumanFriendlyEmitter as HumanFriendlyEmitter,
    HumanFriendlyDumper as HumanFriendlyDumper,
)
from .dumper import dumps as dumps, dump as dump
from .multi_document import (
    MultiDocumentDumper as MultiDocumentDumper,
    KubernetesManifestDumper as KubernetesManifestDumper,
    dump_all as dump_all,
    dumps_all as dumps_all,
    dump_kubernetes_manifests as dump_kubernetes_manifests,
    dumps_kubernetes_manifests as dumps_kubernetes_manifests,
)

__version__: str

__all__: list[str]
