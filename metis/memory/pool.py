"""Flyweight factory and lifecycle manager for shared memory artifacts."""

from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any, Iterable, Mapping, Optional

from metis.memory.artifact import (
    ArtifactKey,
    MemoryReference,
    MissingArtifactError,
    SharedMemoryArtifact,
)


class ArtifactPool:
    """Intern, resolve, retain, and safely evict shared artifacts.

    ``intern`` is the Flyweight factory operation: equivalent content with the
    same tenant, type, and version resolves to the same stored artifact. Pin
    counts express live memento dependencies and prevent unsafe eviction.
    """

    STATE_VERSION = 1

    def __init__(self, max_entries: Optional[int] = None):
        if max_entries is not None and max_entries < 1:
            raise ValueError("max_entries must be positive or None")
        self.max_entries = max_entries
        self._artifacts: "OrderedDict[ArtifactKey, SharedMemoryArtifact]" = (
            OrderedDict()
        )
        self._pins: "Counter[ArtifactKey]" = Counter()

    def intern(
        self,
        *,
        tenant_id: str,
        artifact_type: str,
        version: str,
        content: Any,
    ) -> MemoryReference:
        """Return the canonical reference for a tenant-scoped value."""
        artifact = SharedMemoryArtifact.create(
            tenant_id=tenant_id,
            artifact_type=artifact_type,
            version=version,
            content=content,
        )
        existing = self._artifacts.get(artifact.key)
        if existing is None:
            self._artifacts[artifact.key] = artifact
        else:
            self._artifacts.move_to_end(artifact.key)
        return MemoryReference(artifact.key)

    def get(self, reference: MemoryReference) -> SharedMemoryArtifact:
        """Return the canonical Flyweight or raise a diagnostic error."""
        try:
            artifact = self._artifacts[reference.key]
        except KeyError as exc:
            raise MissingArtifactError(reference) from exc
        self._artifacts.move_to_end(reference.key)
        return artifact

    def resolve(self, reference: MemoryReference) -> Any:
        """Resolve a reference to a fresh, caller-owned value."""
        return self.get(reference).read()

    def retain(self, references: Iterable[MemoryReference]) -> None:
        """Pin artifacts while one or more retained mementos reference them."""
        for reference in references:
            self.get(reference)
            self._pins[reference.key] += 1

    def release(self, references: Iterable[MemoryReference]) -> None:
        """Release memento pins without deleting the underlying artifacts."""
        for reference in references:
            count = self._pins.get(reference.key, 0)
            if count <= 1:
                self._pins.pop(reference.key, None)
            else:
                self._pins[reference.key] = count - 1

    def pin_count(self, reference: MemoryReference) -> int:
        return self._pins.get(reference.key, 0)

    def evict(self, reference: MemoryReference, *, force: bool = False) -> bool:
        """Evict an artifact unless a live memento still depends on it."""
        if reference.key not in self._artifacts:
            return False
        if not force and self._pins.get(reference.key, 0) > 0:
            return False
        del self._artifacts[reference.key]
        self._pins.pop(reference.key, None)
        return True

    def evict_unreferenced(self, target_size: Optional[int] = None) -> int:
        """Evict least-recently-used, unpinned entries down to ``target_size``."""
        target = self.max_entries if target_size is None else target_size
        if target is None:
            return 0
        if target < 0:
            raise ValueError("target_size must be zero or greater")

        removed = 0
        for key in list(self._artifacts.keys()):
            if len(self._artifacts) <= target:
                break
            if self._pins.get(key, 0) > 0:
                continue
            del self._artifacts[key]
            removed += 1
        return removed

    def export_state(self) -> Mapping[str, Any]:
        """Return a pickle-safe representation for the caretaker."""
        return {
            "version": self.STATE_VERSION,
            "max_entries": self.max_entries,
            "artifacts": list(self._artifacts.values()),
            "pins": dict(self._pins),
        }

    def import_state(self, state: Mapping[str, Any]) -> None:
        """Merge a previously exported pool state into this pool."""
        if not isinstance(state, Mapping):
            return
        stored_limit = state.get("max_entries")
        if self.max_entries is None and (
            stored_limit is None or isinstance(stored_limit, int)
        ):
            self.max_entries = stored_limit
        for artifact in state.get("artifacts", []):
            if isinstance(artifact, SharedMemoryArtifact):
                self._artifacts[artifact.key] = artifact
        for key, count in state.get("pins", {}).items():
            if isinstance(key, ArtifactKey) and isinstance(count, int) and count > 0:
                self._pins[key] = count

    def stats(self) -> Mapping[str, int]:
        """Expose observable measures without revealing artifact contents."""
        return {
            "artifacts": len(self._artifacts),
            "pinned_artifacts": sum(1 for count in self._pins.values() if count),
            "references": sum(self._pins.values()),
            "stored_bytes": sum(
                artifact.size_bytes for artifact in self._artifacts.values()
            ),
        }

    def __len__(self) -> int:
        return len(self._artifacts)
