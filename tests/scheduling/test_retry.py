from datetime import timedelta

from metis.scheduling.retry import ExponentialBackoffRetryPolicy


def test_exponential_backoff_doubles_delay_by_attempt():
    policy = ExponentialBackoffRetryPolicy(base_delay=timedelta(minutes=1))

    assert policy.next_delay(1) == timedelta(minutes=1)
    assert policy.next_delay(2) == timedelta(minutes=2)
    assert policy.next_delay(3) == timedelta(minutes=4)
