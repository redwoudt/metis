import pytest

from metis.examples.chapter10_background_tasks import run_demo
from metis.scheduling.scheduler import TaskStatus


def test_chapter10_example_crosses_the_time_boundary() -> None:
    result = run_demo(delay_minutes=5)

    assert result["status_before"] == TaskStatus.SCHEDULED
    assert result["due_before"] == 0
    assert result["processed_after_advance"] == 1
    assert result["status_after"] == TaskStatus.COMPLETED


def test_chapter10_example_rejects_non_positive_delay() -> None:
    with pytest.raises(ValueError, match="delay_minutes must be at least 1"):
        run_demo(delay_minutes=0)
