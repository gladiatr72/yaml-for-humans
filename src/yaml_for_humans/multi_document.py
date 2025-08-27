"""
Multi-document YAML dumper with human-friendly formatting.

This module provides functionality for dumping multiple YAML documents
to a single stream while maintaining the human-friendly formatting
for sequences and key ordering.
"""

from io import StringIO

import yaml
from .emitter import HumanFriendlyDumper


class MultiDocumentDumper:
    """
    Dumper for multiple YAML documents with human-friendly formatting.

    Handles document separators (---) and document end markers (...)
    while applying human-friendly formatting to each document.
    """

    def __init__(self, stream=None, **dumper_kwargs):
        """
        Initialize the multi-document dumper.

        Args:
            stream: Output stream (defaults to StringIO for dumps_all)
            **dumper_kwargs: Additional arguments passed to HumanFriendlyDumper
        """
        self.stream = stream or StringIO()
        self.dumper_kwargs = {
            "default_flow_style": False,
            "indent": 2,
            "sort_keys": False,
            "explicit_start": True,  # Add --- separators
            "explicit_end": False,  # Don't add ... end markers by default
            **dumper_kwargs,
        }
        self._first_document = True

    def dump_document(self, data):
        """
        Dump a single document to the stream.

        Args:
            data: Python object to serialize as a YAML document
        """
        # For first document, don't add separator at start
        if self._first_document:
            # First document: no explicit start separator
            dumper_kwargs = dict(self.dumper_kwargs)
            dumper_kwargs["explicit_start"] = False
            yaml.dump(data, self.stream, Dumper=HumanFriendlyDumper, **dumper_kwargs)
            self._first_document = False
        else:
            # Subsequent documents: add newline and separator
            self.stream.write("\n---\n")
            # Don't use explicit_start for subsequent docs since we manually add separator
            dumper_kwargs = dict(self.dumper_kwargs)
            dumper_kwargs["explicit_start"] = False
            yaml.dump(data, self.stream, Dumper=HumanFriendlyDumper, **dumper_kwargs)

    def dump_all(self, documents):
        """
        Dump multiple documents to the stream.

        Args:
            documents: Iterable of Python objects to serialize
        """
        for document in documents:
            self.dump_document(document)

    def getvalue(self):
        """
        Get the dumped YAML as a string (only works if stream is StringIO).

        Returns:
            str: The complete multi-document YAML string
        """
        if hasattr(self.stream, "getvalue"):
            return self.stream.getvalue()
        else:
            raise ValueError("Stream does not support getvalue()")


def dump_all(documents, stream, **kwargs):
    """
    Serialize multiple Python objects to YAML documents in a stream.

    Args:
        documents: Iterable of Python objects to serialize
        stream: File-like object to write to
        **kwargs: Additional arguments passed to MultiDocumentDumper

    Example:
        documents = [
            {'apiVersion': 'v1', 'kind': 'ConfigMap'},
            {'apiVersion': 'v1', 'kind': 'Service'},
            {'apiVersion': 'apps/v1', 'kind': 'Deployment'}
        ]
        with open('multi.yaml', 'w') as f:
            dump_all(documents, f)
    """
    dumper = MultiDocumentDumper(stream, **kwargs)
    dumper.dump_all(documents)


def dumps_all(documents, **kwargs):
    """
    Serialize multiple Python objects to a multi-document YAML string.

    Args:
        documents: Iterable of Python objects to serialize
        **kwargs: Additional arguments passed to MultiDocumentDumper

    Returns:
        str: Multi-document YAML string

    Example:
        documents = [
            {'kind': 'ConfigMap', 'data': {'key': 'value'}},
            {'kind': 'Service', 'spec': {'ports': [80, 443]}}
        ]
        yaml_str = dumps_all(documents)
        print(yaml_str)
    """
    dumper = MultiDocumentDumper(**kwargs)
    dumper.dump_all(documents)
    return dumper.getvalue()


class KubernetesManifestDumper(MultiDocumentDumper):
    """
    Specialized multi-document dumper for Kubernetes manifests.

    Provides additional functionality specific to Kubernetes YAML files,
    such as automatic resource ordering and validation.
    """

    # Kubernetes resource ordering (CRDs and namespaces first, etc.)
    RESOURCE_ORDER = [
        "CustomResourceDefinition",
        "Namespace",
        "ServiceAccount",
        "ClusterRole",
        "ClusterRoleBinding",
        "Role",
        "RoleBinding",
        "ConfigMap",
        "Secret",
        "PersistentVolume",
        "PersistentVolumeClaim",
        "Service",
        "Ingress",
        "NetworkPolicy",
        "Deployment",
        "StatefulSet",
        "DaemonSet",
        "Job",
        "CronJob",
        "Pod",
    ]

    def __init__(self, stream=None, sort_resources=True, **kwargs):
        """
        Initialize Kubernetes manifest dumper.

        Args:
            stream: Output stream
            sort_resources: Whether to sort resources by kind
            **kwargs: Additional dumper arguments
        """
        super().__init__(stream, **kwargs)
        self.sort_resources = sort_resources

    def dump_all(self, documents):
        """
        Dump Kubernetes manifests with optional resource ordering.

        Args:
            documents: Iterable of Kubernetes resource objects
        """
        if self.sort_resources:
            documents = self._sort_resources(documents)

        super().dump_all(documents)

    def _sort_resources(self, documents):
        """
        Sort Kubernetes resources by kind according to best practices.

        Args:
            documents: Iterable of Kubernetes resource objects

        Returns:
            List of sorted documents
        """
        document_list = list(documents)

        def get_kind_priority(doc):
            """Get sorting priority for a document based on its kind."""
            kind = doc.get("kind", "Unknown")
            try:
                return self.RESOURCE_ORDER.index(kind)
            except ValueError:
                return len(self.RESOURCE_ORDER)  # Unknown kinds go last

        return sorted(document_list, key=get_kind_priority)


def dump_kubernetes_manifests(manifests, stream, **kwargs):
    """
    Dump Kubernetes manifests with proper resource ordering.

    Args:
        manifests: Iterable of Kubernetes resource objects
        stream: File-like object to write to
        **kwargs: Additional arguments

    Example:
        manifests = [
            {'apiVersion': 'apps/v1', 'kind': 'Deployment', ...},
            {'apiVersion': 'v1', 'kind': 'Service', ...},
            {'apiVersion': 'v1', 'kind': 'ConfigMap', ...}
        ]
        with open('k8s-manifests.yaml', 'w') as f:
            dump_kubernetes_manifests(manifests, f)
    """
    dumper = KubernetesManifestDumper(stream, **kwargs)
    dumper.dump_all(manifests)


def dumps_kubernetes_manifests(manifests, **kwargs):
    """
    Serialize Kubernetes manifests to a multi-document YAML string.

    Args:
        manifests: Iterable of Kubernetes resource objects
        **kwargs: Additional arguments

    Returns:
        str: Multi-document YAML string with proper resource ordering
    """
    dumper = KubernetesManifestDumper(**kwargs)
    dumper.dump_all(manifests)
    return dumper.getvalue()
