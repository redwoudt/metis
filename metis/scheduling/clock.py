from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


class Clock:
    """
    Small abstraction around "current time".

    Why this exists:
    - Production code should not call datetime.now() everywhere directly.
    - Scheduling, retries, and recurring work are all time-dependent.
    - Tests become deterministic when they can inject a fake clock.

    This is intentionally tiny. The goal is not to build a full time library,
    only to make "now" an explicit dependency in the scheduling subsystem.
    """

    def now(self) -> datetime:
        """
        Return the current UTC time.

        We use timezone-aware UTC timestamps so that scheduling logic does not
        accidentally mix naive and aware datetimes.
        """
        return datetime.now(timezone.utc)


@dataclass
class TestClock(Clock):
    """
    Test double for the Clock abstraction.

    Why this exists:
    - Unit tests should not wait in real time.
    - Tests can advance the fake clock instantly to trigger due tasks or retries.

    __test__ = False prevents pytest from treating this dataclass as a test case.
    """

    __test__ = False
    current_time: datetime

    def now(self) -> datetime:
        """
        Return the controlled test time instead of real system time.
        """
        return self.current_time

    def advance(self, **kwargs) -> datetime:
        """
        Move the test clock forward by a timedelta constructed from kwargs.

        Example:
            clock.advance(minutes=5)

        This allows tests to simulate the passage of time instantly.
        """
        self.current_time = self.current_time + timedelta(**kwargs)
        return self.current_time