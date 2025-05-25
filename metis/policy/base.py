"""
Defines the Policy interface for enforcing constraints like access control and rate limiting.

How it works:
- Abstract base class for pluggable enforcement logic.

Next Steps:
- Add methods for policy introspection or metadata.
"""

from abc import ABC, abstractmethod


class Policy(ABC):
    @abstractmethod
    def enforce(self, user_id, request):
        pass
