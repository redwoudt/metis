import pytest
from metis.policy.auth import AuthPolicy
from metis.policy.rate_limit import RateLimitPolicy


def test_auth_policy_accept():
    policy = AuthPolicy()
    policy.enforce("user_abc", "request")  # Should not raise


def test_auth_policy_reject():
    policy = AuthPolicy()
    with pytest.raises(PermissionError):
        policy.enforce("guest_abc", "request")


def test_rate_limit_policy():
    policy = RateLimitPolicy()
    for _ in range(5):
        policy.enforce("user_123", "req")
    with pytest.raises(PermissionError):
        policy.enforce("user_123", "req")
