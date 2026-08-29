"""Tests for state-management context managers."""

import pytest

from selenium_teleport.context import teleport_session
from selenium_teleport.exceptions import DomainMismatchError


def test_teleport_session_does_not_suppress_security_errors(mock_driver, state_file):
    """Automatic restore must fail closed on a source/destination mismatch."""
    with pytest.raises(DomainMismatchError):
        with teleport_session(mock_driver, state_file, "https://evil.com/dashboard"):
            pass

    mock_driver.get.assert_not_called()
