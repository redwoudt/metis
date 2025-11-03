from abc import ABC, abstractmethod
from typing import Any, Dict

class ModelClient(ABC):
    """Unified contract for all model providers (Adapter interface)."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Must return a normalized dict:
        {
          "text": str,
          "provider": str,
          "model": str,
          "tokens_in": int,
          "tokens_out": int,
          "latency_ms": int,
          "cost": float,
        }
        """
        raise NotImplementedError