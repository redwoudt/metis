"""
Strategy module housing prompt strategies that customize how model input is generated.

How it works:
- Provides a base PromptStrategy interface.
- Includes Default and Custom strategies for prompt formatting.

Next Steps:
- Add more advanced strategies for task-specific formatting.
- Support dynamic strategy registration or user-defined strategies.
"""

from .base import PromptStrategy
from .default import DefaultPromptStrategy
from .custom import CustomPromptStrategy
