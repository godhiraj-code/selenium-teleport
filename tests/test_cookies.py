"""
Tests for cookie handling.
"""

import pytest


class TestCookieSanitization:
    """Tests for cookie sanitization."""

    def test_sanitize_expiry_float_to_int(self):
        """Test that float expiry is converted to int."""
        from selenium_teleport.cookies import sanitize_cookie

        cookie = {"name": "test", "value": "val", "expiry": 1705300800.5}
        sanitized = sanitize_cookie(cookie)

        assert sanitized["expiry"] == 1705300800
        assert isinstance(sanitized["expiry"], int)

    def test_sanitize_same_site_normalization(self):
        """Test sameSite attribute normalization."""
        from selenium_teleport.cookies import sanitize_cookie

        cookie = {"name": "test", "value": "val", "sameSite": "strict"}
        sanitized = sanitize_cookie(cookie)
        assert sanitized["sameSite"] == "Strict"

        cookie = {"name": "test", "value": "val", "sameSite": "LAX"}
        sanitized = sanitize_cookie(cookie)
        assert sanitized["sameSite"] == "Lax"

    def test_sanitize_removes_invalid_same_site(self):
        """Test that invalid sameSite values are removed."""
        from selenium_teleport.cookies import sanitize_cookie

        cookie = {"name": "test", "value": "val", "sameSite": "invalid"}
        sanitized = sanitize_cookie(cookie)
        assert "sameSite" not in sanitized

    def test_sanitize_removes_none_values(self):
        """Test that None values are removed."""
        from selenium_teleport.cookies import sanitize_cookie

        cookie = {"name": "test", "value": "val", "httpOnly": None, "secure": None}
        sanitized = sanitize_cookie(cookie)

        assert "httpOnly" not in sanitized
        assert "secure" not in sanitized


class TestCookieFiltering:
    """Tests for cookie filtering functions."""

    def test_filter_by_domain(self):
        """Test filtering cookies by domain."""
        from selenium_teleport.cookies import filter_cookies_by_domain

        cookies = [
            {"name": "c1", "value": "v1", "domain": "example.com"},
            {"name": "c2", "value": "v2", "domain": ".example.com"},
            {"name": "c3", "value": "v3", "domain": "other.com"},
        ]

        filtered = filter_cookies_by_domain(cookies, "example.com")

        assert len(filtered) == 2
        assert all(c["domain"].endswith("example.com") for c in filtered)

    def test_get_auth_cookies(self):
        """Test filtering for auth cookies."""
        from selenium_teleport.cookies import get_auth_cookies

        cookies = [
            {"name": "session_id", "value": "abc"},
            {"name": "auth_token", "value": "xyz"},
            {"name": "theme", "value": "dark"},
            {"name": "last_visit", "value": "today"},
        ]

        auth = get_auth_cookies(cookies)

        assert len(auth) == 2
        assert any(c["name"] == "session_id" for c in auth)
        assert any(c["name"] == "auth_token" for c in auth)


class TestCookieInjection:
    """Tests for cookie injection."""

    def test_inject_cookies(self, mock_driver):
        """Test injecting cookies into driver."""
        from selenium_teleport.cookies import inject_cookies

        cookies = [
            {"name": "c1", "value": "v1", "domain": "example.com"},
            {"name": "c2", "value": "v2", "domain": "example.com"},
        ]

        count = inject_cookies(mock_driver, cookies)

        assert count == 2
        assert mock_driver.add_cookie.call_count == 2
