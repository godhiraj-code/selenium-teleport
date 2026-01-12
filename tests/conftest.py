"""
Pytest configuration and fixtures for selenium-teleport tests.
"""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_state() -> Dict[str, Any]:
    """Create a sample browser state for testing."""
    import time

    return {
        "metadata": {
            "saved_at": "2024-01-15T10:30:00",
            "source_url": "https://example.com/dashboard",
            "source_domain": "https://example.com",
            "version": "2.1",
        },
        "cookies": [
            {
                "name": "session_id",
                "value": "abc123xyz",
                "domain": "example.com",
                "path": "/",
                "expiry": int(time.time()) + 86400,  # 24 hours from now
                "secure": True,
                "httpOnly": True,
            },
            {
                "name": "auth_token",
                "value": "token_value",
                "domain": ".example.com",
                "path": "/",
                "expiry": int(time.time()) + 3600,  # 1 hour from now
            },
        ],
        "localStorage": {
            "user_preferences": '{"theme": "dark"}',
            "last_visit": "2024-01-15",
        },
        "sessionStorage": {
            "temp_data": "some_value",
        },
        "indexedDB": {},
    }


@pytest.fixture
def expired_state() -> Dict[str, Any]:
    """Create a state with expired cookies."""
    import time

    return {
        "metadata": {
            "saved_at": "2024-01-01T10:30:00",
            "source_url": "https://example.com/dashboard",
            "source_domain": "https://example.com",
            "version": "2.1",
        },
        "cookies": [
            {
                "name": "expired_session",
                "value": "old_value",
                "domain": "example.com",
                "path": "/",
                "expiry": int(time.time()) - 86400,  # Expired 24 hours ago
            },
        ],
        "localStorage": {},
        "sessionStorage": {},
    }


@pytest.fixture
def state_file(temp_dir, sample_state):
    """Create a temporary state file."""
    file_path = os.path.join(temp_dir, "test_state.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_state, f)
    return file_path


@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver."""
    driver = MagicMock()
    driver.current_url = "https://example.com/dashboard"
    driver.get_cookies.return_value = [
        {
            "name": "test_cookie",
            "value": "test_value",
            "domain": "example.com",
            "path": "/",
        }
    ]

    # Mock execute_script for storage extraction
    def mock_execute_script(script):
        if "localStorage" in script and "return" in script:
            return {"test_key": "test_value"}
        if "sessionStorage" in script and "return" in script:
            return {"session_key": "session_value"}
        if "indexedDB" in script:
            return {}
        return None

    driver.execute_script.side_effect = mock_execute_script

    return driver


@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    # Import here to avoid errors if cryptography not installed
    try:
        from selenium_teleport.security import generate_key

        return generate_key()
    except ImportError:
        pytest.skip("cryptography not installed")
