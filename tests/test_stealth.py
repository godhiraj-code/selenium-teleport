"""Tests for StealthBot-compatible state handling."""

import pytest

from selenium_teleport.exceptions import SSRFError
from selenium_teleport.stealth import load_state_stealth


def test_load_state_stealth_validates_destination_before_navigation(temp_dir):
    """Stealth restores must apply the same destination URL checks."""
    missing_state = f"{temp_dir}/missing.json"

    with pytest.raises(SSRFError):
        load_state_stealth(object(), missing_state, "http://[::1]/admin")
