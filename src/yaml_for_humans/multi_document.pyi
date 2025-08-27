"""
Type stubs for multi_document module.
"""

from typing import Any, Dict, List, Iterable, Union, IO, TextIO, Optional
from typing_extensions import TypeAlias

# Type aliases
YAMLObject: TypeAlias = Union[dict[str, Any], list[Any], str, int, float, bool, None]
StreamType: TypeAlias = Union[IO[str], TextIO]
KubernetesResource: TypeAlias = dict[str, Any]

class MultiDocumentDumper:
    """
    Dumper for multiple YAML documents with human-friendly formatting.
    """

    stream: StreamType
    dumper_kwargs: dict[str, Any]

    def __init__(
        self,
        stream: Optional[StreamType] = ...,
        *,
        default_flow_style: Optional[bool] = ...,
        indent: Optional[int] = ...,
        sort_keys: Optional[bool] = ...,
        explicit_start: Optional[bool] = ...,
        explicit_end: Optional[bool] = ...,
        **dumper_kwargs: Any,
    ) -> None:
        """
        Initialize the multi-document dumper.

        Args:
            stream: Output stream (defaults to StringIO for dumps_all)
            **dumper_kwargs: Additional arguments passed to HumanFriendlyDumper
        """
        ...

    def dump_document(self, data: YAMLObject) -> None:
        """
        Dump a single document to the stream.

        Args:
            data: Python object to serialize as a YAML document
        """
        ...

    def dump_all(self, documents: Iterable[YAMLObject]) -> None:
        """
        Dump multiple documents to the stream.

        Args:
            documents: Iterable of Python objects to serialize
        """
        ...

    def getvalue(self) -> str:
        """
        Get the dumped YAML as a string (only works if stream is StringIO).

        Returns:
            The complete multi-document YAML string
        """
        ...

class KubernetesManifestDumper(MultiDocumentDumper):
    """
    Specialized multi-document dumper for Kubernetes manifests.
    """

    RESOURCE_ORDER: list[str]
    sort_resources: bool

    def __init__(
        self,
        stream: Optional[StreamType] = ...,
        sort_resources: bool = ...,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Kubernetes manifest dumper.

        Args:
            stream: Output stream
            sort_resources: Whether to sort resources by kind
            **kwargs: Additional dumper arguments
        """
        ...

    def dump_all(self, documents: Iterable[YAMLObject]) -> None:
        """
        Dump Kubernetes manifests with optional resource ordering.

        Args:
            documents: Iterable of Kubernetes resource objects
        """
        ...

    def _sort_resources(
        self, documents: Iterable[KubernetesResource]
    ) -> List[KubernetesResource]:
        """
        Sort Kubernetes resources by kind according to best practices.

        Args:
            documents: Iterable of Kubernetes resource objects

        Returns:
            List of sorted documents
        """
        ...

def dump_all(
    documents: Iterable[YAMLObject],
    stream: StreamType,
    **kwargs: Any,
) -> None:
    """
    Serialize multiple Python objects to YAML documents in a stream.

    Args:
        documents: Iterable of Python objects to serialize
        stream: File-like object to write to
        **kwargs: Additional arguments passed to MultiDocumentDumper
    """
    ...

def dumps_all(
    documents: Iterable[YAMLObject],
    **kwargs: Any,
) -> str:
    """
    Serialize multiple Python objects to a multi-document YAML string.

    Args:
        documents: Iterable of Python objects to serialize
        **kwargs: Additional arguments passed to MultiDocumentDumper

    Returns:
        Multi-document YAML string
    """
    ...

def dump_kubernetes_manifests(
    manifests: Iterable[KubernetesResource],
    stream: StreamType,
    **kwargs: Any,
) -> None:
    """
    Dump Kubernetes manifests with proper resource ordering.

    Args:
        manifests: Iterable of Kubernetes resource objects
        stream: File-like object to write to
        **kwargs: Additional arguments
    """
    ...

def dumps_kubernetes_manifests(
    manifests: Iterable[KubernetesResource],
    **kwargs: Any,
) -> str:
    """
    Serialize Kubernetes manifests to a multi-document YAML string.

    Args:
        manifests: Iterable of Kubernetes resource objects
        **kwargs: Additional arguments

    Returns:
        Multi-document YAML string with proper resource ordering
    """
    ...
