import pytest
from metis.dsl.validators import validate_context
from metis.dsl.errors import ValidationError


def test_length_requires_summarize_or_summary():
    # Invalid: length without summarize/summary task
    ctx = {"length": "5 bullet points", "task": "translate"}
    with pytest.raises(ValidationError) as excinfo:
        validate_context(ctx)
    assert "length" in str(excinfo.value).lower()

    # Valid: task is 'summarize'
    ctx_ok = {"length": "5 bullet points", "task": "summarize"}
    validate_context(ctx_ok)  # should not raise

    # Valid: task is 'summary'
    ctx_ok2 = {"length": "short", "task": "summary"}
    validate_context(ctx_ok2)  # should not raise


def test_source_must_be_http_or_https():
    # Invalid: not a URL
    ctx = {"source": "not-a-url", "task": "summarize"}
    with pytest.raises(ValidationError) as excinfo:
        validate_context(ctx)
    assert "source" in str(excinfo.value).lower()

    # Valid: https URL
    ctx_ok = {"source": "https://example.com/doc", "task": "summarize"}
    validate_context(ctx_ok)  # should not raise

    # Valid: http URL
    ctx_ok2 = {"source": "http://example.org/resource", "task": "summarize"}
    validate_context(ctx_ok2)  # should not raise


def test_multiple_rules_trigger_first_violation():
    # If both rules are violated, we expect the first in order to be raised
    ctx = {"length": "5 bullet points", "source": "not-a-url", "task": "translate"}
    with pytest.raises(ValidationError) as excinfo:
        validate_context(ctx)
    # First check is length rule, so that should appear
    assert "length" in str(excinfo.value).lower()