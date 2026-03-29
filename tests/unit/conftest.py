"""
Unit test configuration.

Disables the SecurityService rate-limiter for every unit test so that the
100-req/min limit does not trigger when the full test suite is run in a
single process (e.g. via run_knowhow_tests.py).  The original method is
automatically restored after each test via monkeypatch.
"""
import pytest
from app.security_service import security_service


@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch):
    """Replace _check_rate_limit with a no-op that always returns False."""
    monkeypatch.setattr(security_service, '_check_rate_limit', lambda: False)
