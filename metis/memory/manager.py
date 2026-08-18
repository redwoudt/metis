"""Caretaker for legacy snapshots and reference-based conversation mementos."""

from __future__ import annotations

import os
import pickle
from typing import Any, Optional

from metis.memory.pool import ArtifactPool
from metis.memory.snapshot import ConversationMemento, ConversationSnapshot


class MemoryManager:
    """Persist checkpoints while protecting every artifact they reference.

    Legacy ``ConversationSnapshot`` objects remain supported. Chapter 14
    mementos add lifecycle-aware retain/release behaviour and are stored beside
    the pool state in a versioned on-disk envelope.
    """

    STORAGE_VERSION = 3

    def __init__(
        self,
        file_path: str = "snapshots.pkl",
        *,
        artifact_pool: Optional[ArtifactPool] = None,
        max_snapshots: Optional[int] = None,
    ):
        if max_snapshots is not None and max_snapshots < 1:
            raise ValueError("max_snapshots must be positive or None")
        self._file_path = file_path
        self._artifact_pool = (
            artifact_pool if artifact_pool is not None else ArtifactPool()
        )
        self._max_snapshots = max_snapshots
        self._snapshots: list[Any] = []
        self._scopes: list[str | None] = []
        self._load_from_disk()

    @property
    def artifact_pool(self) -> ArtifactPool:
        return self._artifact_pool

    def _load_from_disk(self) -> None:
        """Load both the legacy list and the Chapter 14 storage envelope."""
        if not os.path.exists(self._file_path):
            return
        try:
            with open(self._file_path, "rb") as stream:
                stored = pickle.load(stream)
        except Exception:
            return

        if isinstance(stored, list):
            self._snapshots = stored
            self._scopes = [None] * len(stored)
            return

        if not isinstance(stored, dict):
            return
        snapshots = stored.get("snapshots", [])
        if isinstance(snapshots, list):
            self._snapshots = snapshots
        scopes = stored.get("scopes", [])
        if isinstance(scopes, list) and len(scopes) == len(self._snapshots):
            self._scopes = [str(scope) if scope is not None else None for scope in scopes]
        else:
            self._scopes = [None] * len(self._snapshots)
        pool_state = stored.get("artifact_pool")
        if isinstance(pool_state, dict):
            self._artifact_pool.import_state(pool_state)

    def _save_to_disk(self) -> None:
        """Atomically persist checkpoints and the artifacts needed to restore them."""
        directory = os.path.dirname(os.path.abspath(self._file_path))
        os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self._file_path}.tmp"
        payload = {
            "storage_version": self.STORAGE_VERSION,
            "snapshots": self._snapshots,
            "scopes": self._scopes,
            "artifact_pool": dict(self._artifact_pool.export_state()),
        }
        with open(temporary_path, "wb") as stream:
            pickle.dump(payload, stream)
        os.replace(temporary_path, self._file_path)

    @staticmethod
    def _memento_references(snapshot: Any):
        if isinstance(snapshot, ConversationMemento):
            return snapshot.references
        return ()

    def save(self, snapshot: Any, *, scope: str | None = None) -> None:
        """Retain a checkpoint and pin all artifacts on which it depends."""
        if snapshot is None:
            return
        references = self._memento_references(snapshot)
        if references:
            self._artifact_pool.retain(references)
        self._snapshots.append(snapshot)
        self._scopes.append(str(scope) if scope is not None else None)
        self._trim_to_limit()
        self._artifact_pool.evict_unreferenced()
        self._save_to_disk()

    def _trim_to_limit(self) -> None:
        if self._max_snapshots is None:
            return
        while len(self._snapshots) > self._max_snapshots:
            removed = self._snapshots.pop(0)
            self._scopes.pop(0)
            self._artifact_pool.release(self._memento_references(removed))

    def trim(self, keep_latest: int) -> int:
        """Discard older checkpoints and release their artifact dependencies."""
        if keep_latest < 0:
            raise ValueError("keep_latest must be zero or greater")
        remove_count = max(0, len(self._snapshots) - keep_latest)
        removed = self._snapshots[:remove_count]
        self._snapshots = self._snapshots[remove_count:]
        self._scopes = self._scopes[remove_count:]
        for snapshot in removed:
            self._artifact_pool.release(self._memento_references(snapshot))
        self._artifact_pool.evict_unreferenced()
        self._save_to_disk()
        return len(removed)

    def _latest_index(self, scope: str | None = None) -> int | None:
        if scope is None:
            return len(self._snapshots) - 1 if self._snapshots else None
        requested = str(scope)
        for index in range(len(self._snapshots) - 1, -1, -1):
            if self._scopes[index] == requested:
                return index
        return None

    def restore_into(self, originator: Any, *, scope: str | None = None) -> bool:
        """Restore and consume the latest checkpoint as one safe lifecycle step.

        The checkpoint is removed and its references are released only after the
        originator has successfully resolved and restored it.
        """
        index = self._latest_index(scope)
        if index is None:
            return False
        snapshot = self._snapshots[index]
        if isinstance(snapshot, ConversationMemento):
            originator.restore_snapshot(snapshot, artifact_pool=self._artifact_pool)
        else:
            originator.restore_snapshot(snapshot)
        self._snapshots.pop(index)
        self._scopes.pop(index)
        self._artifact_pool.release(self._memento_references(snapshot))
        self._artifact_pool.evict_unreferenced()
        self._save_to_disk()
        return True

    def restore_last(self, *, scope: str | None = None):
        """Pop the latest checkpoint, preserving the earlier public API.

        A returned lean memento remains pinned until ``release`` is called. New
        code should prefer ``restore_into`` so resolving and releasing happen as
        one operation.
        """
        index = self._latest_index(scope)
        if index is not None:
            snapshot = self._snapshots.pop(index)
            self._scopes.pop(index)
            self._save_to_disk()
            return snapshot
        return ConversationSnapshot({})

    def release(self, snapshot: Any) -> None:
        """Release a memento obtained with the compatibility ``restore_last`` API."""
        self._artifact_pool.release(self._memento_references(snapshot))
        self._artifact_pool.evict_unreferenced()
        self._save_to_disk()

    def clear(self, *, scope: str | None = None) -> None:
        """Clear saved checkpoints and release their dependencies."""
        if scope is None:
            removed = list(self._snapshots)
            self._snapshots.clear()
            self._scopes.clear()
        else:
            requested = str(scope)
            removed = []
            retained_snapshots = []
            retained_scopes = []
            for snapshot, saved_scope in zip(self._snapshots, self._scopes):
                if saved_scope == requested:
                    removed.append(snapshot)
                else:
                    retained_snapshots.append(snapshot)
                    retained_scopes.append(saved_scope)
            self._snapshots = retained_snapshots
            self._scopes = retained_scopes

        for snapshot in removed:
            self._artifact_pool.release(self._memento_references(snapshot))
        self._artifact_pool.evict_unreferenced()
        self._save_to_disk()

    def count(self, *, scope: str | None = None) -> int:
        """Return the number of retained checkpoints, optionally by scope."""
        if scope is None:
            return len(self._snapshots)
        requested = str(scope)
        return sum(saved_scope == requested for saved_scope in self._scopes)

    def __len__(self) -> int:
        return len(self._snapshots)
