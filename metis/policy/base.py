# Base Policy interface
from abc import ABC, abstractmethod

class Policy(ABC):
    @abstractmethod
    def enforce(self, user_id, request):
        pass
