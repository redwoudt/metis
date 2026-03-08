from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta


class RetryPolicy(ABC):
    """
    Strategy interface for retry timing.

    Why this exists:
    - Not all tasks should retry in the same way.
    - Some may retry aggressively.
    - Others may use exponential backoff to avoid overwhelming dependencies.
    - Some may eventually support jitter, circuit breakers, or provider-specific rules.

    This is a direct use of the Strategy Pattern from earlier chapters.
    """

    @abstractmethod
    def next_delay(self, attempt: int) -> timedelta:
        """
        Return the delay before the next retry attempt.

        attempt is the 1-based retry count after a failure.
        """
        raise NotImplementedError


class FixedDelayRetryPolicy(RetryPolicy):
    """
    Retry strategy that always waits the same amount of time.

    Good for:
    - simple chapter examples
    - predictable retry behavior
    - tests where stable timing is easier to reason about
    """

    def __init__(self, delay: timedelta = timedelta(minutes=1)):
        self.delay = delay

    def next_delay(self, attempt: int) -> timedelta:
        """
        Ignore the attempt number and always return the same delay.
        """
        return self.delay


class ExponentialBackoffRetryPolicy(RetryPolicy):
    """
    Retry strategy where delay increases with each attempt.

    Good for:
    - temporary outages
    - avoiding hammering external APIs
    - more production-like retry behavior

    Example with base_delay=1 minute:
        attempt 1 -> 1 minute
        attempt 2 -> 2 minutes
        attempt 3 -> 4 minutes
    """

    def __init__(self, base_delay: timedelta = timedelta(minutes=1)):
        self.base_delay = base_delay

    def next_delay(self, attempt: int) -> timedelta:
        """
        Return exponentially increasing delay.

        We use max(attempt - 1, 0) so that attempt=1 returns the base delay.
        """
        return self.base_delay * (2 ** max(attempt - 1, 0))