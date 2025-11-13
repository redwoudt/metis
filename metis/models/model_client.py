# metis/models/model_client.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ModelClient(ABC):
    """
    Minimal abstract interface for all model clients used by Metis.
    Concrete provider adapters (OpenAI, Anthropic, Mock, etc.) may or
    may not inherit from this, but the proxy *does* so tests can assert
    `isinstance(proxy, ModelClient)`.

    The contract is intentionally small:
      - `generate(prompt, **kwargs) -> str` must return text.
      - Optional metadata helpers have sane defaults.
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:  # pragma: no cover
        """
        Produce a textual completion from the given prompt.
        Implementations should NOT raise on normal provider failures;
        they should handle/retry and return a best-effort string.
        """
        raise NotImplementedError

    # ---- Optional metadata helpers (non-abstract) ---------------------

    def name(self) -> str:
        """Human-friendly client name (e.g., 'OpenAI', 'Anthropic', 'Mock')."""
        return self.__class__.__name__

    def vendor(self) -> Optional[str]:
        """Provider/vendor id (e.g., 'openai', 'anthropic', 'mock')."""
        return None

    def model(self) -> Optional[str]:
        """Model id/name (e.g., 'gpt-4o-mini', 'claude-3-sonnet')."""
        return None

    def last_usage(self) -> Dict[str, Any]:
        """
        Optional: usage/cost/latency details from the last call.
        Implementations can override to expose richer telemetry.
        """
        return {}

    # String representation helpful in logs
    def __repr__(self) -> str:
        v = self.vendor() or "unknown"
        m = self.model() or "unknown"
        return f"<{self.__class__.__name__} vendor={v} model={m}>"