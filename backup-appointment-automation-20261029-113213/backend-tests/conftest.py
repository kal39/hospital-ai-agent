"""Keep automated tests isolated from persistent demo state."""

import os

import pytest

os.environ["HOSPITAL_DEMO_DATABASE_PATH"] = ":memory:"


@pytest.fixture(autouse=True)
def isolate_rate_limit_state():
    """Prevent request counts from leaking between independent tests."""
    from app.core.rate_limit import reset_rate_limit_state

    reset_rate_limit_state()
    yield
    reset_rate_limit_state()
