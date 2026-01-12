"""
Tests for the security module.
"""

import os
import time

import pytest


class TestEncryption:
    """Tests for encryption/decryption functions."""

    def test_generate_key(self):
        """Test encryption key generation."""
        try:
            from selenium_teleport.security import generate_key
        except ImportError:
            pytest.skip("cryptography not installed")

        key = generate_key()
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet key length

    def test_encrypt_decrypt_roundtrip(self, sample_state, encryption_key):
        """Test that encryption and decryption produce original data."""
        from selenium_teleport.security import decrypt_state, encrypt_state

        encrypted = encrypt_state(sample_state, encryption_key)
        assert isinstance(encrypted, bytes)
        assert encrypted.startswith(b"gAAAAA")  # Fernet prefix

        decrypted = decrypt_state(encrypted, encryption_key)
        assert decrypted == sample_state

    def test_encrypt_without_key_raises_error(self, sample_state):
        """Test that encryption without key raises error."""
        from selenium_teleport.exceptions import EncryptionError
        from selenium_teleport.security import encrypt_state

        with pytest.raises(EncryptionError):
            encrypt_state(sample_state, None)

    def test_decrypt_with_wrong_key_raises_error(self, sample_state, encryption_key):
        """Test that decryption with wrong key raises error."""
        from selenium_teleport.exceptions import EncryptionError
        from selenium_teleport.security import decrypt_state, encrypt_state, generate_key

        encrypted = encrypt_state(sample_state, encryption_key)
        wrong_key = generate_key()

        with pytest.raises(EncryptionError):
            decrypt_state(encrypted, wrong_key)

    def test_is_encrypted_detection(self, sample_state, encryption_key):
        """Test encrypted data detection."""
        import json

        from selenium_teleport.security import encrypt_state, is_encrypted

        encrypted = encrypt_state(sample_state, encryption_key)
        plain = json.dumps(sample_state).encode("utf-8")

        assert is_encrypted(encrypted) is True
        assert is_encrypted(plain) is False


class TestTokenExpiration:
    """Tests for token expiration validation."""

    def test_valid_tokens(self, sample_state):
        """Test validation of non-expired tokens."""
        from selenium_teleport.security import validate_token_expiry

        is_valid, expired = validate_token_expiry(sample_state)
        assert is_valid is True
        assert expired == []

    def test_expired_tokens(self, expired_state):
        """Test detection of expired tokens."""
        from selenium_teleport.security import validate_token_expiry

        is_valid, expired = validate_token_expiry(expired_state)
        assert is_valid is False
        assert "expired_session" in expired

    def test_remove_expired_cookies(self, expired_state):
        """Test removal of expired cookies."""
        from selenium_teleport.security import remove_expired_cookies

        cookies = expired_state["cookies"]
        valid = remove_expired_cookies(cookies)

        assert len(valid) == 0

    def test_keep_session_cookies(self):
        """Test that session cookies (no expiry) are kept."""
        from selenium_teleport.security import remove_expired_cookies

        cookies = [
            {"name": "session_cookie", "value": "abc"},  # No expiry
            {"name": "expired", "value": "xyz", "expiry": 1},  # Expired
        ]

        valid = remove_expired_cookies(cookies)
        assert len(valid) == 1
        assert valid[0]["name"] == "session_cookie"


class TestDomainValidation:
    """Tests for domain validation."""

    def test_same_domain(self):
        """Test validation of same domain."""
        from selenium_teleport.security import validate_domain_match

        assert validate_domain_match("https://example.com", "https://example.com/path") is True

    def test_subdomain_allowed(self):
        """Test that subdomains are allowed by default."""
        from selenium_teleport.security import validate_domain_match

        assert validate_domain_match("https://mail.example.com", "https://www.example.com") is True

    def test_different_domain_rejected(self):
        """Test that different domains are rejected."""
        from selenium_teleport.security import validate_domain_match

        assert validate_domain_match("https://example.com", "https://evil.com") is False

    def test_strict_mode(self):
        """Test strict mode requires exact match."""
        from selenium_teleport.security import validate_domain_match

        assert (
            validate_domain_match(
                "https://mail.example.com", "https://www.example.com", strict=True
            )
            is False
        )

    def test_extract_root_domain(self):
        """Test root domain extraction."""
        from selenium_teleport.security import extract_root_domain

        assert extract_root_domain("https://www.example.com/path") == "example.com"
        assert extract_root_domain("https://mail.google.com:8080") == "google.com"
        assert extract_root_domain("https://example.co.uk") == "example.co.uk"


class TestInputSanitization:
    """Tests for input sanitization."""

    def test_path_traversal_detection(self):
        """Test detection of path traversal attempts."""
        from selenium_teleport.exceptions import PathTraversalError
        from selenium_teleport.security import sanitize_file_path

        with pytest.raises(PathTraversalError):
            sanitize_file_path("../../../etc/passwd")

        with pytest.raises(PathTraversalError):
            sanitize_file_path("..\\..\\windows\\system32")

        with pytest.raises(PathTraversalError):
            sanitize_file_path("%2e%2e%2f")

    def test_valid_path_sanitization(self, temp_dir):
        """Test that valid paths are sanitized correctly."""
        from selenium_teleport.security import sanitize_file_path

        # Relative path should be converted to absolute
        result = sanitize_file_path("test_file.json")
        assert os.path.isabs(result)
        assert "test_file.json" in result

    def test_ssrf_prevention(self):
        """Test SSRF prevention."""
        from selenium_teleport.exceptions import SSRFError
        from selenium_teleport.security import validate_url

        # Private IPs should be blocked
        with pytest.raises(SSRFError):
            validate_url("http://192.168.1.1/api")

        with pytest.raises(SSRFError):
            validate_url("http://127.0.0.1/internal")

        with pytest.raises(SSRFError):
            validate_url("http://localhost/admin")

    def test_valid_urls_allowed(self):
        """Test that valid public URLs are allowed."""
        from selenium_teleport.security import validate_url

        is_valid, msg = validate_url("https://example.com/path")
        assert is_valid is True

        is_valid, msg = validate_url("https://api.github.com/users")
        assert is_valid is True

    def test_allow_private_flag(self):
        """Test that allow_private flag permits private IPs."""
        from selenium_teleport.security import validate_url

        is_valid, msg = validate_url("http://192.168.1.1/api", allow_private=True)
        assert is_valid is True


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_hash_state_for_audit(self, sample_state):
        """Test state hashing for audit."""
        from selenium_teleport.security import hash_state_for_audit

        hash1 = hash_state_for_audit(sample_state)
        hash2 = hash_state_for_audit(sample_state)

        assert hash1 == hash2  # Same state = same hash
        assert len(hash1) == 16  # Truncated hash

    def test_anonymize_state(self, sample_state):
        """Test state anonymization."""
        from selenium_teleport.security import anonymize_state

        anonymized = anonymize_state(sample_state)

        # Metadata should be preserved
        assert anonymized["metadata"] == sample_state["metadata"]

        # Values should be redacted
        assert all(c["value"] == "[REDACTED]" for c in anonymized["cookies"])
        assert all(v == "[REDACTED]" for v in anonymized["localStorage"].values())
