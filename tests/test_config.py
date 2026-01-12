"""
Tests for the configuration module.
"""

import json
import os
import tempfile

import pytest


class TestTeleportConfig:
    """Tests for TeleportConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        from selenium_teleport.config import TeleportConfig

        config = TeleportConfig()

        assert config.encryption_enabled is False
        assert config.validate_expiry is True
        assert config.validate_domain is True
        assert config.default_profile_path == "selenium_profile"
        assert config.log_level == "INFO"

    def test_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        from selenium_teleport.config import TeleportConfig

        monkeypatch.setenv("TELEPORT_ENCRYPTION_KEY", "test_key_123")
        monkeypatch.setenv("TELEPORT_VALIDATE_EXPIRY", "false")
        monkeypatch.setenv("TELEPORT_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("TELEPORT_ALLOWED_DOMAINS", "example.com,test.com")

        config = TeleportConfig.from_env()

        assert config.encryption_key == "test_key_123"
        assert config.encryption_enabled is True
        assert config.validate_expiry is False
        assert config.log_level == "DEBUG"
        assert config.allowed_domains == ["example.com", "test.com"]

    def test_from_file(self, temp_dir):
        """Test loading config from JSON file."""
        from selenium_teleport.config import TeleportConfig

        config_data = {
            "encryption_enabled": True,
            "validate_domain": False,
            "log_level": "WARNING",
            "blocked_domains": ["malicious.com"],
        }

        config_path = os.path.join(temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        config = TeleportConfig.from_file(config_path)

        assert config.encryption_enabled is True
        assert config.validate_domain is False
        assert config.log_level == "WARNING"
        assert "malicious.com" in config.blocked_domains

    def test_to_dict_excludes_sensitive(self):
        """Test that to_dict excludes sensitive data."""
        from selenium_teleport.config import TeleportConfig

        config = TeleportConfig(encryption_key="secret_key")
        config_dict = config.to_dict()

        assert "encryption_key" not in config_dict
        assert "encryption_enabled" in config_dict


class TestGlobalConfig:
    """Tests for global config management."""

    def test_get_set_config(self):
        """Test getting and setting global config."""
        from selenium_teleport.config import TeleportConfig, get_config, set_config

        # Set custom config
        custom_config = TeleportConfig(log_level="ERROR")
        set_config(custom_config)

        # Get should return same config
        retrieved = get_config()
        assert retrieved.log_level == "ERROR"
