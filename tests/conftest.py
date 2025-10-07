# conftest.py
import os
import pytest
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(name)s:%(lineno)d %(message)s",
)

SESSION_FILE = "metis/sessions.pkl"  # Adjust path if necessary

@pytest.fixture(scope="session", autouse=True)
def remove_old_sessions_pickle():
    """
    Ensure stale session pickle file is removed before test run.
    Prevents ModuleNotFoundError from outdated pickled class references.
    """
    try:
        os.remove(SESSION_FILE)
        print(f"✅ Removed old session file: {SESSION_FILE}")
    except FileNotFoundError:
        pass