"""Full snapshots and lean, reference-based conversation mementos."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping, Tuple

from metis.memory.artifact import MemoryReference, encode_content
from metis.memory.pool import ArtifactPool


class ConversationSnapshot:
    """
    Acts as the Memento in the Memento Pattern.
    Encapsulates a deep copy of the Originator's internal state at a point in time.
    """

    def __init__(self, state_data):
        """
        Create a snapshot of the provided state data.

        :param state_data: A dictionary representing the Originator's internal state (typically __dict__).
        """
        self._state_data = copy.deepcopy(state_data)  # Ensure no shared references

    def get_state(self):
        """
        Retrieve a deep copy of the saved state.
        Used by the Originator to restore its own state safely.

        :return: A deep copy of the saved internal state dictionary.
        """
        return copy.deepcopy(self._state_data)


@dataclass(frozen=True)
class ConversationMemento:
    """A lean checkpoint containing references plus session-specific state.

    Unlike ``ConversationSnapshot``, this object does not copy model clients,
    prompt text, tool schemas, safety policies, or history payloads. Those
    values live in the artifact pool and are addressed by immutable references.
    """

    schema_version: int
    state_type: str
    model_role: str
    preferences_json: str
    history_refs: Tuple[MemoryReference, ...]
    artifact_refs: Tuple[Tuple[str, MemoryReference], ...]

    CURRENT_SCHEMA_VERSION = 2

    @classmethod
    def create(
        cls,
        *,
        state_type: str,
        model_role: str,
        preferences: Mapping[str, Any],
        history_refs: Iterable[MemoryReference],
        artifact_refs: Mapping[str, MemoryReference],
    ) -> "ConversationMemento":
        return cls(
            schema_version=cls.CURRENT_SCHEMA_VERSION,
            state_type=state_type,
            model_role=model_role,
            preferences_json=encode_content(dict(preferences)),
            history_refs=tuple(history_refs),
            artifact_refs=tuple(sorted(artifact_refs.items())),
        )

    @property
    def references(self) -> Tuple[MemoryReference, ...]:
        """Return every artifact dependency held by this checkpoint."""
        return self.history_refs + tuple(ref for _, ref in self.artifact_refs)

    def restore_data(self, pool: ArtifactPool) -> Mapping[str, Any]:
        """Resolve a checkpoint into state owned by the restoring conversation."""
        if self.schema_version != self.CURRENT_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported conversation memento schema version: "
                f"{self.schema_version}"
            )
        return {
            "state_type": self.state_type,
            "model_role": self.model_role,
            "preferences": json.loads(self.preferences_json),
            "history": [pool.resolve(ref) for ref in self.history_refs],
            "shared_artifacts": {
                name: pool.resolve(ref) for name, ref in self.artifact_refs
            },
        }
