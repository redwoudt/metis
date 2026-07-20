"""Immutable, content-addressed artifacts used by conversation memory.

The payload is stored as canonical JSON rather than as a mutable Python object.
Callers receive a freshly decoded value whenever they resolve an artifact, so a
conversation cannot accidentally change the shared representation in place.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


def encode_content(content: Any) -> str:
    """Return a deterministic JSON representation of an artifact payload."""
    try:
        return json.dumps(
            content,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise TypeError(
            "Shared memory artifacts must contain JSON-serializable values"
        ) from exc


@dataclass(frozen=True)
class ArtifactKey:
    """The tenant-scoped identity of a shared artifact."""

    tenant_id: str
    artifact_type: str
    version: str
    content_hash: str

    @property
    def identifier(self) -> str:
        """Return a stable identifier suitable for logs and diagnostics."""
        return ":".join(
            (self.tenant_id, self.artifact_type, self.version, self.content_hash)
        )


@dataclass(frozen=True)
class MemoryReference:
    """A lightweight reference stored inside a conversation memento."""

    key: ArtifactKey

    @property
    def identifier(self) -> str:
        return self.key.identifier


@dataclass(frozen=True)
class SharedMemoryArtifact:
    """A Flyweight containing immutable, shareable conversation knowledge."""

    key: ArtifactKey
    encoded_content: str

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        artifact_type: str,
        version: str,
        content: Any,
    ) -> "SharedMemoryArtifact":
        encoded = encode_content(content)
        digest = sha256(encoded.encode("utf-8")).hexdigest()
        key = ArtifactKey(
            tenant_id=str(tenant_id),
            artifact_type=str(artifact_type),
            version=str(version),
            content_hash=digest,
        )
        return cls(key=key, encoded_content=encoded)

    def read(self) -> Any:
        """Decode a fresh value so callers cannot mutate the shared payload."""
        return json.loads(self.encoded_content)

    @property
    def size_bytes(self) -> int:
        return len(self.encoded_content.encode("utf-8"))


class MissingArtifactError(KeyError):
    """Raised when a memento points to an artifact that is no longer present."""

    def __init__(self, reference: MemoryReference):
        self.reference = reference
        super().__init__(
            "Cannot restore conversation memory because artifact "
            f"'{reference.identifier}' is missing"
        )
